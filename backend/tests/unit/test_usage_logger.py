"""
Unit tests for usage_logger — 2.4
All DB and Redis calls are mocked.
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.services.metering.usage_logger import (
    log_usage_sync_result,
    log_usage_stream_result,
)
from app.services.metering.cost_calculator import ModelPricing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pricing() -> ModelPricing:
    return ModelPricing(
        model_id=str(uuid.uuid4()),
        model_name="gpt-4o",
        cost_per_1m_input=Decimal("5.00"),
        cost_per_1m_output=Decimal("15.00"),
    )


def _mock_redis():
    redis = AsyncMock()
    redis.aclose = AsyncMock()
    return redis


# ---------------------------------------------------------------------------
# log_usage_sync_result
# ---------------------------------------------------------------------------

class TestLogUsageSyncResult:
    @pytest.mark.asyncio
    async def test_writes_log_from_response(self):
        org_id = uuid.uuid4()
        key_id = uuid.uuid4()
        response = {"usage": {"prompt_tokens": 50, "completion_tokens": 20}}

        pricing = _pricing()

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", return_value=pricing), \
             patch("app.services.metering.usage_logger.create_usage_log", new_callable=AsyncMock) as mock_create:

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await log_usage_sync_result(
                org_id=org_id,
                service_key_id=key_id,
                model_name="gpt-4o",
                openai_response=response,
                latency_ms=342,
                request_ip="1.2.3.4",
                user_agent="pytest/1.0",
            )

        mock_create.assert_called_once()
        call_data = mock_create.call_args[0][1]  # UsageLogCreate
        assert call_data.tokens_input == 50
        assert call_data.tokens_output == 20
        assert call_data.latency_ms == 342
        assert call_data.is_streaming is False
        assert call_data.request_ip == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_skips_log_for_unknown_model(self):
        org_id = uuid.uuid4()

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", return_value=None), \
             patch("app.services.metering.usage_logger.create_usage_log", new_callable=AsyncMock) as mock_create:

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await log_usage_sync_result(
                org_id=org_id,
                service_key_id=None,
                model_name="some-unknown-model",
                openai_response={"usage": {"prompt_tokens": 10, "completion_tokens": 5}},
                latency_ms=100,
                request_ip=None,
                user_agent=None,
            )

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_db_failure(self):
        """Background tasks must never crash silently — they catch and log."""
        org_id = uuid.uuid4()

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", side_effect=Exception("DB down")):

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            # Should not raise
            await log_usage_sync_result(
                org_id=org_id,
                service_key_id=None,
                model_name="gpt-4o",
                openai_response={},
                latency_ms=100,
                request_ip=None,
                user_agent=None,
            )


# ---------------------------------------------------------------------------
# log_usage_stream_result
# ---------------------------------------------------------------------------

class TestLogUsageStreamResult:
    @pytest.mark.asyncio
    async def test_parses_chunks_and_writes_log(self):
        org_id = uuid.uuid4()
        key_id = uuid.uuid4()
        pricing = _pricing()

        # SSE chunks with include_usage final chunk
        chunks = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            'data: {"choices":[],"usage":{"prompt_tokens":30,"completion_tokens":10}}\n',
            "data: [DONE]\n",
        ]

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", return_value=pricing), \
             patch("app.services.metering.usage_logger.create_usage_log", new_callable=AsyncMock) as mock_create:

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await log_usage_stream_result(
                org_id=org_id,
                service_key_id=key_id,
                model_name="gpt-4o",
                captured_chunks=chunks,
                latency_ms=800,
                request_ip="10.0.0.1",
                user_agent="curl/8.0",
            )

        mock_create.assert_called_once()
        call_data = mock_create.call_args[0][1]
        assert call_data.tokens_input == 30
        assert call_data.tokens_output == 10
        assert call_data.is_streaming is True
        assert call_data.latency_ms == 800

    @pytest.mark.asyncio
    async def test_falls_back_to_tiktoken_when_no_usage_chunk(self):
        org_id = uuid.uuid4()
        pricing = _pricing()

        # No usage chunk — tiktoken counts content
        chunks = [
            'data: {"choices":[{"delta":{"content":"Hello world"}}]}\n',
            "data: [DONE]\n",
        ]

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", return_value=pricing), \
             patch("app.services.metering.usage_logger.create_usage_log", new_callable=AsyncMock) as mock_create:

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await log_usage_stream_result(
                org_id=org_id,
                service_key_id=None,
                model_name="gpt-4o",
                captured_chunks=chunks,
                latency_ms=500,
                request_ip=None,
                user_agent=None,
            )

        call_data = mock_create.call_args[0][1]
        # Input tokens unknown without include_usage
        assert call_data.tokens_input == 0
        # Output tokens estimated by tiktoken
        assert call_data.tokens_output > 0

    @pytest.mark.asyncio
    async def test_cost_is_calculated_correctly(self):
        org_id = uuid.uuid4()
        # gpt-4o: $5/1M input, $15/1M output
        # 100 input + 50 output → $0.0005 + $0.00075 = $0.00125
        pricing = ModelPricing(
            model_id=str(uuid.uuid4()),
            model_name="gpt-4o",
            cost_per_1m_input=Decimal("5.00"),
            cost_per_1m_output=Decimal("15.00"),
        )

        chunks = [
            'data: {"choices":[],"usage":{"prompt_tokens":100,"completion_tokens":50}}\n',
            "data: [DONE]\n",
        ]

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", return_value=pricing), \
             patch("app.services.metering.usage_logger.create_usage_log", new_callable=AsyncMock) as mock_create:

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await log_usage_stream_result(
                org_id=org_id,
                service_key_id=None,
                model_name="gpt-4o",
                captured_chunks=chunks,
                latency_ms=100,
                request_ip=None,
                user_agent=None,
            )

        call_data = mock_create.call_args[0][1]
        assert call_data.cost_usd == Decimal("0.00125000")

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self):
        org_id = uuid.uuid4()

        with patch("app.services.metering.usage_logger.aioredis.from_url", return_value=_mock_redis()), \
             patch("app.services.metering.usage_logger.AsyncSessionFactory") as mock_factory, \
             patch("app.services.metering.usage_logger.get_model_pricing", side_effect=RuntimeError("Redis down")):

            mock_db = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            # Must not propagate — background tasks are fire-and-forget
            await log_usage_stream_result(
                org_id=org_id,
                service_key_id=None,
                model_name="gpt-4o",
                captured_chunks=[],
                latency_ms=0,
                request_ip=None,
                user_agent=None,
            )
