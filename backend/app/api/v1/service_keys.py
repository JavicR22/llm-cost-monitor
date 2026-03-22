from typing import Annotated
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
import redis.asyncio as aioredis

from app.core.dependencies import DB, CurrentUser, get_redis
from app.schemas.service_key import (
    ServiceKeyAssign,
    ServiceKeyCreate,
    ServiceKeyCreateResponse,
    ServiceKeyResponse,
)
from app.services.keys import service_key_service
from app.services.security import audit_service

router = APIRouter(prefix="/service-keys", tags=["service-keys"])

Redis = Annotated[aioredis.Redis, Depends(get_redis)]


@router.get("", response_model=list[ServiceKeyResponse])
async def list_keys(user: CurrentUser, db: DB) -> list[ServiceKeyResponse]:
    """List all service API keys for the current organization."""
    return await service_key_service.list_keys(db, user.organization_id)


@router.post("", response_model=ServiceKeyCreateResponse, status_code=201)
async def create_key(
    data: ServiceKeyCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> ServiceKeyCreateResponse:
    """
    Create a new service API key.
    The `raw_key` field is returned **once** — store it securely.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    result = await service_key_service.create_key(db, user.organization_id, data)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="key_created",
        entity_type="service_api_key",
        entity_id=uuid.UUID(result.id),
        details={"label": result.label, "prefix": result.key_prefix},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return result


@router.patch("/{key_id}/assign", response_model=ServiceKeyResponse)
async def assign_key_layers(
    key_id: uuid.UUID,
    data: ServiceKeyAssign,
    user: CurrentUser,
    db: DB,
    redis: Redis,
) -> ServiceKeyResponse:
    """
    Assign a service key to a FinOps attribution layer (project / team / owner).
    Pass null to clear a field.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    result = await service_key_service.assign_layers(db, key_id, user.organization_id, data)

    # Invalidate project summary cache so member counts refresh immediately
    if data.project_id is not None:
        await redis.delete(f"lcm:project:{data.project_id}:summary")

    return result


@router.delete("/{key_id}", response_model=ServiceKeyResponse)
async def revoke_key(
    key_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
    redis: Redis,
) -> ServiceKeyResponse:
    """
    Revoke a service API key immediately.
    The key stops working within seconds (Redis cache invalidated).
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    result = await service_key_service.revoke_key(db, redis, key_id, user.organization_id)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="key_revoked",
        entity_type="service_api_key",
        entity_id=key_id,
        details={"prefix": result.key_prefix},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return result


def _require_owner_or_admin(user) -> None:
    from fastapi import HTTPException, status
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")
