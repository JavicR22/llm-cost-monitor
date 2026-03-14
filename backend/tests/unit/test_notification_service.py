"""
Unit tests for the notification service and email sender.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notifications.email_sender import build_alert_email, send_email
from app.services.notifications.notification_service import _dispatch


# ---------------------------------------------------------------------------
# email_sender
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_email_no_op_when_no_api_key():
    with patch("app.services.notifications.email_sender.settings") as mock_settings:
        mock_settings.RESEND_API_KEY = ""
        result = await send_email(to="a@b.com", subject="Test", html="<p>Hi</p>")
    assert result is False


@pytest.mark.asyncio
async def test_send_email_returns_true_on_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.notifications.email_sender.settings") as mock_settings:
        mock_settings.RESEND_API_KEY = "re_test_key"
        mock_settings.NOTIFICATIONS_FROM_EMAIL = "alerts@test.com"
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_email(to="user@example.com", subject="Alert", html="<p>!</p>")

    assert result is True
    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["to"] == ["user@example.com"]
    assert call_kwargs["json"]["from"] == "alerts@test.com"


@pytest.mark.asyncio
async def test_send_email_returns_false_on_http_error():
    import httpx

    with patch("app.services.notifications.email_sender.settings") as mock_settings:
        mock_settings.RESEND_API_KEY = "re_test_key"
        mock_settings.NOTIFICATIONS_FROM_EMAIL = "alerts@test.com"
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.text = "Unprocessable"
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=mock_response)
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_email(to="bad@example.com", subject="X", html="<p>X</p>")

    assert result is False


def test_build_alert_email_critical():
    subject, html = build_alert_email(
        severity="critical",
        alert_type="circuit_breaker",
        message="Breaker tripped.",
    )
    assert "CRITICAL" in subject
    assert "Circuit Breaker" in subject
    assert "Breaker tripped." in html
    assert "#dc2626" in html  # red color for critical


def test_build_alert_email_warning():
    subject, html = build_alert_email(
        severity="warning",
        alert_type="anomaly",
        message="Unusual spend.",
    )
    assert "WARNING" in subject
    assert "#d97706" in html  # amber color for warning


# ---------------------------------------------------------------------------
# notification_service._dispatch
# ---------------------------------------------------------------------------

def _make_event(severity: str = "critical", alert_type: str = "circuit_breaker"):
    event = MagicMock()
    event.id = uuid.uuid4()
    event.severity = severity
    event.type = alert_type
    event.message = "Test alert message"
    event.notification_sent = False
    return event


def _make_channel(email: str = "admin@example.com"):
    channel = MagicMock()
    channel.id = uuid.uuid4()
    channel.type = "email"
    config = json.dumps({"email": email})
    # vault.decrypt will return this plaintext config
    channel.config_encrypted = "encrypted_placeholder"
    return channel, config


@pytest.mark.asyncio
async def test_dispatch_sends_email_and_marks_sent():
    org_id = uuid.uuid4()
    event = _make_event()
    channel, config_plain = _make_channel("admin@example.com")

    db = AsyncMock()
    db.commit = AsyncMock()

    with patch("app.services.notifications.notification_service.get_active_channels",
               return_value=[channel]):
        with patch("app.services.notifications.notification_service.get_key_vault") as mock_vault_fn:
            mock_vault = MagicMock()
            mock_vault.decrypt.return_value = config_plain
            mock_vault_fn.return_value = mock_vault

            with patch("app.services.notifications.notification_service.send_email",
                       return_value=True) as mock_send:
                await _dispatch(db, org_id, event)

    mock_send.assert_called_once()
    assert event.notification_sent is True
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_skips_when_no_channels():
    org_id = uuid.uuid4()
    event = _make_event()
    db = AsyncMock()

    with patch("app.services.notifications.notification_service.get_active_channels",
               return_value=[]):
        with patch("app.services.notifications.notification_service.send_email") as mock_send:
            await _dispatch(db, org_id, event)

    mock_send.assert_not_called()
    assert event.notification_sent is False


@pytest.mark.asyncio
async def test_dispatch_skips_channel_on_decrypt_error():
    org_id = uuid.uuid4()
    event = _make_event()
    channel, _ = _make_channel()
    db = AsyncMock()
    db.commit = AsyncMock()

    with patch("app.services.notifications.notification_service.get_active_channels",
               return_value=[channel]):
        with patch("app.services.notifications.notification_service.get_key_vault") as mock_vault_fn:
            mock_vault = MagicMock()
            mock_vault.decrypt.side_effect = Exception("bad key")
            mock_vault_fn.return_value = mock_vault

            with patch("app.services.notifications.notification_service.send_email") as mock_send:
                await _dispatch(db, org_id, event)

    mock_send.assert_not_called()
    db.commit.assert_not_called()
