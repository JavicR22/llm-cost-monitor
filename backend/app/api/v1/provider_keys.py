import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DB, CurrentUser
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyResponse
from app.services.keys import provider_key_service

router = APIRouter(prefix="/provider-keys", tags=["provider-keys"])


@router.get("", response_model=list[ProviderKeyResponse])
async def list_keys(user: CurrentUser, db: DB) -> list[ProviderKeyResponse]:
    """List all provider API keys for the current organization (prefix only)."""
    return await provider_key_service.list_keys(db, user.organization_id)


@router.post("", response_model=ProviderKeyResponse, status_code=201)
async def create_key(
    data: ProviderKeyCreate, user: CurrentUser, db: DB
) -> ProviderKeyResponse:
    """
    Store a provider API key (OpenAI, Anthropic, etc.) encrypted at rest.
    The raw key is never returned after this call.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    return await provider_key_service.create_key(db, user.organization_id, data)


@router.delete("/{key_id}", response_model=ProviderKeyResponse)
async def revoke_key(
    key_id: uuid.UUID, user: CurrentUser, db: DB
) -> ProviderKeyResponse:
    """
    Revoke a provider API key.
    The proxy will immediately stop using it for new requests.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    return await provider_key_service.revoke_key(db, key_id, user.organization_id)


def _require_owner_or_admin(user) -> None:
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")
