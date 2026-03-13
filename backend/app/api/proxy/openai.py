"""
OpenAI-compatible proxy endpoint.

Clients point their base_url here and use their lcm_sk_live_... key.
Request/response formats are preserved exactly — no schema changes.
"""
import time
from collections.abc import AsyncIterator
from typing import Annotated, Any

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.dependencies import DB, get_redis
from app.services.metering.usage_logger import log_usage_stream_result, log_usage_sync_result
from app.services.proxy.proxy_service import ProxyService, get_proxy_service

log = structlog.get_logger()

router = APIRouter(tags=["proxy"])

Redis = Annotated[aioredis.Redis, Depends(get_redis)]
Proxy = Annotated[ProxyService, Depends(get_proxy_service)]


def _extract_bearer(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Bearer token")
    return auth.removeprefix("Bearer ").strip()


async def _capture_stream(
    source: AsyncIterator[bytes],
    captured: list[str],
) -> AsyncIterator[bytes]:
    """
    Wrap a streaming generator to collect raw SSE chunks while yielding them.
    After the generator exhausts, `captured` holds all chunks for usage parsing.
    """
    async for chunk in source:
        captured.append(chunk.decode(errors="replace"))
        yield chunk


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DB,
    redis: Redis,
    proxy: Proxy,
) -> Any:
    """
    OpenAI-compatible chat completions proxy.

    Auth:      Authorization: Bearer lcm_sk_live_<key>
    Streaming: pass "stream": true — SSE is passed through transparently.
    Logging:   usage_logs written asynchronously after response is sent.
    """
    raw_key = _extract_bearer(request)

    # 1. Authenticate service key
    service_key = await proxy.authenticate(raw_key, db, redis)
    org_id = service_key.organization_id

    # 2. Rate limit
    await proxy.check_rate_limit(str(org_id), redis)

    # 3. Parse body
    body: dict = await request.json()
    model_name: str = body.get("model", "gpt-4o")
    stream: bool = body.get("stream", False)

    # 4. Decrypt provider key (lives in memory only during this request)
    api_key = await proxy.get_decrypted_provider_key(db, org_id, "openai")

    # Shared logging context
    request_ip: str | None = request.client.host if request.client else None
    user_agent: str | None = request.headers.get("User-Agent")

    log.info("proxy_request", org_id=str(org_id), model=model_name, stream=stream)

    start_ms = time.monotonic()

    # ------------------------------------------------------------------
    # 5a. Streaming
    # ------------------------------------------------------------------
    if stream:
        # Inject include_usage so the last SSE chunk contains token counts
        body.setdefault("stream_options", {})
        body["stream_options"]["include_usage"] = True

        captured: list[str] = []
        source = proxy.forward_stream("openai", body, api_key)

        background_tasks.add_task(
            log_usage_stream_result,
            org_id=org_id,
            service_key_id=service_key.id,
            model_name=model_name,
            captured_chunks=captured,
            latency_ms=int((time.monotonic() - start_ms) * 1000),
            request_ip=request_ip,
            user_agent=user_agent,
        )

        return StreamingResponse(
            _capture_stream(source, captured),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ------------------------------------------------------------------
    # 5b. Non-streaming
    # ------------------------------------------------------------------
    response = await proxy.forward("openai", body, api_key)
    latency_ms = int((time.monotonic() - start_ms) * 1000)

    background_tasks.add_task(
        log_usage_sync_result,
        org_id=org_id,
        service_key_id=service_key.id,
        model_name=model_name,
        openai_response=response,
        latency_ms=latency_ms,
        request_ip=request_ip,
        user_agent=user_agent,
    )

    log.info(
        "proxy_response",
        org_id=str(org_id),
        model=model_name,
        usage=response.get("usage"),
        latency_ms=latency_ms,
    )

    return response
