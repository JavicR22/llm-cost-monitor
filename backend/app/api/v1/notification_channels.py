"""
Notification channels CRUD.

Endpoints:
  GET    /api/v1/notification-channels           → list channels for org
  POST   /api/v1/notification-channels           → create channel (owner/admin)
  DELETE /api/v1/notification-channels/{id}      → delete channel (owner/admin)
"""
import json
import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DB, CurrentUser
from app.repositories.notification_channel_repo import (
    create_channel,
    delete_channel,
    get_channel,
    list_channels,
)
from app.schemas.notification_channel import (
    NotificationChannelCreate,
    NotificationChannelResponse,
)
from app.services.security.key_vault import get_key_vault

router = APIRouter(prefix="/notification-channels", tags=["notification-channels"])


def _require_owner_or_admin(user) -> None:
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")


def _mask_email(email: str) -> str:
    """u***@example.com"""
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}"


def _to_response(channel, vault) -> NotificationChannelResponse:
    try:
        config = json.loads(vault.decrypt(channel.config_encrypted))
        email = config.get("email", "")
        display_hint = _mask_email(email) if email else channel.type
    except Exception:
        display_hint = channel.type

    return NotificationChannelResponse(
        id=channel.id,
        type=channel.type,
        display_hint=display_hint,
        is_active=channel.is_active,
        created_at=channel.created_at,
    )


@router.get("", response_model=list[NotificationChannelResponse])
async def list_notification_channels(user: CurrentUser, db: DB):
    """List all notification channels for the current organization."""
    vault = get_key_vault()
    channels = await list_channels(db, user.organization_id)
    return [_to_response(ch, vault) for ch in channels]


@router.post("", response_model=NotificationChannelResponse, status_code=201)
async def create_notification_channel(
    data: NotificationChannelCreate, user: CurrentUser, db: DB
):
    """Add a notification channel. Requires owner or admin role."""
    _require_owner_or_admin(user)
    vault = get_key_vault()
    config_encrypted = vault.encrypt(json.dumps({"email": str(data.email)}))
    channel = await create_channel(
        db,
        user.organization_id,
        type=data.type,
        config_encrypted=config_encrypted,
    )
    return _to_response(channel, vault)


@router.delete("/{channel_id}", status_code=204)
async def delete_notification_channel(
    channel_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Delete a notification channel. Requires owner or admin role."""
    _require_owner_or_admin(user)
    channel = await get_channel(db, channel_id, user.organization_id)
    await delete_channel(db, channel)
