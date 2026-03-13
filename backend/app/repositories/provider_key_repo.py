import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ProviderAPIKey
from app.models.provider import Provider


async def get_provider_by_name(db: AsyncSession, name: str) -> Optional[Provider]:
    return await db.scalar(
        select(Provider).where(Provider.name == name, Provider.is_active == True)  # noqa: E712
    )


async def list_provider_keys(
    db: AsyncSession, org_id: uuid.UUID
) -> list[ProviderAPIKey]:
    result = await db.execute(
        select(ProviderAPIKey)
        .where(ProviderAPIKey.organization_id == org_id)
        .order_by(ProviderAPIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_provider_key(
    db: AsyncSession, key_id: uuid.UUID, org_id: uuid.UUID
) -> Optional[ProviderAPIKey]:
    return await db.scalar(
        select(ProviderAPIKey).where(
            ProviderAPIKey.id == key_id,
            ProviderAPIKey.organization_id == org_id,
        )
    )


async def create_provider_key(
    db: AsyncSession,
    org_id: uuid.UUID,
    provider_id: uuid.UUID,
    provider: str,
    key_ciphertext: str,
    key_prefix: str,
    label: Optional[str],
) -> ProviderAPIKey:
    key = ProviderAPIKey(
        organization_id=org_id,
        provider_id=provider_id,
        provider=provider,
        key_ciphertext=key_ciphertext,
        key_prefix=key_prefix,
        label=label,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return key


async def revoke_provider_key(
    db: AsyncSession, key: ProviderAPIKey
) -> ProviderAPIKey:
    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(key)
    return key
