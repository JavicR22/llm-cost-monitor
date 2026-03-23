"""
Developer API key repository.
One key per developer user — unique constraint enforced at DB level.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_key import DeveloperAPIKey


async def get_by_user(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[DeveloperAPIKey]:
    """Return the developer key for a given user, or None."""
    return await db.scalar(
        select(DeveloperAPIKey).where(DeveloperAPIKey.user_id == user_id)
    )


async def create_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    key_hash: str,
    key_prefix: str,
    label: Optional[str] = None,
) -> DeveloperAPIKey:
    """Create and persist a new developer API key."""
    key = DeveloperAPIKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=label,
        is_active=True,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key


async def revoke_key(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """
    Revoke the developer key for the given user.
    Returns True if a key was found and revoked, False otherwise.
    """
    key = await get_by_user(db, user_id)
    if key is None or not key.is_active:
        return False
    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(key)
    return True
