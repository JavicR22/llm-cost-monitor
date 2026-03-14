"""
Notification channel repository.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import NotificationChannel


async def list_channels(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> list[NotificationChannel]:
    result = await db.execute(
        select(NotificationChannel)
        .where(NotificationChannel.organization_id == org_id)
        .order_by(NotificationChannel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_channels(
    db: AsyncSession,
    org_id: uuid.UUID,
    channel_type: Optional[str] = None,
) -> list[NotificationChannel]:
    """Return active channels for an org, optionally filtered by type."""
    q = select(NotificationChannel).where(
        NotificationChannel.organization_id == org_id,
        NotificationChannel.is_active == True,  # noqa: E712
    )
    if channel_type:
        q = q.where(NotificationChannel.type == channel_type)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_channel(
    db: AsyncSession,
    channel_id: uuid.UUID,
    org_id: uuid.UUID,
) -> NotificationChannel:
    result = await db.scalar(
        select(NotificationChannel).where(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == org_id,
        )
    )
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification channel not found")
    return result


async def create_channel(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    type: str,
    config_encrypted: str,
) -> NotificationChannel:
    channel = NotificationChannel(
        organization_id=org_id,
        type=type,
        config_encrypted=config_encrypted,
        is_active=True,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


async def delete_channel(
    db: AsyncSession,
    channel: NotificationChannel,
) -> None:
    await db.delete(channel)
    await db.commit()
