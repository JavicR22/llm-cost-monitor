"""
Unit tests for provider key CRUD — 2.7
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.provider_key import ProviderKeyCreate
from app.services.keys.provider_key_service import create_key, list_keys, revoke_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider(name: str = "openai") -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.name = name
    p.is_active = True
    return p


def _make_key(is_active: bool = True, provider: str = "openai") -> MagicMock:
    key = MagicMock()
    key.id = uuid.uuid4()
    key.organization_id = uuid.uuid4()
    key.provider = provider
    key.key_prefix = "sk-...***abcd"
    key.key_ciphertext = "gAAAAAB..."
    key.label = None
    key.is_active = is_active
    key.revoked_at = None
    key.created_at = datetime.now(timezone.utc)
    key.last_validated_at = None
    return key


# ---------------------------------------------------------------------------
# list_keys
# ---------------------------------------------------------------------------

class TestListKeys:
    @pytest.mark.asyncio
    async def test_returns_responses_without_ciphertext(self):
        db = AsyncMock()
        keys = [_make_key(), _make_key(provider="anthropic")]

        with patch("app.services.keys.provider_key_service.list_provider_keys", return_value=keys):
            result = await list_keys(db, uuid.uuid4())

        assert len(result) == 2
        # Ciphertext must NEVER be in the response
        for r in result:
            assert not hasattr(r, "key_ciphertext")

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        db = AsyncMock()
        with patch("app.services.keys.provider_key_service.list_provider_keys", return_value=[]):
            result = await list_keys(db, uuid.uuid4())
        assert result == []


# ---------------------------------------------------------------------------
# create_key
# ---------------------------------------------------------------------------

class TestCreateKey:
    @pytest.mark.asyncio
    async def test_encrypts_raw_key(self):
        db = AsyncMock()
        provider = _make_provider("openai")
        stored_key = _make_key()

        with patch("app.services.keys.provider_key_service.get_provider_by_name", return_value=provider), \
             patch("app.services.keys.provider_key_service.create_provider_key", return_value=stored_key) as mock_create:
            await create_key(db, uuid.uuid4(), ProviderKeyCreate(provider="openai", raw_key="sk-test-key-123456"))

        # ciphertext passed to repo must differ from the raw key
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["key_ciphertext"] != "sk-test-key-123456"
        assert call_kwargs["key_ciphertext"].startswith("gAAAA")  # Fernet prefix

    @pytest.mark.asyncio
    async def test_response_has_no_ciphertext(self):
        db = AsyncMock()
        provider = _make_provider("openai")
        stored_key = _make_key()

        with patch("app.services.keys.provider_key_service.get_provider_by_name", return_value=provider), \
             patch("app.services.keys.provider_key_service.create_provider_key", return_value=stored_key):
            result = await create_key(db, uuid.uuid4(), ProviderKeyCreate(provider="openai", raw_key="sk-test-key-123456"))

        assert not hasattr(result, "raw_key")
        assert not hasattr(result, "key_ciphertext")

    @pytest.mark.asyncio
    async def test_raises_400_for_unsupported_provider(self):
        db = AsyncMock()
        with patch("app.services.keys.provider_key_service.get_provider_by_name", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await create_key(db, uuid.uuid4(), ProviderKeyCreate(provider="openai", raw_key="sk-test-key-123456"))
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_prefix_extracted_correctly(self):
        db = AsyncMock()
        provider = _make_provider("openai")
        stored_key = _make_key()

        with patch("app.services.keys.provider_key_service.get_provider_by_name", return_value=provider), \
             patch("app.services.keys.provider_key_service.create_provider_key", return_value=stored_key) as mock_create:
            await create_key(db, uuid.uuid4(), ProviderKeyCreate(provider="openai", raw_key="sk-proj-ABCDEFGHIJ"))

        call_kwargs = mock_create.call_args.kwargs
        prefix = call_kwargs["key_prefix"]
        # Should show start and end, not the full key
        assert "***" in prefix
        assert "sk-proj" in prefix

    @pytest.mark.asyncio
    async def test_different_providers_stored_correctly(self):
        db = AsyncMock()

        for provider_name in ("openai", "anthropic", "google", "mistral"):
            provider = _make_provider(provider_name)
            stored_key = _make_key(provider=provider_name)

            with patch("app.services.keys.provider_key_service.get_provider_by_name", return_value=provider), \
                 patch("app.services.keys.provider_key_service.create_provider_key", return_value=stored_key) as mock_create:
                await create_key(db, uuid.uuid4(), ProviderKeyCreate(provider=provider_name, raw_key="test-key-123456789"))

            assert mock_create.call_args.kwargs["provider"] == provider_name


# ---------------------------------------------------------------------------
# revoke_key
# ---------------------------------------------------------------------------

class TestRevokeKey:
    @pytest.mark.asyncio
    async def test_revokes_active_key(self):
        db = AsyncMock()
        active = _make_key(is_active=True)
        revoked = _make_key(is_active=False)

        with patch("app.services.keys.provider_key_service.get_provider_key", return_value=active), \
             patch("app.services.keys.provider_key_service.revoke_provider_key", return_value=revoked):
            result = await revoke_key(db, active.id, active.organization_id)

        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_raises_404_for_unknown_key(self):
        db = AsyncMock()
        with patch("app.services.keys.provider_key_service.get_provider_key", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_409_for_already_revoked(self):
        db = AsyncMock()
        already_revoked = _make_key(is_active=False)

        with patch("app.services.keys.provider_key_service.get_provider_key", return_value=already_revoked):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, already_revoked.id, already_revoked.organization_id)
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cannot_revoke_other_org_key(self):
        db = AsyncMock()
        with patch("app.services.keys.provider_key_service.get_provider_key", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_ciphertext_not_exposed_in_revoke_response(self):
        db = AsyncMock()
        active = _make_key(is_active=True)
        revoked = _make_key(is_active=False)

        with patch("app.services.keys.provider_key_service.get_provider_key", return_value=active), \
             patch("app.services.keys.provider_key_service.revoke_provider_key", return_value=revoked):
            result = await revoke_key(db, active.id, active.organization_id)

        assert not hasattr(result, "key_ciphertext")
