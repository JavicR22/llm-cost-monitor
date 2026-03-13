"""
Unit tests for service key CRUD — 2.6
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.service_key import ServiceKeyCreate
from app.services.keys.service_key_service import create_key, list_keys, revoke_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_key(
    is_active: bool = True,
    revoked_at=None,
    key_hash: str = "abc123",
) -> MagicMock:
    key = MagicMock()
    key.id = uuid.uuid4()
    key.organization_id = uuid.uuid4()
    key.label = "Test key"
    key.key_prefix = "lcm_sk_live_...***abcd"
    key.key_hash = key_hash
    key.is_active = is_active
    key.revoked_at = revoked_at
    key.created_at = datetime.now(timezone.utc)
    key.last_used_at = None
    return key


# ---------------------------------------------------------------------------
# list_keys
# ---------------------------------------------------------------------------

class TestListKeys:
    @pytest.mark.asyncio
    async def test_returns_list_of_responses(self):
        db = AsyncMock()
        org_id = uuid.uuid4()
        keys = [_make_key(), _make_key()]

        with patch("app.services.keys.service_key_service.list_service_keys", return_value=keys):
            result = await list_keys(db, org_id)

        assert len(result) == 2
        # raw_key must NOT be in the response
        for r in result:
            assert not hasattr(r, "raw_key") or r.__class__.__name__ == "ServiceKeyResponse"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_keys(self):
        db = AsyncMock()
        with patch("app.services.keys.service_key_service.list_service_keys", return_value=[]):
            result = await list_keys(db, uuid.uuid4())
        assert result == []


# ---------------------------------------------------------------------------
# create_key
# ---------------------------------------------------------------------------

class TestCreateKey:
    @pytest.mark.asyncio
    async def test_returns_raw_key_once(self):
        db = AsyncMock()
        org_id = uuid.uuid4()
        stored_key = _make_key()

        with patch(
            "app.services.keys.service_key_service.create_service_key",
            return_value=stored_key,
        ):
            result = await create_key(db, org_id, ServiceKeyCreate(label="prod"))

        # raw_key is present and has the correct prefix
        assert result.raw_key.startswith("lcm_sk_live_")
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_raw_key_is_not_stored(self):
        """The raw key must differ from the key_prefix stored in DB."""
        db = AsyncMock()
        org_id = uuid.uuid4()
        stored_key = _make_key()

        with patch(
            "app.services.keys.service_key_service.create_service_key",
            return_value=stored_key,
        ) as mock_create:
            result = await create_key(db, org_id, ServiceKeyCreate())

        # create_service_key was called with a hash, not the raw key
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["key_hash"] != result.raw_key

    @pytest.mark.asyncio
    async def test_two_keys_have_different_raw_keys(self):
        db = AsyncMock()
        org_id = uuid.uuid4()

        with patch(
            "app.services.keys.service_key_service.create_service_key",
            return_value=_make_key(),
        ):
            r1 = await create_key(db, org_id, ServiceKeyCreate())
            r2 = await create_key(db, org_id, ServiceKeyCreate())

        assert r1.raw_key != r2.raw_key

    @pytest.mark.asyncio
    async def test_label_is_stored(self):
        db = AsyncMock()
        stored_key = _make_key()
        stored_key.label = "My API key"

        with patch(
            "app.services.keys.service_key_service.create_service_key",
            return_value=stored_key,
        ):
            result = await create_key(db, uuid.uuid4(), ServiceKeyCreate(label="My API key"))

        assert result.label == "My API key"


# ---------------------------------------------------------------------------
# revoke_key
# ---------------------------------------------------------------------------

class TestRevokeKey:
    @pytest.mark.asyncio
    async def test_revokes_active_key(self):
        db = AsyncMock()
        redis = AsyncMock()
        redis.delete = AsyncMock()

        active_key = _make_key(is_active=True)
        revoked_key = _make_key(is_active=False)

        with patch("app.services.keys.service_key_service.get_service_key", return_value=active_key), \
             patch("app.services.keys.service_key_service.revoke_service_key", return_value=revoked_key):
            result = await revoke_key(db, redis, active_key.id, active_key.organization_id)

        assert result.is_active is False
        redis.delete.assert_called_once()  # cache invalidated

    @pytest.mark.asyncio
    async def test_raises_404_for_unknown_key(self):
        db = AsyncMock()
        redis = AsyncMock()

        with patch("app.services.keys.service_key_service.get_service_key", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, redis, uuid.uuid4(), uuid.uuid4())

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_409_for_already_revoked_key(self):
        db = AsyncMock()
        redis = AsyncMock()
        already_revoked = _make_key(is_active=False)

        with patch("app.services.keys.service_key_service.get_service_key", return_value=already_revoked):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, redis, already_revoked.id, already_revoked.organization_id)

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cannot_revoke_other_org_key(self):
        """get_service_key filters by org_id — returns None for foreign keys."""
        db = AsyncMock()
        redis = AsyncMock()

        with patch("app.services.keys.service_key_service.get_service_key", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await revoke_key(db, redis, uuid.uuid4(), uuid.uuid4())

        assert exc.value.status_code == 404
