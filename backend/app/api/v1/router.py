from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    analytics,
    audit_logs,
    auth,
    dashboard,
    developer_keys,
    members,
    notification_channels,
    projects,
    provider_keys,
    reports,
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
router.include_router(projects.router)
router.include_router(reports.router)
router.include_router(members.router)
router.include_router(developer_keys.router)
router.include_router(analytics.router)
