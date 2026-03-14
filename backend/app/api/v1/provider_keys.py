import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.core.dependencies import DB, CurrentUser
from app.schemas.provider_key import ProviderKeyCreate, ProviderKeyResponse
from app.services.keys import provider_key_service
from app.services.security import audit_service

router = APIRouter(prefix="/provider-keys", tags=["provider-keys"])


@router.get("", response_model=list[ProviderKeyResponse])
async def list_keys(user: CurrentUser, db: DB) -> list[ProviderKeyResponse]:
    """List all provider API keys for the current organization (prefix only)."""
    return await provider_key_service.list_keys(db, user.organization_id)


@router.post("", response_model=ProviderKeyResponse, status_code=201)
async def create_key(
    data: ProviderKeyCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> ProviderKeyResponse:
    """
    Store a provider API key (OpenAI, Anthropic, etc.) encrypted at rest.
    The raw key is never returned after this call.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    result = await provider_key_service.create_key(db, user.organization_id, data)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="key_created",
        entity_type="provider_api_key",
        entity_id=uuid.UUID(result.id),
        details={"provider": result.provider, "prefix": result.key_prefix},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return result


@router.delete("/{key_id}", response_model=ProviderKeyResponse)
async def revoke_key(
    key_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> ProviderKeyResponse:
    """
    Revoke a provider API key.
    The proxy will immediately stop using it for new requests.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    result = await provider_key_service.revoke_key(db, key_id, user.organization_id)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="key_revoked",
        entity_type="provider_api_key",
        entity_id=key_id,
        details={"provider": result.provider, "prefix": result.key_prefix},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return result


def _require_owner_or_admin(user) -> None:
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")
