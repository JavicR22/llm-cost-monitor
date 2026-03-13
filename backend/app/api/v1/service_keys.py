from typing import Annotated
import uuid

from fastapi import APIRouter, Depends
import redis.asyncio as aioredis

from app.core.dependencies import DB, CurrentUser, get_redis
from app.schemas.service_key import ServiceKeyCreate, ServiceKeyCreateResponse, ServiceKeyResponse
from app.services.keys import service_key_service

router = APIRouter(prefix="/service-keys", tags=["service-keys"])

Redis = Annotated[aioredis.Redis, Depends(get_redis)]


@router.get("", response_model=list[ServiceKeyResponse])
async def list_keys(user: CurrentUser, db: DB) -> list[ServiceKeyResponse]:
    """List all service API keys for the current organization."""
    return await service_key_service.list_keys(db, user.organization_id)


@router.post("", response_model=ServiceKeyCreateResponse, status_code=201)
async def create_key(
    data: ServiceKeyCreate, user: CurrentUser, db: DB
) -> ServiceKeyCreateResponse:
    """
    Create a new service API key.
    The `raw_key` field is returned **once** — store it securely.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    return await service_key_service.create_key(db, user.organization_id, data)


@router.delete("/{key_id}", response_model=ServiceKeyResponse)
async def revoke_key(
    key_id: uuid.UUID, user: CurrentUser, db: DB, redis: Redis
) -> ServiceKeyResponse:
    """
    Revoke a service API key immediately.
    The key stops working within seconds (Redis cache invalidated).
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    return await service_key_service.revoke_key(db, redis, key_id, user.organization_id)


def _require_owner_or_admin(user) -> None:
    from fastapi import HTTPException, status
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")
