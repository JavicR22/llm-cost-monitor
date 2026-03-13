"""
Unit tests for the proxy service — auth, rate limiting, forwarding.
All external calls (DB, Redis, httpx) are mocked.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.proxy.proxy_service import ProxyService, _build_headers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def proxy():
    return ProxyService()


def _make_service_key(org_id: uuid.UUID | None = None) -> MagicMock:
    key = MagicMock()
    key.organization_id = org_id or uuid.uuid4()
    key.is_active = True
    key.revoked_at = None
    return key


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_rejects_wrong_prefix(self, proxy):
        db = AsyncMock()
        redis = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await proxy.authenticate("sk-openai-key", db, redis)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_unknown_key(self, proxy):
        db = AsyncMock()
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)  # cache miss

        with patch("app.services.proxy.proxy_service.get_service_key_by_hash", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await proxy.authenticate("lcm_sk_live_notreal", db, redis)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_valid_key_db_path(self, proxy):
        db = AsyncMock()
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)  # cache miss
        redis.setex = AsyncMock()

        service_key = _make_service_key()

        with patch("app.services.proxy.proxy_service.get_service_key_by_hash", return_value=service_key):
            result = await proxy.authenticate("lcm_sk_live_validkey123456789", db, redis)

        assert result is service_key
        redis.setex.assert_called_once()  # populated cache

    @pytest.mark.asyncio
    async def test_accepts_valid_key_cache_path(self, proxy):
        db = AsyncMock()
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="1")  # cache hit

        service_key = _make_service_key()

        with patch("app.services.proxy.proxy_service.get_service_key_by_hash", return_value=service_key):
            result = await proxy.authenticate("lcm_sk_live_validkey123456789", db, redis)

        assert result is service_key

    @pytest.mark.asyncio
    async def test_revoked_key_invalidates_cache(self, proxy):
        db = AsyncMock()
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="1")  # cache hit
        redis.delete = AsyncMock()

        with patch("app.services.proxy.proxy_service.get_service_key_by_hash", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await proxy.authenticate("lcm_sk_live_revoked", db, redis)

        assert exc.value.status_code == 401
        redis.delete.assert_called_once()  # cache invalidated


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimit:
    @pytest.mark.asyncio
    async def test_allows_within_limit(self, proxy):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="free")

        with patch("app.services.proxy.proxy_service.check_rate_limit", return_value=(True, 55)):
            await proxy.check_rate_limit("org-123", redis)  # should not raise

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, proxy):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="free")

        with patch("app.services.proxy.proxy_service.check_rate_limit", return_value=(False, 0)):
            with pytest.raises(HTTPException) as exc:
                await proxy.check_rate_limit("org-123", redis)

        assert exc.value.status_code == 429
        assert "Retry-After" in exc.value.headers


# ---------------------------------------------------------------------------
# Provider key decryption
# ---------------------------------------------------------------------------

class TestGetDecryptedProviderKey:
    @pytest.mark.asyncio
    async def test_raises_when_no_key_configured(self, proxy):
        db = AsyncMock()
        with patch("app.services.proxy.proxy_service.get_active_provider_key", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await proxy.get_decrypted_provider_key(db, uuid.uuid4(), "openai")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_decrypts_and_returns_key(self, proxy):
        db = AsyncMock()
        provider_key = MagicMock()
        provider_key.key_ciphertext = "some_ciphertext"

        vault = MagicMock()
        vault.decrypt = MagicMock(return_value="sk-real-openai-key")

        with patch("app.services.proxy.proxy_service.get_active_provider_key", return_value=provider_key):
            with patch("app.services.proxy.proxy_service.get_key_vault", return_value=vault):
                result = await proxy.get_decrypted_provider_key(db, uuid.uuid4(), "openai")

        assert result == "sk-real-openai-key"


# ---------------------------------------------------------------------------
# Header building
# ---------------------------------------------------------------------------

class TestBuildHeaders:
    def test_openai_uses_bearer(self):
        headers = _build_headers("openai", "sk-test")
        assert headers["Authorization"] == "Bearer sk-test"
        assert headers["Content-Type"] == "application/json"

    def test_anthropic_uses_x_api_key(self):
        headers = _build_headers("anthropic", "ant-test")
        assert headers["x-api-key"] == "ant-test"
        assert "anthropic-version" in headers


# ---------------------------------------------------------------------------
# Forward (non-streaming)
# ---------------------------------------------------------------------------

class TestForward:
    @pytest.mark.asyncio
    async def test_returns_provider_json(self, proxy):
        fake_response = {"id": "chatcmpl-abc", "choices": [{"message": {"content": "Hello"}}]}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value=fake_response)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.proxy.proxy_service.httpx.AsyncClient", return_value=mock_client):
            result = await proxy.forward("openai", {"model": "gpt-4o", "messages": []}, "sk-test")

        assert result["id"] == "chatcmpl-abc"

    @pytest.mark.asyncio
    async def test_raises_502_on_provider_error(self, proxy):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json = MagicMock(return_value={"error": {"message": "quota exceeded"}})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.proxy.proxy_service.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(HTTPException) as exc:
                await proxy.forward("openai", {"model": "gpt-4o"}, "sk-bad")

        assert exc.value.status_code == 502
        assert "quota exceeded" in exc.value.detail
