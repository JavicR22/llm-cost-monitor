"""
Proxy repository — DB queries for the request hot path.
All methods are read-only and must be fast.
"""
import uuid
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ProviderAPIKey, ServiceAPIKey

log = structlog.get_logger()


async def get_service_key_by_hash(
    db: AsyncSession, key_hash: str
) -> Optional[ServiceAPIKey]:
    """Look up an active service key by its SHA-256 hash."""
    result = await db.execute(
        select(ServiceAPIKey).where(
            ServiceAPIKey.key_hash == key_hash,
            ServiceAPIKey.is_active == True,  # noqa: E712
            ServiceAPIKey.revoked_at == None,  # noqa: E711
        )
    )
    return result.scalar_one_or_none()


async def get_active_provider_key(
    db: AsyncSession, org_id: uuid.UUID, provider: str
) -> Optional[ProviderAPIKey]:
    """Return the first active provider key for an org+provider pair."""
    result = await db.execute(
        select(ProviderAPIKey).where(
            ProviderAPIKey.organization_id == org_id,
            ProviderAPIKey.provider == provider,
            ProviderAPIKey.is_active == True,  # noqa: E712
            ProviderAPIKey.revoked_at == None,  # noqa: E711
        )
    )
    return result.scalar_one_or_none()
