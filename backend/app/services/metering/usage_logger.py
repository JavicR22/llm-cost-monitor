"""
Async usage logger — 2.4

Background tasks that write to usage_logs after the response is sent.
Never blocks the proxy response path.

Two entry points:
  - log_usage_sync_result()  → non-streaming (token counts already known)
  - log_usage_stream_result() → streaming (parses SSE chunks for token counts)
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

import redis.asyncio as aioredis
import structlog

from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app.repositories.usage_log_repo import UsageLogCreate, create_usage_log
from app.services.metering.cost_calculator import get_model_pricing, calculate_cost
from app.services.metering.token_counter import (
    extract_usage_from_response,
    extract_usage_from_streaming_chunks,
)

log = structlog.get_logger()


async def log_usage_sync_result(
    *,
    org_id: uuid.UUID,
    service_key_id: Optional[uuid.UUID],
    model_name: str,
    openai_response: dict,
    latency_ms: int,
    request_ip: Optional[str],
    user_agent: Optional[str],
) -> None:
    """
    Background task for non-streaming requests.
    Extracts token counts from the OpenAI response JSON and writes to DB.
    """
    input_tokens, output_tokens = extract_usage_from_response(openai_response)

    await _write_log(
        org_id=org_id,
        service_key_id=service_key_id,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        is_streaming=False,
        request_ip=request_ip,
        user_agent=user_agent,
    )


async def log_usage_stream_result(
    *,
    org_id: uuid.UUID,
    service_key_id: Optional[uuid.UUID],
    model_name: str,
    captured_chunks: list[str],
    latency_ms: int,
    request_ip: Optional[str],
    user_agent: Optional[str],
) -> None:
    """
    Background task for streaming requests.
    Parses the accumulated SSE chunks (captured by the stream wrapper) for token usage.
    """
    input_tokens, output_tokens = extract_usage_from_streaming_chunks(
        captured_chunks, model_name
    )

    await _write_log(
        org_id=org_id,
        service_key_id=service_key_id,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        is_streaming=True,
        request_ip=request_ip,
        user_agent=user_agent,
    )


async def _write_log(
    *,
    org_id: uuid.UUID,
    service_key_id: Optional[uuid.UUID],
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    is_streaming: bool,
    request_ip: Optional[str],
    user_agent: Optional[str],
) -> None:
    """
    Resolve model pricing, compute cost, and INSERT a usage_log row.
    Opens its own DB and Redis sessions — the request session is already closed.
    """
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        async with AsyncSessionFactory() as db:
            pricing = await get_model_pricing(model_name, db, redis)

            if not pricing:
                log.error(
                    "usage_log_skipped_unknown_model — add this model to the 'models' table",
                    model=model_name,
                    org_id=str(org_id),
                )
                return

            cost = calculate_cost(input_tokens, output_tokens, pricing)
            model_id = uuid.UUID(pricing.model_id)

            await create_usage_log(
                db,
                UsageLogCreate(
                    organization_id=org_id,
                    model_id=model_id,
                    service_api_key_id=service_key_id,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    is_streaming=is_streaming,
                    request_ip=request_ip,
                    user_agent=user_agent,
                ),
            )

            # Alert engine — runs in the same background task, after the log is written
            from app.services.alerts.alert_engine import get_alert_engine
            await get_alert_engine().post_request_tasks(org_id, cost)

            log.info(
                "usage_logged",
                org_id=str(org_id),
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=str(cost),
                latency_ms=latency_ms,
            )

    except Exception:
        log.exception("usage_log_failed", org_id=str(org_id), model=model_name)
    finally:
        await redis.aclose()
