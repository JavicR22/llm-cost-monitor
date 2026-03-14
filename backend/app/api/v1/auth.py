from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.core.dependencies import DB, CurrentUser
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import auth_service
from app.services.security import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _ua(request: Request) -> str | None:
    return request.headers.get("User-Agent")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DB,
) -> TokenResponse:
    result = await auth_service.register(db, data)
    # Decode org_id from the fresh token for the audit entry
    from app.core.security import decode_token
    payload = decode_token(result.access_token)
    import uuid
    org_id = uuid.UUID(payload["org_id"])
    user_id = uuid.UUID(payload["sub"])
    background_tasks.add_task(
        audit_service.log,
        org_id=org_id,
        user_id=user_id,
        action="login",
        details={"event": "register"},
        ip=_ip(request),
        ua=_ua(request),
    )
    return result


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DB,
) -> TokenResponse:
    try:
        result = await auth_service.login(db, data)
    except HTTPException as exc:
        if exc.status_code == 401:
            # Log failed attempt inline (can't use background_tasks — we're re-raising)
            from sqlalchemy import select
            from app.models import User
            user = await db.scalar(select(User).where(User.email == data.email))
            if user:
                import asyncio
                asyncio.ensure_future(
                    audit_service.log(
                        org_id=user.organization_id,
                        user_id=user.id,
                        action="login_failed",
                        details={"email": data.email},
                        ip=_ip(request),
                        ua=_ua(request),
                    )
                )
        raise

    from app.core.security import decode_token
    import uuid
    payload = decode_token(result.access_token)
    org_id = uuid.UUID(payload["org_id"])
    user_id = uuid.UUID(payload["sub"])
    background_tasks.add_task(
        audit_service.log,
        org_id=org_id,
        user_id=user_id,
        action="login",
        ip=_ip(request),
        ua=_ua(request),
    )
    return result


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
