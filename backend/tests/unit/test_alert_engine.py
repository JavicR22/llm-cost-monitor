"""
Unit tests for AlertEngine — Sprint 3.1/3.2

All Redis and DB interactions are mocked so these run without
any external services.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.alerts.alert_engine import AlertEngine, SoftAlert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule(type: str, scope: str = "daily", threshold: str = "10.00", multiplier: str = "3.0"):
    rule = MagicMock()
    rule.id = uuid.uuid4()
    rule.type = type
    rule.scope = scope
    rule.threshold_value = Decimal(threshold)
    rule.anomaly_multiplier = Decimal(multiplier)
    return rule


def _make_redis(*, cb_open: bool = False, spend: str = "0", ttl: int = 100):
    redis = AsyncMock()
    redis.exists = AsyncMock(return_value=int(cb_open))
    redis.get = AsyncMock(return_value=spend if spend != "0" else None)
    redis.set = AsyncMock()
    redis.ttl = AsyncMock(return_value=ttl)
    redis.incrbyfloat = AsyncMock()
    redis.expire = AsyncMock()
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture()
def engine():
    return AlertEngine()


@pytest.fixture()
def org_id():
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# pre_request_checks — circuit breaker
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_open_blocks(engine, org_id):
    redis = _make_redis(cb_open=True)
    db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await engine.pre_request_checks(org_id, db, redis)

    assert exc_info.value.status_code == 429
    assert "Circuit breaker" in exc_info.value.detail


@pytest.mark.asyncio
async def test_circuit_breaker_closed_passes(engine, org_id):
    redis = _make_redis(cb_open=False)
    db = AsyncMock()

    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[]):
        result = await engine.pre_request_checks(org_id, db, redis)

    assert result == []


# ---------------------------------------------------------------------------
# pre_request_checks — budget hard limit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hard_budget_blocks_when_exceeded(engine, org_id):
    redis = _make_redis(cb_open=False, spend="15.00")
    db = AsyncMock()
    rule = _make_rule("budget_hard", threshold="10.00")

    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch.object(engine, "_get_current_spend", return_value=Decimal("15.00")):
            with pytest.raises(HTTPException) as exc_info:
                await engine.pre_request_checks(org_id, db, redis)

    assert exc_info.value.status_code == 429
    assert "Hard" in exc_info.value.detail


@pytest.mark.asyncio
async def test_hard_budget_passes_when_under(engine, org_id):
    redis = _make_redis(cb_open=False)
    db = AsyncMock()
    rule = _make_rule("budget_hard", threshold="10.00")

    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch.object(engine, "_get_current_spend", return_value=Decimal("5.00")):
            result = await engine.pre_request_checks(org_id, db, redis)

    assert result == []


# ---------------------------------------------------------------------------
# pre_request_checks — budget soft limit (80%)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_budget_returns_alert_at_80_pct(engine, org_id):
    redis = _make_redis(cb_open=False)
    db = AsyncMock()
    rule = _make_rule("budget_soft", threshold="10.00")

    # 8.50 / 10.00 = 85% → above the 80% threshold
    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch.object(engine, "_get_current_spend", return_value=Decimal("8.50")):
            result = await engine.pre_request_checks(org_id, db, redis)

    assert len(result) == 1
    alert = result[0]
    assert isinstance(alert, SoftAlert)
    assert alert.rule_id == rule.id
    assert alert.severity == "warning"
    assert "85%" in alert.message


@pytest.mark.asyncio
async def test_soft_budget_no_alert_below_80_pct(engine, org_id):
    redis = _make_redis(cb_open=False)
    db = AsyncMock()
    rule = _make_rule("budget_soft", threshold="10.00")

    # 7.00 / 10.00 = 70% → below 80%, no alert
    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch.object(engine, "_get_current_spend", return_value=Decimal("7.00")):
            result = await engine.pre_request_checks(org_id, db, redis)

    assert result == []


# ---------------------------------------------------------------------------
# Circuit breaker — unlock / status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unlock_circuit_breaker_returns_true(engine, org_id):
    redis = _make_redis()
    redis.delete = AsyncMock(return_value=1)
    was_open = await engine.unlock_circuit_breaker(org_id, redis)
    assert was_open is True


@pytest.mark.asyncio
async def test_unlock_circuit_breaker_already_closed(engine, org_id):
    redis = _make_redis()
    redis.delete = AsyncMock(return_value=0)
    was_open = await engine.unlock_circuit_breaker(org_id, redis)
    assert was_open is False


@pytest.mark.asyncio
async def test_is_circuit_open_true(engine, org_id):
    redis = _make_redis(cb_open=True)
    assert await engine.is_circuit_open(org_id, redis) is True


@pytest.mark.asyncio
async def test_is_circuit_open_false(engine, org_id):
    redis = _make_redis(cb_open=False)
    assert await engine.is_circuit_open(org_id, redis) is False


# ---------------------------------------------------------------------------
# _increment_spend — Redis keys updated
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_increment_spend_updates_all_keys(engine, org_id):
    redis = AsyncMock()
    redis.incrbyfloat = AsyncMock()
    redis.ttl = AsyncMock(return_value=-1)   # no TTL set yet
    redis.expire = AsyncMock()

    await engine._increment_spend(org_id, Decimal("1.2345"), redis)

    # Should have called incrbyfloat 3 times (daily, monthly, 5-min bucket)
    assert redis.incrbyfloat.call_count == 3
    # And expire on each because ttl == -1
    assert redis.expire.call_count == 3


@pytest.mark.asyncio
async def test_increment_spend_no_expire_when_ttl_set(engine, org_id):
    redis = AsyncMock()
    redis.incrbyfloat = AsyncMock()
    redis.ttl = AsyncMock(return_value=500)  # TTL already set
    redis.expire = AsyncMock()

    await engine._increment_spend(org_id, Decimal("0.50"), redis)

    redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_increment_spend_passes_string_to_incrbyfloat(engine, org_id):
    """incrbyfloat must receive a string, not a float, to preserve Decimal precision."""
    redis = AsyncMock()
    redis.incrbyfloat = AsyncMock()
    redis.ttl = AsyncMock(return_value=100)
    redis.expire = AsyncMock()

    cost = Decimal("0.000123456789")
    await engine._increment_spend(org_id, cost, redis)

    for call in redis.incrbyfloat.call_args_list:
        _, amount = call.args
        assert isinstance(amount, str), "incrbyfloat should receive str, not float"
        assert amount == str(cost)


# ---------------------------------------------------------------------------
# _evaluate_circuit_breaker — no duplicate events when already open
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_no_duplicate_event_when_already_open(engine, org_id):
    """If the CB is already open, _evaluate_circuit_breaker must return without
    inserting a new alert event."""
    rule = _make_rule("circuit_breaker", threshold="5.00")

    redis = AsyncMock()
    redis.get = AsyncMock(return_value="10.00")   # window spend > threshold
    redis.exists = AsyncMock(return_value=1)       # CB already open

    db = AsyncMock()

    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch("app.services.alerts.alert_engine.insert_alert_event") as mock_insert:
            await engine._evaluate_circuit_breaker(org_id, db, redis)
            mock_insert.assert_not_called()


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_inserts_event_when_closed(engine, org_id):
    """If the CB is closed and threshold exceeded, it opens the CB and inserts one event."""
    rule = _make_rule("circuit_breaker", threshold="5.00")

    redis = AsyncMock()
    redis.get = AsyncMock(return_value="10.00")   # window spend > threshold
    redis.exists = AsyncMock(return_value=0)       # CB currently closed
    redis.set = AsyncMock()

    db = AsyncMock()

    with patch("app.services.alerts.alert_engine.get_active_alert_rules", return_value=[rule]):
        with patch("app.services.alerts.alert_engine.insert_alert_event") as mock_insert:
            await engine._evaluate_circuit_breaker(org_id, db, redis)
            redis.set.assert_called_once()
            mock_insert.assert_called_once()
