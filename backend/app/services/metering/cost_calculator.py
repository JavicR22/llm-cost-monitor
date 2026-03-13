"""
Cost calculation — 2.3

Converts token counts into USD cost using per-model pricing from the DB.
Model pricing is cached in Redis to avoid a DB hit on every proxied request.

Formula:
    cost = (input_tokens  / 1_000_000) * cost_per_1m_input
         + (output_tokens / 1_000_000) * cost_per_1m_output
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

import redis.asyncio as aioredis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.model_repo import get_model_by_name

log = structlog.get_logger()

# Pricing cache TTL — 1 hour (prices rarely change)
_PRICING_CACHE_TTL = 3600

# Precision: 8 decimal places → $0.00000001 minimum (sub-cent accuracy)
_QUANTIZE = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Immutable result of a metered request."""

    model_name: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Pricing snapshot — read from DB, cached in Redis."""

    model_id: str          # UUID as string
    model_name: str
    cost_per_1m_input: Decimal
    cost_per_1m_output: Decimal


async def get_model_pricing(
    model_name: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> Optional[ModelPricing]:
    """
    Return pricing for a model. Checks Redis first, falls back to DB.
    Returns None if the model is not in our catalog (unknown model).
    """
    cache_key = f"pricing:{model_name}"

    # Fast path — Redis
    cached = await redis.hgetall(cache_key)
    if cached:
        return ModelPricing(
            model_id=cached["model_id"],
            model_name=model_name,
            cost_per_1m_input=Decimal(cached["input"]),
            cost_per_1m_output=Decimal(cached["output"]),
        )

    # Slow path — DB
    model = await get_model_by_name(db, model_name)
    if not model:
        log.warning("cost_calculator_unknown_model", model=model_name)
        return None

    pricing = ModelPricing(
        model_id=str(model.id),
        model_name=model_name,
        cost_per_1m_input=model.cost_per_1m_input_tokens,
        cost_per_1m_output=model.cost_per_1m_output_tokens,
    )

    # Populate Redis cache
    await redis.hset(
        cache_key,
        mapping={
            "model_id": pricing.model_id,
            "input": str(pricing.cost_per_1m_input),
            "output": str(pricing.cost_per_1m_output),
        },
    )
    await redis.expire(cache_key, _PRICING_CACHE_TTL)

    return pricing


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    pricing: ModelPricing,
) -> Decimal:
    """
    Compute USD cost for a request.

    Uses Decimal arithmetic throughout — never float — to avoid
    accumulation errors when summing millions of requests.
    """
    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * pricing.cost_per_1m_input
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * pricing.cost_per_1m_output
    return (input_cost + output_cost).quantize(_QUANTIZE, rounding=ROUND_HALF_UP)


async def meter_request(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> Optional[TokenUsage]:
    """
    High-level entry point: resolve pricing and compute cost in one call.
    Returns None if the model is not in the catalog (cost will be recorded as $0).
    """
    pricing = await get_model_pricing(model_name, db, redis)
    if not pricing:
        return None

    cost = calculate_cost(input_tokens, output_tokens, pricing)
    log.debug(
        "metered",
        model=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=str(cost),
    )
    return TokenUsage(
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
    )
