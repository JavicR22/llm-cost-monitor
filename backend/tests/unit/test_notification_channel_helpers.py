"""
Unit tests for notification_channels helpers:
  _mask_email, _to_response
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.api.v1.notification_channels import _mask_email, _to_response


# ---------------------------------------------------------------------------
# _mask_email
# ---------------------------------------------------------------------------

class TestMaskEmail:
    def test_standard_email(self):
        assert _mask_email("alice@example.com") == "a***@example.com"

    def test_single_char_local(self):
        assert _mask_email("x@example.com") == "x***@example.com"

    def test_long_local_part(self):
        result = _mask_email("verylongname@domain.io")
        assert result.startswith("v***@")
        assert result.endswith("domain.io")

    def test_subdomain_preserved(self):
        result = _mask_email("u@mail.company.co.uk")
        assert result == "u***@mail.company.co.uk"

    def test_preserves_domain_exactly(self):
        domain = "my-company.com"
        result = _mask_email(f"admin@{domain}")
        assert result.endswith(f"@{domain}")


# ---------------------------------------------------------------------------
# _to_response
# ---------------------------------------------------------------------------

def _make_channel(encrypted_config: str) -> MagicMock:
    ch = MagicMock()
    ch.id = uuid.uuid4()
    ch.type = "email"
    ch.config_encrypted = encrypted_config
    ch.is_active = True
    ch.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return ch


class TestToResponse:
    def test_returns_masked_email_on_success(self):
        vault = MagicMock()
        vault.decrypt.return_value = json.dumps({"email": "admin@example.com"})

        channel = _make_channel("encrypted")
        result = _to_response(channel, vault)

        assert result.display_hint == "a***@example.com"
        assert result.type == "email"
        assert result.is_active is True

    def test_falls_back_to_type_on_decrypt_error(self):
        vault = MagicMock()
        vault.decrypt.side_effect = Exception("bad key")

        channel = _make_channel("corrupt")
        result = _to_response(channel, vault)

        assert result.display_hint == "email"

    def test_falls_back_to_type_when_email_missing_from_config(self):
        vault = MagicMock()
        vault.decrypt.return_value = json.dumps({})  # no "email" key

        channel = _make_channel("encrypted")
        result = _to_response(channel, vault)

        assert result.display_hint == "email"

    def test_response_id_matches_channel_id(self):
        vault = MagicMock()
        vault.decrypt.return_value = json.dumps({"email": "a@b.com"})

        channel = _make_channel("enc")
        result = _to_response(channel, vault)

        assert result.id == channel.id
