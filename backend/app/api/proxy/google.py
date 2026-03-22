"""
Google Gemini proxy endpoint — OpenAI-compatible format.

Google exposes an OpenAI-compatible API at:
  https://generativelanguage.googleapis.com/v1beta/openai/chat/completions

Clients use their lcm_sk_live_... service key and pass Gemini model names
(e.g. gemini-2.0-flash, gemini-1.5-pro) in the "model" field.
"""
import time
from collections.abc import AsyncIterator
from typing import Annotated, Any

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.dependencies import DB, get_redis
from app.services.alerts.alert_engine import AlertEngine, get_alert_engine
from app.services.metering.usage_logger import log_usage_stream_result, log_usage_sync_result
from app.services.proxy.proxy_service import ProxyService, get_proxy_service

log = structlog.get_logger()

router = APIRouter(tags=["proxy-google"])

Redis = Annotated[aioredis.Redis, Depends(get_redis)]
Proxy = Annotated[ProxyService, Depends(get_proxy_service)]
Alerts = Annotated[AlertEngine, Depends(get_alert_engine)]


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
    async for chunk in source:
        captured.append(chunk.decode(errors="replace"))
        yield chunk


@router.post("/v1/google/chat/completions")
async def google_chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DB,
    redis: Redis,
    proxy: Proxy,
    alert_engine: Alerts,
) -> Any:
    """
    Google Gemini chat completions proxy (OpenAI-compatible format).

    Auth:   Authorization: Bearer lcm_sk_live_<key>
    Models: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
    """
    raw_key = _extract_bearer(request)

    # 1. Authenticate service key
    service_key = await proxy.authenticate(raw_key, db, redis)
    org_id = service_key.organization_id

    # 2. Rate limit
    await proxy.check_rate_limit(str(org_id), redis)

    # 3. Budget + circuit breaker checks
    soft_alerts = await alert_engine.pre_request_checks(org_id, db, redis)
    if soft_alerts:
        background_tasks.add_task(alert_engine.save_soft_alerts, org_id, soft_alerts)

    # 4. Parse body
    body: dict = await request.json()
    model_name: str = body.get("model", "gemini-2.0-flash")
    stream: bool = body.get("stream", False)

    # 5. Decrypt Google provider key
    api_key = await proxy.get_decrypted_provider_key(db, org_id, "google")

    request_ip: str | None = request.client.host if request.client else None
    user_agent: str | None = request.headers.get("User-Agent")

    log.info("proxy_request", provider="google", org_id=str(org_id), model=model_name, stream=stream)

    start_ms = time.monotonic()

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    # FinOps attribution — inherited from the authenticated service key
    finops = {
        "project_id": service_key.project_id,
        "team_id": service_key.team_id,
        "user_id": service_key.owner_user_id,
    }

    if stream:
        body.setdefault("stream_options", {})
        body["stream_options"]["include_usage"] = True

        captured: list[str] = []
        source = proxy.forward_stream("google", body, api_key)

        background_tasks.add_task(
            log_usage_stream_result,
            org_id=org_id,
            service_key_id=service_key.id,
            model_name=model_name,
            captured_chunks=captured,
            latency_ms=int((time.monotonic() - start_ms) * 1000),
            request_ip=request_ip,
            user_agent=user_agent,
            **finops,
        )

        return StreamingResponse(
            _capture_stream(source, captured),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------
    response = await proxy.forward("google", body, api_key)
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
        **finops,
    )

    log.info(
        "proxy_response",
        provider="google",
        org_id=str(org_id),
        model=model_name,
        usage=response.get("usage"),
        latency_ms=latency_ms,
    )

    return response
