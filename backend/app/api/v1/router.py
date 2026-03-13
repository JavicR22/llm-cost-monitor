from fastapi import APIRouter

from app.api.v1 import auth, dashboard, provider_keys, service_keys

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(service_keys.router)
router.include_router(provider_keys.router)
router.include_router(dashboard.router)
