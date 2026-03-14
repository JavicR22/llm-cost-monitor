"""
Alert rules CRUD + alert events history.

Endpoints:
  GET    /api/v1/alerts/rules            → list all rules for org
  POST   /api/v1/alerts/rules            → create rule (owner/admin)
  PATCH  /api/v1/alerts/rules/{rule_id}  → update rule (owner/admin)
  DELETE /api/v1/alerts/rules/{rule_id}  → delete rule (owner/admin)
  GET    /api/v1/alerts/events           → paginated event history
  GET    /api/v1/alerts/circuit-breaker  → circuit breaker status
  POST   /api/v1/alerts/circuit-breaker/unlock → manual unlock (owner/admin)
"""
import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from app.core.dependencies import DB, CurrentUser, get_redis
from app.repositories.alert_repo import (
    create_alert_rule,
    delete_alert_rule,
    get_alert_rule,
    list_alert_events,
    list_alert_rules,
    update_alert_rule,
)
from app.schemas.alert import (
    AlertEventResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    CircuitBreakerStatus,
)
from app.services.alerts.alert_engine import get_alert_engine
from app.services.security import audit_service

router = APIRouter(prefix="/alerts", tags=["alerts"])

Redis = Annotated[aioredis.Redis, Depends(get_redis)]


def _require_owner_or_admin(user) -> None:
    from fastapi import HTTPException, status
    if user.role not in ("owner", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner or admin role required")


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(user: CurrentUser, db: DB) -> list[AlertRuleResponse]:
    """List all alert rules for the current organization."""
    return await list_alert_rules(db, user.organization_id)


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_rule(
    data: AlertRuleCreate, user: CurrentUser, db: DB
) -> AlertRuleResponse:
    """Create a new alert rule. Requires owner or admin role."""
    _require_owner_or_admin(user)
    return await create_alert_rule(
        db,
        user.organization_id,
        type=data.type,
        scope=data.scope,
        threshold_value=data.threshold_value,
        anomaly_multiplier=data.anomaly_multiplier,
        is_active=data.is_active,
    )


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: uuid.UUID, data: AlertRuleUpdate, user: CurrentUser, db: DB
) -> AlertRuleResponse:
    """Update threshold, multiplier or active status. Requires owner or admin."""
    _require_owner_or_admin(user)
    rule = await get_alert_rule(db, rule_id, user.organization_id)
    return await update_alert_rule(
        db,
        rule,
        threshold_value=data.threshold_value,
        anomaly_multiplier=data.anomaly_multiplier,
        is_active=data.is_active,
    )


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: uuid.UUID, user: CurrentUser, db: DB
) -> None:
    """Delete an alert rule permanently. Requires owner or admin."""
    _require_owner_or_admin(user)
    rule = await get_alert_rule(db, rule_id, user.organization_id)
    await delete_alert_rule(db, rule)


# ---------------------------------------------------------------------------
# Alert Events (read-only history)
# ---------------------------------------------------------------------------

@router.get("/events", response_model=list[AlertEventResponse])
async def list_events(
    user: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[AlertEventResponse]:
    """Paginated alert event history for the current organization."""
    return await list_alert_events(db, user.organization_id, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------

@router.get("/circuit-breaker", response_model=CircuitBreakerStatus)
async def circuit_breaker_status(
    user: CurrentUser, redis: Redis
) -> CircuitBreakerStatus:
    """Check whether the circuit breaker is currently open."""
    is_open = await get_alert_engine().is_circuit_open(user.organization_id, redis)
    return CircuitBreakerStatus(is_open=is_open)


@router.post("/circuit-breaker/unlock", response_model=CircuitBreakerStatus)
async def unlock_circuit_breaker(
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    redis: Redis,
) -> CircuitBreakerStatus:
    """
    Manually unlock the circuit breaker.
    Requires owner or admin role.
    """
    _require_owner_or_admin(user)
    await get_alert_engine().unlock_circuit_breaker(user.organization_id, redis)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="circuit_breaker_released",
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return CircuitBreakerStatus(is_open=False)
