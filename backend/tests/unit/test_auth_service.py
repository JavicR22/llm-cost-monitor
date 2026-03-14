"""
Unit tests for auth_service — register, login, refresh.
All DB interactions are mocked.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.services.auth import auth_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    *,
    email: str = "test@example.com",
    password: str = "hashed_pw",
    role: str = "owner",
    org_active: bool = True,
) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.password_hash = password
    user.role = role
    user.organization_id = uuid.uuid4()
    return user


def _make_org(*, is_active: bool = True) -> MagicMock:
    org = MagicMock()
    org.id = uuid.uuid4()
    org.is_active = is_active
    org.slug = "acme"
    return org


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------

def test_slugify_basic():
    assert auth_service._slugify("Acme Corp") == "acme-corp"


def test_slugify_removes_special_chars():
    assert auth_service._slugify("My  Company!!") == "my-company"


def test_slugify_all_lowercase():
    result = auth_service._slugify("OpenAI")
    assert result == result.lower()


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

class TestRegister:
    @pytest.mark.asyncio
    async def test_raises_409_on_duplicate_email(self):
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=_make_user())  # email exists

        with pytest.raises(HTTPException) as exc:
            await auth_service.register(
                db,
                RegisterRequest(email="dup@example.com", password="password123", name="A", org_name="B"),
            )
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_returns_tokens_on_success(self):
        db = AsyncMock()
        # First scalar = no existing user; second scalar = no slug conflict
        db.scalar = AsyncMock(side_effect=[None, None])
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        org = _make_org()
        user = _make_user()

        db.refresh = AsyncMock()

        with patch("app.services.auth.auth_service.hash_password", return_value="hashed"):
            with patch("app.services.auth.auth_service.create_access_token", return_value="access_tok"):
                with patch("app.services.auth.auth_service.create_refresh_token", return_value="refresh_tok"):
                    # Intercept db.add so we can control org.id and user.id
                    added = []
                    def fake_add(obj):
                        if hasattr(obj, "slug"):
                            obj.id = org.id
                        else:
                            obj.id = user.id
                            obj.organization_id = org.id
                            obj.role = "owner"
                        added.append(obj)

                    db.add = fake_add
                    result = await auth_service.register(
                        db,
                        RegisterRequest(
                            email="new@example.com",
                            password="password123",
                            name="Alice",
                            org_name="Acme",
                        ),
                    )

        assert result.access_token == "access_tok"
        assert result.refresh_token == "refresh_tok"

    @pytest.mark.asyncio
    async def test_user_is_created_with_owner_role(self):
        db = AsyncMock()
        db.scalar = AsyncMock(side_effect=[None, None])
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        org = _make_org()
        user = _make_user()
        created_users = []

        def fake_add(obj):
            if not hasattr(obj, "slug"):
                obj.id = user.id
                obj.organization_id = org.id
                created_users.append(obj)
            else:
                obj.id = org.id

        db.add = fake_add
        db.refresh = AsyncMock()

        with patch("app.services.auth.auth_service.hash_password", return_value="hashed"):
            with patch("app.services.auth.auth_service.create_access_token", return_value="tok"):
                with patch("app.services.auth.auth_service.create_refresh_token", return_value="rtok"):
                    await auth_service.register(
                        db,
                        RegisterRequest(
                            email="alice@example.com",
                            password="password123",
                            name="Alice",
                            org_name="Acme",
                        ),
                    )

        assert any(getattr(u, "role", None) == "owner" for u in created_users)


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:
    @pytest.mark.asyncio
    async def test_raises_401_for_unknown_email(self):
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)  # user not found

        with pytest.raises(HTTPException) as exc:
            await auth_service.login(
                db, LoginRequest(email="ghost@example.com", password="password123")
            )
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_for_wrong_password(self):
        user = _make_user(password="correct_hash")
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=user)

        with patch("app.services.auth.auth_service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await auth_service.login(
                    db, LoginRequest(email="user@example.com", password="wrong")
                )
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_403_for_inactive_org(self):
        user = _make_user()
        org = _make_org(is_active=False)
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=user)
        db.get = AsyncMock(return_value=org)

        with patch("app.services.auth.auth_service.verify_password", return_value=True):
            with pytest.raises(HTTPException) as exc:
                await auth_service.login(
                    db, LoginRequest(email="user@example.com", password="password123")
                )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_tokens_on_valid_credentials(self):
        user = _make_user()
        org = _make_org(is_active=True)
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=user)
        db.get = AsyncMock(return_value=org)

        with patch("app.services.auth.auth_service.verify_password", return_value=True):
            with patch("app.services.auth.auth_service.create_access_token", return_value="access"):
                with patch("app.services.auth.auth_service.create_refresh_token", return_value="refresh"):
                    result = await auth_service.login(
                        db, LoginRequest(email="user@example.com", password="password123")
                    )

        assert result.access_token == "access"
        assert result.refresh_token == "refresh"

    @pytest.mark.asyncio
    async def test_raises_403_when_org_not_found(self):
        user = _make_user()
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=user)
        db.get = AsyncMock(return_value=None)  # org missing

        with patch("app.services.auth.auth_service.verify_password", return_value=True):
            with pytest.raises(HTTPException) as exc:
                await auth_service.login(
                    db, LoginRequest(email="user@example.com", password="password123")
                )
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_token(self):
        from jose import JWTError
        db = AsyncMock()

        with patch("app.services.auth.auth_service.decode_token", side_effect=JWTError("bad")):
            with pytest.raises(HTTPException) as exc:
                await auth_service.refresh(db, RefreshRequest(refresh_token="garbage"))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_when_token_is_access_type(self):
        db = AsyncMock()

        with patch(
            "app.services.auth.auth_service.decode_token",
            return_value={"type": "access", "sub": str(uuid.uuid4())},
        ):
            with pytest.raises(HTTPException) as exc:
                await auth_service.refresh(db, RefreshRequest(refresh_token="access_tok"))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_when_user_not_found(self):
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with patch(
            "app.services.auth.auth_service.decode_token",
            return_value={"type": "refresh", "sub": str(uuid.uuid4())},
        ):
            with pytest.raises(HTTPException) as exc:
                await auth_service.refresh(db, RefreshRequest(refresh_token="rtok"))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_new_tokens_on_valid_refresh(self):
        user = _make_user()
        org = _make_org(is_active=True)
        db = AsyncMock()
        # db.get called twice: first for user, then for org
        db.get = AsyncMock(side_effect=[user, org])

        with patch(
            "app.services.auth.auth_service.decode_token",
            return_value={"type": "refresh", "sub": str(user.id)},
        ):
            with patch("app.services.auth.auth_service.create_access_token", return_value="new_access"):
                with patch("app.services.auth.auth_service.create_refresh_token", return_value="new_refresh"):
                    result = await auth_service.refresh(
                        db, RefreshRequest(refresh_token="valid_rtok")
                    )

        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"
