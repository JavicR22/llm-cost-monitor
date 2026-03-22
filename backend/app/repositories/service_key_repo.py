import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ServiceAPIKey


async def list_service_keys(
    db: AsyncSession, org_id: uuid.UUID
) -> list[ServiceAPIKey]:
    result = await db.execute(
        select(ServiceAPIKey)
        .where(ServiceAPIKey.organization_id == org_id)
        .order_by(ServiceAPIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_service_key(
    db: AsyncSession, key_id: uuid.UUID, org_id: uuid.UUID
) -> Optional[ServiceAPIKey]:
    """Return a key only if it belongs to the given org."""
    return await db.scalar(
        select(ServiceAPIKey).where(
            ServiceAPIKey.id == key_id,
            ServiceAPIKey.organization_id == org_id,
        )
    )


async def create_service_key(
    db: AsyncSession,
    org_id: uuid.UUID,
    key_hash: str,
    key_prefix: str,
    label: Optional[str],
    project_id: Optional[uuid.UUID] = None,
    team_id: Optional[uuid.UUID] = None,
    owner_user_id: Optional[uuid.UUID] = None,
) -> ServiceAPIKey:
    key = ServiceAPIKey(
        organization_id=org_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=label,
        project_id=project_id,
        team_id=team_id,
        owner_user_id=owner_user_id,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key


async def assign_service_key_layers(
    db: AsyncSession,
    key: ServiceAPIKey,
    project_id: Optional[uuid.UUID],
    team_id: Optional[uuid.UUID],
    owner_user_id: Optional[uuid.UUID],
) -> ServiceAPIKey:
    """Update FinOps attribution fields. Pass None to clear a field."""
    key.project_id = project_id
    key.team_id = team_id
    key.owner_user_id = owner_user_id
    await db.commit()
    await db.refresh(key)
    return key


async def revoke_service_key(
    db: AsyncSession, key: ServiceAPIKey
) -> ServiceAPIKey:
    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(key)
    return key
