import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Organization, User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    return _SLUG_RE.sub("-", name.lower()).strip("-")


async def register(db: AsyncSession, data: RegisterRequest) -> TokenResponse:
    # Check email uniqueness
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    # Create organization
    slug = _slugify(data.org_name)
    # Ensure slug uniqueness by appending a short suffix if needed
    base_slug = slug
    counter = 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=data.org_name, slug=slug)
    db.add(org)
    await db.flush()  # get org.id before creating user

    # Create owner user
    user = User(
        organization_id=org.id,
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role="owner",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), str(org.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    org = await db.get(Organization, user.organization_id)
    if not org or not org.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization is inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), str(org.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def refresh(db: AsyncSession, data: RefreshRequest) -> TokenResponse:
    from jose import JWTError

    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")

    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    org = await db.get(Organization, user.organization_id)
    if not org or not org.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization is inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), str(org.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )
