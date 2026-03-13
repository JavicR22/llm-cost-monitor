"""
Unit tests for cost_calculator — 2.3
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.metering.cost_calculator import (
    ModelPricing,
    TokenUsage,
    calculate_cost,
    get_model_pricing,
    meter_request,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _pricing(input_per_m: str = "5.00", output_per_m: str = "15.00") -> ModelPricing:
    return ModelPricing(
        model_id=str(uuid.uuid4()),
        model_name="gpt-4o",
        cost_per_1m_input=Decimal(input_per_m),
        cost_per_1m_output=Decimal(output_per_m),
    )


# ---------------------------------------------------------------------------
# calculate_cost
# ---------------------------------------------------------------------------

class TestCalculateCost:
    def test_zero_tokens_is_zero_cost(self):
        cost = calculate_cost(0, 0, _pricing())
        assert cost == Decimal("0.00000000")

    def test_known_price_gpt4o(self):
        # gpt-4o: $5/1M input, $15/1M output
        # 1000 input + 500 output
        # = (1000/1M)*5 + (500/1M)*15
        # = 0.005 + 0.0075 = 0.0125
        cost = calculate_cost(1000, 500, _pricing("5.00", "15.00"))
        assert cost == Decimal("0.01250000")

    def test_uses_decimal_not_float(self):
        cost = calculate_cost(100, 100, _pricing())
        assert isinstance(cost, Decimal)

    def test_output_tokens_more_expensive(self):
        # Same token count, output costs more
        input_only = calculate_cost(1000, 0, _pricing("5.00", "15.00"))
        output_only = calculate_cost(0, 1000, _pricing("5.00", "15.00"))
        assert output_only > input_only

    def test_large_request_precision(self):
        # 1M input + 1M output at gpt-4o pricing = $5 + $15 = $20
        cost = calculate_cost(1_000_000, 1_000_000, _pricing("5.00", "15.00"))
        assert cost == Decimal("20.00000000")

    def test_quantized_to_8_decimal_places(self):
        cost = calculate_cost(1, 1, _pricing("5.00", "15.00"))
        # str representation should have 8 decimal places
        assert len(str(cost).split(".")[1]) == 8

    def test_cheap_model_economy(self):
        # gpt-4o-mini: $0.15/1M input, $0.60/1M output
        pricing = _pricing("0.15", "0.60")
        cost = calculate_cost(1000, 500, pricing)
        expected = (Decimal("1000") / 1_000_000 * Decimal("0.15")) + \
                   (Decimal("500")  / 1_000_000 * Decimal("0.60"))
        assert cost == expected.quantize(Decimal("0.00000001"))


# ---------------------------------------------------------------------------
# get_model_pricing
# ---------------------------------------------------------------------------

class TestGetModelPricing:
    @pytest.mark.asyncio
    async def test_returns_cached_pricing(self):
        db = AsyncMock()
        redis = AsyncMock()
        redis.hgetall = AsyncMock(return_value={
            "model_id": str(uuid.uuid4()),
            "input": "5.00",
            "output": "15.00",
        })

        result = await get_model_pricing("gpt-4o", db, redis)

        assert result is not None
        assert result.model_name == "gpt-4o"
        assert result.cost_per_1m_input == Decimal("5.00")
        db.execute.assert_not_called()  # DB not touched on cache hit

    @pytest.mark.asyncio
    async def test_falls_back_to_db_on_cache_miss(self):
        db = AsyncMock()
        redis = AsyncMock()
        redis.hgetall = AsyncMock(return_value={})  # cache miss
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()

        model = MagicMock()
        model.id = uuid.uuid4()
        model.cost_per_1m_input_tokens = Decimal("5.00")
        model.cost_per_1m_output_tokens = Decimal("15.00")

        with patch("app.services.metering.cost_calculator.get_model_by_name", return_value=model):
            result = await get_model_pricing("gpt-4o", db, redis)

        assert result is not None
        redis.hset.assert_called_once()  # populated cache
        redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_model(self):
        db = AsyncMock()
        redis = AsyncMock()
        redis.hgetall = AsyncMock(return_value={})

        with patch("app.services.metering.cost_calculator.get_model_by_name", return_value=None):
            result = await get_model_pricing("nonexistent-model", db, redis)

        assert result is None


# ---------------------------------------------------------------------------
# meter_request (integration of get_model_pricing + calculate_cost)
# ---------------------------------------------------------------------------

class TestMeterRequest:
    @pytest.mark.asyncio
    async def test_returns_token_usage_with_cost(self):
        db = AsyncMock()
        redis = AsyncMock()

        p = _pricing("5.00", "15.00")
        with patch("app.services.metering.cost_calculator.get_model_pricing", return_value=p):
            result = await meter_request("gpt-4o", 1000, 500, db, redis)

        assert result is not None
        assert isinstance(result, TokenUsage)
        assert result.input_tokens == 1000
        assert result.output_tokens == 500
        assert result.cost_usd == Decimal("0.01250000")
        assert result.total_tokens == 1500

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_model(self):
        db = AsyncMock()
        redis = AsyncMock()

        with patch("app.services.metering.cost_calculator.get_model_pricing", return_value=None):
            result = await meter_request("unknown-model", 100, 50, db, redis)

        assert result is None

    @pytest.mark.asyncio
    async def test_zero_cost_for_zero_tokens(self):
        db = AsyncMock()
        redis = AsyncMock()

        p = _pricing("5.00", "15.00")
        with patch("app.services.metering.cost_calculator.get_model_pricing", return_value=p):
            result = await meter_request("gpt-4o", 0, 0, db, redis)

        assert result is not None
        assert result.cost_usd == Decimal("0.00000000")
