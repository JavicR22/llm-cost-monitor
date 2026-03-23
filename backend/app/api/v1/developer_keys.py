"""
Developer API key endpoints.
Each developer (role='developer') gets exactly one personal proxy key.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel

from app.core.dependencies import DB, CurrentUser
from app.repositories.developer_key_repo import (
    create_key,
    get_by_user,
    revoke_key,
)
from app.services.security import audit_service

log = structlog.get_logger()
router = APIRouter(prefix="/developer-keys", tags=["developer-keys"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DeveloperKeyGenerateResponse(BaseModel):
    raw_key: str
    key_prefix: str
    created_at: datetime


class DeveloperKeyResponse(BaseModel):
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_developer(user) -> None:
    if user.role != "developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer role required",
        )


def _generate_dev_key() -> tuple[str, str, str]:
    """
    Returns (raw_key, key_hash, key_prefix).
    Format: lcm_dev_{64 hex chars}
    Prefix stored: lcm_dev_...***<last 4 chars>
    """
    raw = f"lcm_dev_{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    suffix = raw[-4:]
    key_prefix = f"lcm_dev_...***{suffix}"
    return raw, key_hash, key_prefix


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=DeveloperKeyGenerateResponse, status_code=201)
async def generate_developer_key(
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> DeveloperKeyGenerateResponse:
    """
    Generate a personal developer API key.
    Requires 'developer' role.
    Only one active key per developer — raises 409 if one already exists.
    The raw key is returned once and never stored.
    """
    _require_developer(user)

    existing = await get_by_user(db, user.id)
    if existing is not None and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active developer key already exists. Revoke it before generating a new one.",
        )

    raw_key, key_hash, key_prefix = _generate_dev_key()
    key = await create_key(db, user_id=user.id, key_hash=key_hash, key_prefix=key_prefix)

    # Mark user as having seen the key modal
    user.has_seen_key_modal = True
    await db.commit()

    log.info("developer_key_generated", user_id=str(user.id), key_prefix=key_prefix)

    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="developer_key_generated",
        entity_type="developer_api_key",
        entity_id=key.id,
        details={"key_prefix": key_prefix},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )

    return DeveloperKeyGenerateResponse(
        raw_key=raw_key,
        key_prefix=key_prefix,
        created_at=key.created_at,
    )


@router.get("/me", response_model=DeveloperKeyResponse)
async def get_my_developer_key(
    user: CurrentUser,
    db: DB,
) -> DeveloperKeyResponse:
    """
    Get the current developer's key metadata.
    Never returns the raw key.
    """
    _require_developer(user)

    key = await get_by_user(db, user.id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No developer key found. Generate one first.",
        )

    return DeveloperKeyResponse(
        key_prefix=key.key_prefix,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        is_active=key.is_active,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_my_developer_key(
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> None:
    """
    Revoke the current developer's API key.
    The key stops working immediately.
    """
    _require_developer(user)

    revoked = await revoke_key(db, user.id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active developer key found.",
        )

    log.info("developer_key_revoked", user_id=str(user.id))

    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="developer_key_revoked",
        entity_type="developer_api_key",
        details={},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
