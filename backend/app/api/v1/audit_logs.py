"""
Audit log read endpoint — append-only, no writes via API.

GET /api/v1/audit-logs?limit=50&offset=0
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.core.dependencies import DB, CurrentUser
from app.repositories.audit_log_repo import list_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["audit"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[uuid.UUID]
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime


@router.get("", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user: CurrentUser,
    db: DB,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[AuditLogResponse]:
    """
    Paginated audit log for the current organization, newest first.
    Any authenticated user can read; writes only happen via internal hooks.
    """
    return await list_audit_logs(db, user.organization_id, limit=limit, offset=offset)
