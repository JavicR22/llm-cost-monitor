from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.schemas.dashboard import (
    ActivityResponse,
    DailySpend,
    SpendByModel,
    SummaryResponse,
)
from app.services.dashboard import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryResponse)
async def summary(
    user: CurrentUser,
    db: DB,
    days: int = Query(default=30, ge=1, le=365),
) -> SummaryResponse:
    """
    KPI cards: total spend, request count, avg cost, tokens.
    Includes % change vs the previous period of the same duration.
    """
    return await dashboard_service.get_summary(db, user.organization_id, days)


@router.get("/spend-over-time", response_model=list[DailySpend])
async def spend_over_time(
    user: CurrentUser,
    db: DB,
    days: int = Query(default=30, ge=1, le=365),
) -> list[DailySpend]:
    """Daily spend time series for the area chart."""
    return await dashboard_service.get_spend_over_time(db, user.organization_id, days)


@router.get("/spend-by-model", response_model=list[SpendByModel])
async def spend_by_model(
    user: CurrentUser,
    db: DB,
    days: int = Query(default=30, ge=1, le=365),
) -> list[SpendByModel]:
    """Spend breakdown by model — sorted by spend descending."""
    return await dashboard_service.get_spend_by_model(db, user.organization_id, days)


@router.get("/activity", response_model=ActivityResponse)
async def activity(
    user: CurrentUser,
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ActivityResponse:
    """Paginated recent usage log — the Recent Activity table."""
    return await dashboard_service.get_activity_page(
        db, user.organization_id, page, page_size
    )
