"""
Dashboard service — assembles KPI data from the repository layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repo import (
    get_activity,
    get_daily_spend,
    get_period_summary,
    get_spend_by_model,
)
from app.schemas.dashboard import (
    ActivityResponse,
    ActivityRow,
    DailySpend,
    SpendByModel,
    SummaryResponse,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _change_pct(current: Decimal | int, previous: Decimal | int) -> float | None:
    """Percentage change from previous to current. None if no previous data."""
    prev = float(previous)
    if prev == 0:
        return None
    return round((float(current) - prev) / prev * 100, 1)


async def get_summary(
    db: AsyncSession,
    org_id: uuid.UUID,
    days: int,
) -> SummaryResponse:
    now = _now()
    period_start = now - timedelta(days=days)
    prev_start = period_start - timedelta(days=days)

    # Current period + previous period in parallel would need two queries
    current = await get_period_summary(db, org_id, period_start, now)
    previous = await get_period_summary(db, org_id, prev_start, period_start)

    avg_cost = (
        current.total_spend / current.request_count
        if current.request_count > 0
        else Decimal("0")
    )

    return SummaryResponse(
        total_spend_usd=current.total_spend,
        request_count=current.request_count,
        avg_cost_per_request=avg_cost,
        total_tokens=current.total_tokens,
        spend_change_pct=_change_pct(current.total_spend, previous.total_spend),
        request_change_pct=_change_pct(current.request_count, previous.request_count),
    )


async def get_spend_over_time(
    db: AsyncSession,
    org_id: uuid.UUID,
    days: int,
) -> list[DailySpend]:
    since = _now() - timedelta(days=days)
    rows = await get_daily_spend(db, org_id, since)
    return [
        DailySpend(date=r.date, spend_usd=r.spend_usd, request_count=r.request_count)
        for r in rows
    ]


async def get_spend_by_model(
    db: AsyncSession,
    org_id: uuid.UUID,
    days: int,
) -> list[SpendByModel]:
    since = _now() - timedelta(days=days)
    rows = await get_spend_by_model_repo(db, org_id, since)

    total_spend = sum(r.spend_usd for r in rows) or Decimal("1")  # avoid div/0

    return [
        SpendByModel(
            model_name=r.model_name,
            display_name=r.display_name,
            spend_usd=r.spend_usd,
            request_count=r.request_count,
            total_tokens=r.total_tokens,
            pct_of_total=round(float(r.spend_usd / total_spend * 100), 1),
        )
        for r in rows
    ]


async def get_activity_page(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int,
    page_size: int,
) -> ActivityResponse:
    rows, total = await get_activity(db, org_id, page, page_size)
    return ActivityResponse(
        items=[
            ActivityRow(
                id=str(r.id),
                model_name=r.model_name,
                display_name=r.display_name,
                tokens_input=r.tokens_input,
                tokens_output=r.tokens_output,
                cost_usd=r.cost_usd,
                latency_ms=r.latency_ms,
                is_streaming=r.is_streaming,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# Re-export to avoid circular import confusion
from app.repositories.dashboard_repo import get_spend_by_model as get_spend_by_model_repo  # noqa: E402
