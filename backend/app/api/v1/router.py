from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    audit_logs,
    auth,
    dashboard,
    notification_channels,
    provider_keys,
    service_keys,
)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(service_keys.router)
router.include_router(provider_keys.router)
router.include_router(dashboard.router)
router.include_router(alerts.router)
router.include_router(notification_channels.router)
router.include_router(audit_logs.router)
