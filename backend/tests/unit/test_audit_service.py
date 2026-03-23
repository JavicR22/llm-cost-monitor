"""
Unit tests for audit_service.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.security import audit_service


@pytest.fixture()
def org_id():
    return uuid.uuid4()


@pytest.fixture()
def user_id():
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_log_inserts_entry(org_id, user_id):
    """Happy path: log() opens a session and calls insert_audit_log."""
    with patch("app.services.security.audit_service.AsyncSessionFactory") as mock_factory:
        mock_db = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.security.audit_service.insert_audit_log") as mock_insert:
            await audit_service.log(
                org_id=org_id,
                user_id=user_id,
                action="key_created",
                entity_type="service_api_key",
                entity_id=uuid.uuid4(),
                details={"label": "prod"},
                ip="127.0.0.1",
                ua="pytest/1.0",
            )

    mock_insert.assert_awaited_once()
    call_kwargs = mock_insert.call_args.kwargs
    assert call_kwargs["organization_id"] == org_id
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["action"] == "key_created"
    assert call_kwargs["ip_address"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_log_swallows_exceptions(org_id, user_id):
    """log() must never raise even if the DB call fails."""
    with patch("app.services.security.audit_service.AsyncSessionFactory") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(side_effect=RuntimeError("DB down"))
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        # Should not raise
        await audit_service.log(
            org_id=org_id,
            user_id=user_id,
            action="login",
        )


@pytest.mark.asyncio
async def test_log_accepts_none_user_id(org_id):
    """user_id can be None (e.g. failed login for unknown user)."""
    with patch("app.services.security.audit_service.AsyncSessionFactory") as mock_factory:
        mock_db = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.security.audit_service.insert_audit_log") as mock_insert:
            await audit_service.log(
                org_id=org_id,
                user_id=None,
                action="login_failed",
                details={"email": "bad@example.com"},
            )

    call_kwargs = mock_insert.call_args.kwargs
    assert call_kwargs["user_id"] is None
    assert call_kwargs["action"] == "login_failed"


@pytest.mark.asyncio
async def test_log_minimal_fields(org_id, user_id):
    """log() works with only required fields."""
    with patch("app.services.security.audit_service.AsyncSessionFactory") as mock_factory:
        mock_db = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.security.audit_service.insert_audit_log") as mock_insert:
            await audit_service.log(
                org_id=org_id,
                user_id=user_id,
                action="circuit_breaker_released",
            )

    call_kwargs = mock_insert.call_args.kwargs
    assert call_kwargs["entity_type"] is None
    assert call_kwargs["details"] is None
    assert call_kwargs["ip_address"] is None
