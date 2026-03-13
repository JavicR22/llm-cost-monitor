import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ProviderAPIKey
from app.repositories.provider_key_repo import (
    create_provider_key,
    get_provider_by_name,
    get_provider_key,
    list_provider_keys,
    revoke_provider_key,
)
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyResponse
from app.services.security.key_vault import get_key_vault

log = structlog.get_logger()


async def list_keys(db: AsyncSession, org_id: uuid.UUID) -> list[ProviderKeyResponse]:
    keys = await list_provider_keys(db, org_id)
    return [_to_response(k) for k in keys]


async def create_key(
    db: AsyncSession, org_id: uuid.UUID, data: ProviderKeyCreate
) -> ProviderKeyResponse:
    # Resolve provider_id from DB
    provider = await get_provider_by_name(db, data.provider)
    if not provider:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Provider '{data.provider}' is not supported or inactive.",
        )

    vault = get_key_vault()

    # Encrypt the raw key — it must never be stored in plaintext
    ciphertext = vault.encrypt(data.raw_key)
    key_prefix = vault.extract_prefix(data.raw_key)

    key = await create_provider_key(
        db,
        org_id=org_id,
        provider_id=provider.id,
        provider=data.provider,
        key_ciphertext=ciphertext,
        key_prefix=key_prefix,
        label=data.label,
    )

    log.info(
        "provider_key_created",
        org_id=str(org_id),
        provider=data.provider,
        key_prefix=key_prefix,
    )

    return _to_response(key)


async def revoke_key(
    db: AsyncSession,
    key_id: uuid.UUID,
    org_id: uuid.UUID,
) -> ProviderKeyResponse:
    key = await get_provider_key(db, key_id, org_id)
    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider key not found")
    if not key.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "Provider key is already revoked")

    key = await revoke_provider_key(db, key)

    # Invalidate the pricing/model cache is not needed here —
    # the proxy_service.get_decrypted_provider_key() queries the DB live each request.
    log.info("provider_key_revoked", org_id=str(org_id), key_id=str(key_id))

    return _to_response(key)


def _to_response(key: ProviderAPIKey) -> ProviderKeyResponse:
    return ProviderKeyResponse(
        id=str(key.id),
        provider=key.provider,
        key_prefix=key.key_prefix,
        label=key.label,
        is_active=key.is_active,
        created_at=key.created_at,
        last_validated_at=key.last_validated_at,
    )
