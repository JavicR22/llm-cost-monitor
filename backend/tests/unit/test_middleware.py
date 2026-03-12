from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import SecurityHeadersMiddleware


# ------------------------------------------------------------------
# Security Headers
# ------------------------------------------------------------------

def _make_app_with_security_headers() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    def test_route():
        return {"ok": True}

    return app


def test_security_headers_present() -> None:
    client = TestClient(_make_app_with_security_headers())
    res = client.get("/test")
    assert res.status_code == 200
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Strict-Transport-Security"].startswith("max-age=")
    assert "Content-Security-Policy" in res.headers
    assert "Referrer-Policy" in res.headers


# ------------------------------------------------------------------
# Rate limiter — standalone function (no HTTP layer needed)
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_allows_under_limit() -> None:
    from app.middleware.rate_limit import check_rate_limit

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock()
    redis_mock.get = AsyncMock(return_value="free")

    allowed, remaining = await check_rate_limit(redis_mock, "org-1", plan="free")
    assert allowed is True
    assert remaining == 59  # 60 limit - 1 used


@pytest.mark.asyncio
async def test_rate_limit_blocks_at_limit() -> None:
    from app.middleware.rate_limit import check_rate_limit

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=61)  # over the free limit of 60
    redis_mock.expire = AsyncMock()

    allowed, remaining = await check_rate_limit(redis_mock, "org-1", plan="free")
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_rate_limit_pro_plan_higher_limit() -> None:
    from app.middleware.rate_limit import check_rate_limit

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=500)
    redis_mock.expire = AsyncMock()

    allowed, remaining = await check_rate_limit(redis_mock, "org-1", plan="pro")
    assert allowed is True
    assert remaining == 500  # 1000 - 500


@pytest.mark.asyncio
async def test_rate_limit_exact_boundary() -> None:
    from app.middleware.rate_limit import check_rate_limit

    redis_mock = AsyncMock()
    redis_mock.incr = AsyncMock(return_value=60)  # exactly at limit
    redis_mock.expire = AsyncMock()

    allowed, remaining = await check_rate_limit(redis_mock, "org-1", plan="free")
    assert allowed is True
    assert remaining == 0
