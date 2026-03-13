"""
Dashboard repository — read-only aggregation queries.
All queries are scoped to org_id and a time window.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import LLMModel
from app.models.usage_log import UsageLog


# ---------------------------------------------------------------------------
# Summary (KPI cards)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PeriodSummary:
    total_spend: Decimal
    request_count: int
    total_tokens: int


async def get_period_summary(
    db: AsyncSession,
    org_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> PeriodSummary:
    row = await db.execute(
        select(
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal("0")).label("spend"),
            func.count(UsageLog.id).label("requests"),
            func.coalesce(
                func.sum(UsageLog.tokens_input + UsageLog.tokens_output), 0
            ).label("tokens"),
        ).where(
            UsageLog.organization_id == org_id,
            UsageLog.created_at >= since,
            UsageLog.created_at < until,
        )
    )
    r = row.one()
    return PeriodSummary(
        total_spend=r.spend or Decimal("0"),
        request_count=r.requests or 0,
        total_tokens=r.tokens or 0,
    )


# ---------------------------------------------------------------------------
# Daily spend (area chart)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DailyRow:
    date: date
    spend_usd: Decimal
    request_count: int


async def get_daily_spend(
    db: AsyncSession,
    org_id: uuid.UUID,
    since: datetime,
) -> list[DailyRow]:
    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("day"),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal("0")).label("spend"),
            func.count(UsageLog.id).label("requests"),
        )
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.created_at >= since,
        )
        .group_by(func.date(UsageLog.created_at))
        .order_by(func.date(UsageLog.created_at).asc())
    )
    return [
        DailyRow(date=r.day, spend_usd=r.spend or Decimal("0"), request_count=r.requests)
        for r in result.all()
    ]


# ---------------------------------------------------------------------------
# Spend by model (horizontal bar chart)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ModelRow:
    model_name: str
    display_name: str
    spend_usd: Decimal
    request_count: int
    total_tokens: int


async def get_spend_by_model(
    db: AsyncSession,
    org_id: uuid.UUID,
    since: datetime,
) -> list[ModelRow]:
    result = await db.execute(
        select(
            LLMModel.name.label("model_name"),
            LLMModel.display_name.label("display_name"),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal("0")).label("spend"),
            func.count(UsageLog.id).label("requests"),
            func.coalesce(
                func.sum(UsageLog.tokens_input + UsageLog.tokens_output), 0
            ).label("tokens"),
        )
        .join(LLMModel, UsageLog.model_id == LLMModel.id)
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.created_at >= since,
        )
        .group_by(LLMModel.id, LLMModel.name, LLMModel.display_name)
        .order_by(func.sum(UsageLog.cost_usd).desc())
    )
    return [
        ModelRow(
            model_name=r.model_name,
            display_name=r.display_name,
            spend_usd=r.spend or Decimal("0"),
            request_count=r.requests,
            total_tokens=r.tokens,
        )
        for r in result.all()
    ]


# ---------------------------------------------------------------------------
# Recent activity (table)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ActivityRow:
    id: uuid.UUID
    model_name: str
    display_name: str
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal
    latency_ms: int
    is_streaming: bool
    created_at: datetime


async def get_activity(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[ActivityRow], int]:
    """Returns (rows, total_count)."""
    offset = (page - 1) * page_size

    # Total count
    total = await db.scalar(
        select(func.count(UsageLog.id)).where(UsageLog.organization_id == org_id)
    ) or 0

    # Page of rows
    result = await db.execute(
        select(
            UsageLog.id,
            LLMModel.name.label("model_name"),
            LLMModel.display_name.label("display_name"),
            UsageLog.tokens_input,
            UsageLog.tokens_output,
            UsageLog.cost_usd,
            UsageLog.latency_ms,
            UsageLog.is_streaming,
            UsageLog.created_at,
        )
        .join(LLMModel, UsageLog.model_id == LLMModel.id)
        .where(UsageLog.organization_id == org_id)
        .order_by(UsageLog.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )

    rows = [
        ActivityRow(
            id=r.id,
            model_name=r.model_name,
            display_name=r.display_name,
            tokens_input=r.tokens_input,
            tokens_output=r.tokens_output,
            cost_usd=r.cost_usd,
            latency_ms=r.latency_ms,
            is_streaming=r.is_streaming,
            created_at=r.created_at,
        )
        for r in result.all()
    ]

    return rows, total
