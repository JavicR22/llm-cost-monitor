from fastapi import APIRouter

from app.core.dependencies import DB, CurrentUser
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: DB) -> TokenResponse:
    return await auth_service.register(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DB) -> TokenResponse:
    return await auth_service.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DB) -> TokenResponse:
    return await auth_service.refresh(db, data)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        org_id=str(user.organization_id),
    )
