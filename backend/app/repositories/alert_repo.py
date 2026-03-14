"""
Alert repository — queries for alert rules, events, and anomaly data.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertEvent, AlertRule
from app.models.usage_log import UsageLog


async def get_active_alert_rules(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> list[AlertRule]:
    """Return all active alert rules for an organization."""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.organization_id == org_id,
            AlertRule.is_active == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def list_alert_rules(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> list[AlertRule]:
    """Return all alert rules (active and inactive) for an organization."""
    result = await db.execute(
        select(AlertRule)
        .where(AlertRule.organization_id == org_id)
        .order_by(AlertRule.created_at.desc())
    )
    return list(result.scalars().all())


async def get_alert_rule(
    db: AsyncSession,
    rule_id: uuid.UUID,
    org_id: uuid.UUID,
) -> AlertRule:
    """Fetch a single alert rule; raises 404 if not found or wrong org."""
    result = await db.scalar(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.organization_id == org_id,
        )
    )
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert rule not found")
    return result


async def create_alert_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    type: str,
    scope: str,
    threshold_value: Optional[Decimal],
    anomaly_multiplier: Optional[Decimal],
    is_active: bool,
) -> AlertRule:
    """Insert a new alert rule and return it."""
    rule = AlertRule(
        organization_id=org_id,
        type=type,
        scope=scope,
        threshold_value=threshold_value,
        anomaly_multiplier=anomaly_multiplier,
        is_active=is_active,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def update_alert_rule(
    db: AsyncSession,
    rule: AlertRule,
    *,
    threshold_value: Optional[Decimal] = None,
    anomaly_multiplier: Optional[Decimal] = None,
    is_active: Optional[bool] = None,
) -> AlertRule:
    """Patch mutable fields of an alert rule."""
    if threshold_value is not None:
        rule.threshold_value = threshold_value
    if anomaly_multiplier is not None:
        rule.anomaly_multiplier = anomaly_multiplier
    if is_active is not None:
        rule.is_active = is_active
    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_alert_rule(
    db: AsyncSession,
    rule: AlertRule,
) -> None:
    """Hard delete an alert rule."""
    await db.delete(rule)
    await db.commit()


async def list_alert_events(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[AlertEvent]:
    """Return paginated alert events for an organization, newest first."""
    result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.organization_id == org_id)
        .order_by(AlertEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_spend_since(
    db: AsyncSession,
    org_id: uuid.UUID,
    since: datetime,
) -> Decimal:
    """Sum of cost_usd from usage_logs since the given UTC datetime."""
    result = await db.scalar(
        select(
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal("0"))
        ).where(
            UsageLog.organization_id == org_id,
            UsageLog.created_at >= since,
        )
    )
    return result or Decimal("0")


async def get_hourly_avg_7d(
    db: AsyncSession,
    org_id: uuid.UUID,
    before: datetime,
) -> Decimal:
    """
    7-day hourly average spend ending at `before`.
    Returns total spend over 7 days divided by 168 hours.
    Zero if there is no historical data.
    """
    since_7d = before - timedelta(days=7)
    total = await get_spend_since(db, org_id, since_7d)
    if total == 0:
        return Decimal("0")
    return (total / Decimal("168")).quantize(Decimal("0.00000001"))


async def insert_alert_event(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    alert_rule_id: Optional[uuid.UUID],
    severity: str,
    type: str,
    message: str,
    triggered_value: Decimal,
    threshold_value: Decimal,
) -> AlertEvent:
    """Insert an AlertEvent row and commit."""
    event = AlertEvent(
        organization_id=org_id,
        alert_rule_id=alert_rule_id,
        severity=severity,
        type=type,
        message=message,
        triggered_value=triggered_value,
        threshold_value=threshold_value,
        notification_sent=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
