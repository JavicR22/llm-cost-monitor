"""
Unit tests for dashboard service — 2.8
Repository calls are mocked; we test the business logic layer.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.repositories.dashboard_repo import DailyRow, ModelRow, ActivityRow as RepoActivityRow, PeriodSummary
from app.services.dashboard.dashboard_service import (
    _change_pct,
    get_summary,
    get_spend_over_time,
    get_spend_by_model,
    get_activity_page,
)


# ---------------------------------------------------------------------------
# _change_pct (pure function)
# ---------------------------------------------------------------------------

class TestChangePct:
    def test_positive_change(self):
        assert _change_pct(Decimal("110"), Decimal("100")) == 10.0

    def test_negative_change(self):
        assert _change_pct(Decimal("90"), Decimal("100")) == -10.0

    def test_no_previous_data_returns_none(self):
        assert _change_pct(Decimal("50"), Decimal("0")) is None

    def test_zero_change(self):
        assert _change_pct(Decimal("100"), Decimal("100")) == 0.0

    def test_works_with_ints(self):
        assert _change_pct(200, 100) == 100.0

    def test_rounds_to_one_decimal(self):
        result = _change_pct(Decimal("103"), Decimal("97"))
        assert result == round(result, 1)


# ---------------------------------------------------------------------------
# get_summary
# ---------------------------------------------------------------------------

class TestGetSummary:
    @pytest.mark.asyncio
    async def test_returns_kpi_data(self):
        db = AsyncMock()
        org_id = uuid.uuid4()

        current = PeriodSummary(
            total_spend=Decimal("100.00"),
            request_count=500,
            total_tokens=1_000_000,
        )
        previous = PeriodSummary(
            total_spend=Decimal("80.00"),
            request_count=400,
            total_tokens=800_000,
        )

        with patch("app.services.dashboard.dashboard_service.get_period_summary", side_effect=[current, previous]):
            result = await get_summary(db, org_id, days=30)

        assert result.total_spend_usd == Decimal("100.00")
        assert result.request_count == 500
        assert result.total_tokens == 1_000_000
        assert result.spend_change_pct == 25.0   # (100-80)/80 * 100
        assert result.request_change_pct == 25.0

    @pytest.mark.asyncio
    async def test_avg_cost_calculated_correctly(self):
        db = AsyncMock()
        current = PeriodSummary(Decimal("10.00"), 1000, 500_000)
        previous = PeriodSummary(Decimal("0"), 0, 0)

        with patch("app.services.dashboard.dashboard_service.get_period_summary", side_effect=[current, previous]):
            result = await get_summary(db, uuid.uuid4(), days=30)

        # $10 / 1000 requests = $0.01 per request
        assert result.avg_cost_per_request == Decimal("0.01")

    @pytest.mark.asyncio
    async def test_avg_cost_zero_when_no_requests(self):
        db = AsyncMock()
        empty = PeriodSummary(Decimal("0"), 0, 0)

        with patch("app.services.dashboard.dashboard_service.get_period_summary", side_effect=[empty, empty]):
            result = await get_summary(db, uuid.uuid4(), days=30)

        assert result.avg_cost_per_request == Decimal("0")

    @pytest.mark.asyncio
    async def test_no_change_pct_when_no_previous_data(self):
        db = AsyncMock()
        current = PeriodSummary(Decimal("50"), 100, 10_000)
        previous = PeriodSummary(Decimal("0"), 0, 0)

        with patch("app.services.dashboard.dashboard_service.get_period_summary", side_effect=[current, previous]):
            result = await get_summary(db, uuid.uuid4(), days=7)

        assert result.spend_change_pct is None
        assert result.request_change_pct is None


# ---------------------------------------------------------------------------
# get_spend_over_time
# ---------------------------------------------------------------------------

class TestGetSpendOverTime:
    @pytest.mark.asyncio
    async def test_returns_daily_series(self):
        db = AsyncMock()
        rows = [
            DailyRow(date=date(2026, 3, 1), spend_usd=Decimal("10.00"), request_count=100),
            DailyRow(date=date(2026, 3, 2), spend_usd=Decimal("15.00"), request_count=150),
        ]

        with patch("app.services.dashboard.dashboard_service.get_daily_spend", return_value=rows):
            result = await get_spend_over_time(db, uuid.uuid4(), days=30)

        assert len(result) == 2
        assert result[0].spend_usd == Decimal("10.00")
        assert result[1].request_count == 150

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_data(self):
        db = AsyncMock()
        with patch("app.services.dashboard.dashboard_service.get_daily_spend", return_value=[]):
            result = await get_spend_over_time(db, uuid.uuid4(), days=7)
        assert result == []


# ---------------------------------------------------------------------------
# get_spend_by_model
# ---------------------------------------------------------------------------

class TestGetSpendByModel:
    @pytest.mark.asyncio
    async def test_calculates_pct_of_total(self):
        db = AsyncMock()
        rows = [
            ModelRow("gpt-4o", "GPT-4o", Decimal("75.00"), 500, 1_000_000),
            ModelRow("gpt-4o-mini", "GPT-4o mini", Decimal("25.00"), 300, 500_000),
        ]

        with patch("app.services.dashboard.dashboard_service.get_spend_by_model_repo", return_value=rows):
            result = await get_spend_by_model(db, uuid.uuid4(), days=30)

        assert len(result) == 2
        assert result[0].pct_of_total == 75.0
        assert result[1].pct_of_total == 25.0

    @pytest.mark.asyncio
    async def test_sorted_by_spend_descending(self):
        db = AsyncMock()
        rows = [
            ModelRow("gpt-4o", "GPT-4o", Decimal("80.00"), 100, 100_000),
            ModelRow("gpt-4o-mini", "GPT-4o mini", Decimal("20.00"), 200, 200_000),
        ]

        with patch("app.services.dashboard.dashboard_service.get_spend_by_model_repo", return_value=rows):
            result = await get_spend_by_model(db, uuid.uuid4(), days=30)

        # Repo already sorts — service preserves order
        assert result[0].model_name == "gpt-4o"
        assert result[1].model_name == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_handles_empty(self):
        db = AsyncMock()
        with patch("app.services.dashboard.dashboard_service.get_spend_by_model_repo", return_value=[]):
            result = await get_spend_by_model(db, uuid.uuid4(), days=30)
        assert result == []


# ---------------------------------------------------------------------------
# get_activity_page
# ---------------------------------------------------------------------------

class TestGetActivityPage:
    @pytest.mark.asyncio
    async def test_returns_paginated_result(self):
        db = AsyncMock()
        now = datetime.now(timezone.utc)
        rows = [
            RepoActivityRow(
                id=uuid.uuid4(),
                model_name="gpt-4o",
                display_name="GPT-4o",
                tokens_input=100,
                tokens_output=50,
                cost_usd=Decimal("0.001"),
                latency_ms=320,
                is_streaming=False,
                created_at=now,
            )
        ]

        with patch("app.services.dashboard.dashboard_service.get_activity", return_value=(rows, 94)):
            result = await get_activity_page(db, uuid.uuid4(), page=1, page_size=10)

        assert result.total == 94
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 1
        assert result.items[0].model_name == "gpt-4o"
        assert result.items[0].cost_usd == Decimal("0.001")

    @pytest.mark.asyncio
    async def test_empty_page(self):
        db = AsyncMock()
        with patch("app.services.dashboard.dashboard_service.get_activity", return_value=([], 0)):
            result = await get_activity_page(db, uuid.uuid4(), page=1, page_size=10)

        assert result.total == 0
        assert result.items == []
