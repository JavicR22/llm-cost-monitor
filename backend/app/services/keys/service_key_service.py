import uuid

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ServiceAPIKey
from app.repositories.service_key_repo import (
    assign_service_key_layers,
    create_service_key,
    get_service_key,
    list_service_keys,
    revoke_service_key,
)
from app.schemas.service_key import (
    ServiceKeyAssign,
    ServiceKeyCreate,
    ServiceKeyCreateResponse,
    ServiceKeyResponse,
)
from app.services.security.key_vault import get_key_vault

log = structlog.get_logger()


async def list_keys(db: AsyncSession, org_id: uuid.UUID) -> list[ServiceKeyResponse]:
    keys = await list_service_keys(db, org_id)
    return [_to_response(k) for k in keys]


async def create_key(
    db: AsyncSession, org_id: uuid.UUID, data: ServiceKeyCreate
) -> ServiceKeyCreateResponse:
    vault = get_key_vault()
    raw_key, key_hash, key_prefix = vault.generate_service_key()

    key = await create_service_key(
        db,
        org_id=org_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=data.label,
        project_id=data.project_id,
        team_id=data.team_id,
        owner_user_id=data.owner_user_id,
    )

    log.info("service_key_created", org_id=str(org_id), key_prefix=key_prefix)

    return ServiceKeyCreateResponse(
        id=str(key.id),
        label=key.label,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        raw_key=raw_key,  # shown once — never stored
    )


async def revoke_key(
    db: AsyncSession,
    redis: aioredis.Redis,
    key_id: uuid.UUID,
    org_id: uuid.UUID,
) -> ServiceKeyResponse:
    key = await get_service_key(db, key_id, org_id)
    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")
    if not key.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "API key is already revoked")

    key = await revoke_service_key(db, key)

    # Invalidate the Redis auth cache so the key stops working immediately
    from app.services.security.key_vault import KeyVault
    # We only have the hash stored — invalidate by key_hash
    cache_key = f"sk_valid:{key.key_hash}"
    await redis.delete(cache_key)

    log.info("service_key_revoked", org_id=str(org_id), key_id=str(key_id))

    return _to_response(key)


async def assign_layers(
    db: AsyncSession,
    key_id: uuid.UUID,
    org_id: uuid.UUID,
    data: ServiceKeyAssign,
) -> ServiceKeyResponse:
    key = await get_service_key(db, key_id, org_id)
    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")

    key = await assign_service_key_layers(
        db,
        key,
        project_id=data.project_id,
        team_id=data.team_id,
        owner_user_id=data.owner_user_id,
    )
    log.info(
        "service_key_layers_assigned",
        org_id=str(org_id),
        key_id=str(key_id),
        project_id=str(data.project_id),
        team_id=str(data.team_id),
    )
    return _to_response(key)


def _to_response(key: ServiceAPIKey) -> ServiceKeyResponse:
    return ServiceKeyResponse(
        id=str(key.id),
        label=key.label,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        project_id=key.project_id,
        team_id=key.team_id,
        owner_user_id=key.owner_user_id,
    )
