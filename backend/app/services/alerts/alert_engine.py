"""
Alert Engine — Sprint 3.1 + 3.2

Implements 4 protection layers (evaluated per request):

  1. Circuit Breaker  — pre-request: blocks if opened (Redis flag, manual unlock)
  2. Budget Hard Limit — pre-request: blocks when accumulated spend >= limit
  3. Budget Soft Limit — pre-request: non-blocking, records alert event in background
  4. Anomaly Detection — post-request (background): last-hour vs 7-day avg

Redis key schema:
  cb:open:{org_id}              → "1" if circuit breaker is open (no TTL)
  cb:5min:{org_id}:{bucket}    → spend in 5-min bucket (TTL 10 min)
  budget:daily:{org_id}:{date} → accumulated daily spend (TTL 2 days)
  budget:monthly:{org_id}:{ym} → accumulated monthly spend (TTL 35 days)

Latency budget: pre_request_checks must add <5ms to the request path.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timezone
from decimal import Decimal
from typing import Optional

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app.repositories.alert_repo import (
    get_active_alert_rules,
    get_hourly_avg_7d,
    get_spend_since,
    insert_alert_event,
)
from app.services.notifications.notification_service import notify_alert_event

log = structlog.get_logger()
UTC = timezone.utc

# Redis key templates
_CB_OPEN_KEY = "cb:open:{org_id}"
_CB_5MIN_KEY = "cb:5min:{org_id}:{bucket}"
_BUDGET_DAILY_KEY = "budget:daily:{org_id}:{date}"
_BUDGET_MONTHLY_KEY = "budget:monthly:{org_id}:{month}"


@dataclass(slots=True)
class SoftAlert:
    """
    A non-blocking alert. Returned by pre_request_checks so the
    route handler can fire a background task to persist it.
    """

    rule_id: uuid.UUID
    type: str          # "soft_limit"
    severity: str      # "warning"
    message: str
    triggered_value: Decimal
    threshold_value: Decimal


class AlertEngine:
    """Stateless — one singleton shared via DI."""

    # ------------------------------------------------------------------
    # Pre-request (runs in the request path — keep it fast)
    # ------------------------------------------------------------------

    async def pre_request_checks(
        self,
        org_id: uuid.UUID,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> list[SoftAlert]:
        """
        Run before forwarding to the LLM provider.

        Raises HTTPException (429) for:
          - Open circuit breaker
          - Hard budget limit exceeded

        Returns a list of SoftAlerts (may be empty) to be persisted
        asynchronously — the caller adds them as a background task.
        """
        soft_alerts: list[SoftAlert] = []

        # 1. Circuit breaker — single Redis GET (~0.5 ms)
        cb_key = _CB_OPEN_KEY.format(org_id=org_id)
        if await redis.exists(cb_key):
            log.warning("circuit_breaker_blocking", org_id=str(org_id))
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Circuit breaker is open: anomalous spending detected. "
                    "All requests are blocked. Contact support to unlock."
                ),
                headers={"Retry-After": "3600"},
            )

        # 2. Load budget rules — skip DB hit if no rules exist
        rules = await get_active_alert_rules(db, org_id)
        budget_rules = [r for r in rules if r.type in ("budget_soft", "budget_hard")]
        if not budget_rules:
            return soft_alerts

        # 3. Get current period spend (Redis, seeded from DB if key is missing)
        now = datetime.now(UTC)
        today = now.date()

        daily_spend = await self._get_current_spend("daily", org_id, today, db, redis)
        monthly_spend = await self._get_current_spend("monthly", org_id, today, db, redis)

        for rule in budget_rules:
            if rule.scope == "daily":
                current = daily_spend
            elif rule.scope == "monthly":
                current = monthly_spend
            else:
                continue

            threshold = Decimal(str(rule.threshold_value))

            # Hard limit → block immediately
            if rule.type == "budget_hard" and current >= threshold:
                log.warning(
                    "budget_hard_limit_exceeded",
                    org_id=str(org_id),
                    scope=rule.scope,
                    current_usd=str(current),
                    threshold_usd=str(threshold),
                )
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Hard {rule.scope} budget limit of ${threshold:.2f} exceeded "
                        f"(current: ${current:.4f}). Requests blocked until limit resets."
                    ),
                    headers={"Retry-After": "3600"},
                )

            # Soft limit → alert at 80 % of threshold
            soft_threshold = threshold * Decimal("0.80")
            if rule.type == "budget_soft" and current >= soft_threshold:
                pct = (current / threshold * 100).quantize(Decimal("1"))
                soft_alerts.append(
                    SoftAlert(
                        rule_id=rule.id,
                        type="soft_limit",
                        severity="warning",
                        message=(
                            f"{pct}% of {rule.scope} budget used "
                            f"(${current:.4f} / ${threshold:.2f})"
                        ),
                        triggered_value=current,
                        threshold_value=threshold,
                    )
                )

        return soft_alerts

    # ------------------------------------------------------------------
    # Post-request (always run as a background task)
    # ------------------------------------------------------------------

    async def post_request_tasks(
        self,
        org_id: uuid.UUID,
        cost_usd: Decimal,
    ) -> None:
        """
        Background: increment Redis spend counters, then evaluate circuit
        breaker and anomaly detection.

        Opens its own DB + Redis sessions — the request's session is closed.
        """
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            async with AsyncSessionFactory() as db:
                await self._increment_spend(org_id, cost_usd, redis)
                await self._evaluate_circuit_breaker(org_id, db, redis)
                await self._evaluate_anomaly(org_id, db, redis)
        except Exception:
            log.exception("alert_post_request_failed", org_id=str(org_id))
        finally:
            await redis.aclose()

    async def save_soft_alerts(
        self,
        org_id: uuid.UUID,
        soft_alerts: list[SoftAlert],
    ) -> None:
        """
        Background: persist a list of SoftAlerts to DB as AlertEvent rows.
        Opens its own DB session.
        """
        if not soft_alerts:
            return
        try:
            async with AsyncSessionFactory() as db:
                for alert in soft_alerts:
                    event = await insert_alert_event(
                        db,
                        org_id=org_id,
                        alert_rule_id=alert.rule_id,
                        severity=alert.severity,
                        type=alert.type,
                        message=alert.message,
                        triggered_value=alert.triggered_value,
                        threshold_value=alert.threshold_value,
                    )
                    await notify_alert_event(org_id, event)
        except Exception:
            log.exception("save_soft_alerts_failed", org_id=str(org_id))

    async def unlock_circuit_breaker(
        self,
        org_id: uuid.UUID,
        redis: aioredis.Redis,
    ) -> bool:
        """
        Manual unlock — called from settings/admin endpoint.
        Returns True if the breaker was open (and is now cleared).
        """
        cb_key = _CB_OPEN_KEY.format(org_id=org_id)
        deleted = await redis.delete(cb_key)
        log.info(
            "circuit_breaker_unlocked",
            org_id=str(org_id),
            was_open=bool(deleted),
        )
        return bool(deleted)

    async def is_circuit_open(
        self,
        org_id: uuid.UUID,
        redis: aioredis.Redis,
    ) -> bool:
        cb_key = _CB_OPEN_KEY.format(org_id=org_id)
        return bool(await redis.exists(cb_key))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_current_spend(
        self,
        scope: str,
        org_id: uuid.UUID,
        today: date,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> Decimal:
        """
        Get current period spend from Redis.
        Seeds from DB if the key is missing (server restart, first request of period).
        """
        if scope == "daily":
            redis_key = _BUDGET_DAILY_KEY.format(
                org_id=org_id, date=today.isoformat()
            )
            ttl = 172_800  # 2 days
            since = datetime.combine(today, dtime.min, tzinfo=UTC)
        else:  # monthly
            month_str = today.strftime("%Y-%m")
            redis_key = _BUDGET_MONTHLY_KEY.format(org_id=org_id, month=month_str)
            ttl = 3_024_000  # 35 days
            since = datetime(today.year, today.month, 1, tzinfo=UTC)

        val = await redis.get(redis_key)
        if val is not None:
            return Decimal(val)

        # Seed from DB and cache
        spend = await get_spend_since(db, org_id, since)
        await redis.set(redis_key, str(spend), ex=ttl)
        return spend

    async def _increment_spend(
        self,
        org_id: uuid.UUID,
        cost_usd: Decimal,
        redis: aioredis.Redis,
    ) -> None:
        """Atomically increment all spend counters after a successful request."""
        today = datetime.now(UTC).date()
        amount = str(cost_usd)  # str preserves Decimal precision; incrbyfloat parses it
        bucket = int(time.time()) // 300  # 5-minute bucket

        keys_ttls = [
            (
                _BUDGET_DAILY_KEY.format(org_id=org_id, date=today.isoformat()),
                172_800,
            ),
            (
                _BUDGET_MONTHLY_KEY.format(
                    org_id=org_id, month=today.strftime("%Y-%m")
                ),
                3_024_000,
            ),
            (
                _CB_5MIN_KEY.format(org_id=org_id, bucket=bucket),
                600,
            ),
        ]

        for key, ttl in keys_ttls:
            await redis.incrbyfloat(key, amount)
            # Set TTL only if the key has none (newly created by incrbyfloat)
            if await redis.ttl(key) < 0:
                await redis.expire(key, ttl)

    async def _evaluate_circuit_breaker(
        self,
        org_id: uuid.UUID,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> None:
        """
        Background: if spend in the current 5-minute window exceeds any
        circuit_breaker threshold, open the circuit and save an alert event.
        """
        rules = await get_active_alert_rules(db, org_id)
        cb_rules = [r for r in rules if r.type == "circuit_breaker"]
        if not cb_rules:
            return

        bucket = int(time.time()) // 300
        cb_5min_key = _CB_5MIN_KEY.format(org_id=org_id, bucket=bucket)
        val = await redis.get(cb_5min_key)
        if not val:
            return

        window_spend = Decimal(val)
        cb_key = _CB_OPEN_KEY.format(org_id=org_id)

        # Skip if already open — avoids inserting duplicate alert events
        if await redis.exists(cb_key):
            return

        for rule in cb_rules:
            threshold = Decimal(str(rule.threshold_value))
            if window_spend >= threshold:
                # Open circuit — no TTL, manual unlock required
                await redis.set(cb_key, "1")

                log.critical(
                    "circuit_breaker_tripped",
                    org_id=str(org_id),
                    window_spend_usd=str(window_spend),
                    threshold_usd=str(threshold),
                )

                event = await insert_alert_event(
                    db,
                    org_id=org_id,
                    alert_rule_id=rule.id,
                    severity="critical",
                    type="circuit_breaker",
                    message=(
                        f"Circuit breaker tripped: ${window_spend:.4f} spent in 5 min "
                        f"(threshold: ${threshold:.2f}). All requests are now blocked."
                    ),
                    triggered_value=window_spend,
                    threshold_value=threshold,
                )
                await notify_alert_event(org_id, event)
                break  # one trip per evaluation cycle

    async def _evaluate_anomaly(
        self,
        org_id: uuid.UUID,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> None:
        """
        Background: compare last-hour spend against 3× 7-day hourly average.
        Creates a warning alert event if anomalous. Does not block requests.
        """
        rules = await get_active_alert_rules(db, org_id)
        anomaly_rules = [r for r in rules if r.type == "anomaly"]
        if not anomaly_rules:
            return

        # Sum the last 12 5-minute buckets (~1 hour of data)
        now_ts = time.time()
        current_bucket = int(now_ts) // 300
        last_hour_spend = Decimal("0")
        for i in range(12):
            key = _CB_5MIN_KEY.format(org_id=org_id, bucket=current_bucket - i)
            val = await redis.get(key)
            if val:
                last_hour_spend += Decimal(val)

        if last_hour_spend == 0:
            return

        before = datetime.now(UTC)
        avg_hourly = await get_hourly_avg_7d(db, org_id, before)
        if avg_hourly == 0:
            return  # No historical data — cannot evaluate anomaly

        for rule in anomaly_rules:
            multiplier = Decimal(str(rule.anomaly_multiplier or "3.0"))
            threshold = avg_hourly * multiplier
            if last_hour_spend > threshold:
                log.warning(
                    "anomaly_detected",
                    org_id=str(org_id),
                    last_hour_usd=str(last_hour_spend),
                    avg_hourly_usd=str(avg_hourly),
                    multiplier=str(multiplier),
                )
                event = await insert_alert_event(
                    db,
                    org_id=org_id,
                    alert_rule_id=rule.id,
                    severity="warning",
                    type="anomaly",
                    message=(
                        f"Anomaly: ${last_hour_spend:.4f} spent in last hour "
                        f"({multiplier}× the ${avg_hourly:.4f} 7-day hourly avg)"
                    ),
                    triggered_value=last_hour_spend,
                    threshold_value=threshold,
                )
                await notify_alert_event(org_id, event)
                break  # one alert per evaluation cycle


def get_alert_engine() -> AlertEngine:
    """DI factory — returns the module-level singleton."""
    return _alert_engine


_alert_engine = AlertEngine()
