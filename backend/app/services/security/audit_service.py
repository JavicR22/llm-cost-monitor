"""
Audit service — fire-and-forget logging for sensitive actions.

All public functions open their own DB session and swallow errors so
they never block or break the request path.

Usage (background task):
    background_tasks.add_task(
        audit_service.log,
        org_id=org_id,
        user_id=user_id,
        action="key_created",
        entity_type="service_api_key",
        entity_id=key.id,
        ip=request.client.host,
        ua=request.headers.get("User-Agent"),
    )

Usage (inline, e.g. for login_failed where we re-raise immediately):
    await audit_service.log(...)
"""
from __future__ import annotations

import uuid
from typing import Optional

import structlog

from app.core.database import AsyncSessionFactory
from app.repositories.audit_log_repo import insert_audit_log

_log = structlog.get_logger()


async def log(
    *,
    org_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> None:
    """
    Persist one audit event. Never raises — swallows all errors.
    Opens its own DB session (safe to use as a BackgroundTask).
    """
    try:
        async with AsyncSessionFactory() as db:
            await insert_audit_log(
                db,
                organization_id=org_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip,
                user_agent=ua,
            )
        _log.info("audit_logged", org_id=str(org_id), action=action)
    except Exception:
        _log.exception("audit_log_failed", org_id=str(org_id), action=action)
