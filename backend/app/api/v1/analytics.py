"""
Analytics endpoints — aggregated spend, usage, and project/team/developer breakdowns.
All endpoints require owner, admin, or project_leader role.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DB, require_role
from app.models.api_key import ServiceAPIKey
from app.models.project import Project
from app.models.team import Team
from app.models.usage_log import UsageLog
from app.models.user import User

log = structlog.get_logger()
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Role guard
AnalyticsUser = Annotated[User, Depends(require_role("owner", "admin", "project_leader"))]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OverviewResponse(BaseModel):
    total_spend: str
    total_requests: int
    active_projects: int
    active_developers: int
    spend_trend_pct: Optional[float] = None


class ProjectAnalyticsItem(BaseModel):
    id: str
    name: str
    spend_30d: str
    requests_30d: int
    teams_count: int
    members_count: int
    budget: Optional[str]
    budget_used_pct: Optional[float]


class TeamAnalyticsItem(BaseModel):
    id: str
    name: str
    spend: str
    requests: int
    members_count: int


class DeveloperAnalyticsItem(BaseModel):
    user_id: str
    name: str
    email: str
    spend_30d: str
    requests_30d: int
    tokens_30d: int
    last_active: Optional[datetime]


class TimeseriesPoint(BaseModel):
    date: str
    spend: str
    requests: int


class TimeseriesResponse(BaseModel):
    series: list[TimeseriesPoint]


class ModelUsageItem(BaseModel):
    model_name: str
    spend: str
    requests: int
    tokens: int
    pct_of_total: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_range(range_str: str) -> tuple[datetime, datetime]:
    """Convert a range string ('7d', '30d', '90d') to (from_date, to_date)."""
    valid = {"7d": 7, "30d": 30, "90d": 90}
    days = valid.get(range_str)
    if days is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid range '{range_str}'. Use one of: 7d, 30d, 90d",
        )
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)
    return from_date, to_date


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=OverviewResponse)
async def analytics_overview(
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
) -> OverviewResponse:
    """Organization-level spend overview for the given date range."""
    from_date, to_date = _parse_range(range)
    days = (to_date - from_date).days

    # Current period aggregates
    current = await db.execute(
        select(
            func.coalesce(func.sum(UsageLog.cost_usd), 0).label("total_spend"),
            func.count(UsageLog.id).label("total_requests"),
        ).where(
            UsageLog.organization_id == user.organization_id,
            UsageLog.created_at >= from_date,
            UsageLog.created_at < to_date,
        )
    )
    cur = current.one()
    total_spend = Decimal(str(cur.total_spend))
    total_requests = int(cur.total_requests)

    # Previous period for trend
    prev_from = from_date - timedelta(days=days)
    prev = await db.execute(
        select(
            func.coalesce(func.sum(UsageLog.cost_usd), 0).label("prev_spend"),
        ).where(
            UsageLog.organization_id == user.organization_id,
            UsageLog.created_at >= prev_from,
            UsageLog.created_at < from_date,
        )
    )
    prev_spend = Decimal(str(prev.scalar_one()))

    if prev_spend > 0:
        trend_pct = float((total_spend - prev_spend) / prev_spend * 100)
    else:
        trend_pct = None

    # Active projects: projects with at least one log in range
    proj_result = await db.execute(
        select(func.count(func.distinct(UsageLog.project_id))).where(
            UsageLog.organization_id == user.organization_id,
            UsageLog.created_at >= from_date,
            UsageLog.created_at < to_date,
            UsageLog.project_id.isnot(None),
        )
    )
    active_projects = int(proj_result.scalar_one() or 0)

    # Active developers: users with at least one log in range
    dev_result = await db.execute(
        select(func.count(func.distinct(UsageLog.user_id))).where(
            UsageLog.organization_id == user.organization_id,
            UsageLog.created_at >= from_date,
            UsageLog.created_at < to_date,
            UsageLog.user_id.isnot(None),
        )
    )
    active_developers = int(dev_result.scalar_one() or 0)

    return OverviewResponse(
        total_spend=str(total_spend),
        total_requests=total_requests,
        active_projects=active_projects,
        active_developers=active_developers,
        spend_trend_pct=round(trend_pct, 2) if trend_pct is not None else None,
    )


@router.get("/projects", response_model=list[ProjectAnalyticsItem])
async def analytics_projects(
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
) -> list[ProjectAnalyticsItem]:
    """Per-project spend, requests, team/member counts and budget utilization."""
    from_date, to_date = _parse_range(range)

    # All projects for this org
    projects_result = await db.execute(
        select(Project).where(Project.organization_id == user.organization_id)
    )
    projects = list(projects_result.scalars().all())

    items: list[ProjectAnalyticsItem] = []
    for project in projects:
        # Spend + requests
        agg = await db.execute(
            select(
                func.coalesce(func.sum(UsageLog.cost_usd), 0).label("spend"),
                func.count(UsageLog.id).label("reqs"),
            ).where(
                UsageLog.project_id == project.id,
                UsageLog.created_at >= from_date,
                UsageLog.created_at < to_date,
            )
        )
        row = agg.one()
        spend = Decimal(str(row.spend))
        reqs = int(row.reqs)

        # Teams count
        team_count_result = await db.execute(
            select(func.count(Team.id)).where(Team.project_id == project.id)
        )
        teams_count = int(team_count_result.scalar_one() or 0)

        # Members count (service keys with this project assigned)
        members_result = await db.execute(
            select(func.count(func.distinct(ServiceAPIKey.owner_user_id))).where(
                ServiceAPIKey.project_id == project.id,
                ServiceAPIKey.owner_user_id.isnot(None),
            )
        )
        members_count = int(members_result.scalar_one() or 0)

        # Budget utilization
        budget = project.budget_limit
        budget_used_pct: Optional[float] = None
        if budget and budget > 0:
            budget_used_pct = round(float(spend / budget * 100), 2)

        items.append(
            ProjectAnalyticsItem(
                id=str(project.id),
                name=project.name,
                spend_30d=str(spend),
                requests_30d=reqs,
                teams_count=teams_count,
                members_count=members_count,
                budget=str(budget) if budget is not None else None,
                budget_used_pct=budget_used_pct,
            )
        )

    return items


@router.get("/projects/{project_id}/teams", response_model=list[TeamAnalyticsItem])
async def analytics_project_teams(
    project_id: uuid.UUID,
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
) -> list[TeamAnalyticsItem]:
    """Per-team spend and usage within a project."""
    from_date, to_date = _parse_range(range)

    # Verify project belongs to org
    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == user.organization_id,
        )
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    teams_result = await db.execute(
        select(Team).where(Team.project_id == project_id)
    )
    teams = list(teams_result.scalars().all())

    items: list[TeamAnalyticsItem] = []
    for team in teams:
        agg = await db.execute(
            select(
                func.coalesce(func.sum(UsageLog.cost_usd), 0).label("spend"),
                func.count(UsageLog.id).label("reqs"),
            ).where(
                UsageLog.team_id == team.id,
                UsageLog.created_at >= from_date,
                UsageLog.created_at < to_date,
            )
        )
        row = agg.one()

        members_result = await db.execute(
            select(func.count(func.distinct(ServiceAPIKey.owner_user_id))).where(
                ServiceAPIKey.team_id == team.id,
                ServiceAPIKey.owner_user_id.isnot(None),
            )
        )
        members_count = int(members_result.scalar_one() or 0)

        items.append(
            TeamAnalyticsItem(
                id=str(team.id),
                name=team.name,
                spend=str(Decimal(str(row.spend))),
                requests=int(row.reqs),
                members_count=members_count,
            )
        )

    return items


@router.get("/projects/{project_id}/developers", response_model=list[DeveloperAnalyticsItem])
async def analytics_project_developers(
    project_id: uuid.UUID,
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
) -> list[DeveloperAnalyticsItem]:
    """Per-developer spend and usage within a project."""
    from_date, to_date = _parse_range(range)

    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == user.organization_id,
        )
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Aggregate spend/requests/tokens per user within the project
    agg_result = await db.execute(
        select(
            UsageLog.user_id,
            func.sum(UsageLog.cost_usd).label("spend"),
            func.count(UsageLog.id).label("reqs"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("tokens"),
            func.max(UsageLog.created_at).label("last_active"),
        )
        .where(
            UsageLog.project_id == project_id,
            UsageLog.created_at >= from_date,
            UsageLog.created_at < to_date,
            UsageLog.user_id.isnot(None),
        )
        .group_by(UsageLog.user_id)
    )
    rows = agg_result.all()

    items: list[DeveloperAnalyticsItem] = []
    for row in rows:
        dev_user = await db.get(User, row.user_id)
        if dev_user is None:
            continue
        items.append(
            DeveloperAnalyticsItem(
                user_id=str(dev_user.id),
                name=dev_user.name,
                email=dev_user.email,
                spend_30d=str(Decimal(str(row.spend))),
                requests_30d=int(row.reqs),
                tokens_30d=int(row.tokens or 0),
                last_active=row.last_active,
            )
        )

    return items


@router.get("/spend/timeseries", response_model=TimeseriesResponse)
async def analytics_spend_timeseries(
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
    project_id: Optional[uuid.UUID] = Query(None),
) -> TimeseriesResponse:
    """Daily spend and request timeseries. Optionally filter by project."""
    from_date, to_date = _parse_range(range)

    conditions = [
        UsageLog.organization_id == user.organization_id,
        UsageLog.created_at >= from_date,
        UsageLog.created_at < to_date,
    ]
    if project_id is not None:
        conditions.append(UsageLog.project_id == project_id)

    result = await db.execute(
        select(
            func.date_trunc("day", UsageLog.created_at).label("day"),
            func.sum(UsageLog.cost_usd).label("spend"),
            func.count(UsageLog.id).label("reqs"),
        )
        .where(*conditions)
        .group_by(text("day"))
        .order_by(text("day"))
    )
    rows = result.all()

    series = [
        TimeseriesPoint(
            date=row.day.strftime("%Y-%m-%d"),
            spend=str(Decimal(str(row.spend))),
            requests=int(row.reqs),
        )
        for row in rows
    ]

    return TimeseriesResponse(series=series)


@router.get("/models/usage", response_model=list[ModelUsageItem])
async def analytics_models_usage(
    db: DB,
    user: AnalyticsUser,
    range: str = Query("30d"),
) -> list[ModelUsageItem]:
    """Per-model spend, requests, tokens, and percentage of total."""
    from_date, to_date = _parse_range(range)

    from app.models.provider import LLMModel

    result = await db.execute(
        select(
            LLMModel.name.label("model_name"),
            func.sum(UsageLog.cost_usd).label("spend"),
            func.count(UsageLog.id).label("reqs"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("tokens"),
        )
        .join(LLMModel, UsageLog.model_id == LLMModel.id)
        .where(
            UsageLog.organization_id == user.organization_id,
            UsageLog.created_at >= from_date,
            UsageLog.created_at < to_date,
        )
        .group_by(LLMModel.name)
        .order_by(func.sum(UsageLog.cost_usd).desc())
    )
    rows = result.all()

    total_spend = sum(Decimal(str(r.spend)) for r in rows)

    items: list[ModelUsageItem] = []
    for row in rows:
        spend = Decimal(str(row.spend))
        pct = float(spend / total_spend * 100) if total_spend > 0 else 0.0
        items.append(
            ModelUsageItem(
                model_name=row.model_name,
                spend=str(spend),
                requests=int(row.reqs),
                tokens=int(row.tokens or 0),
                pct_of_total=round(pct, 2),
            )
        )

    return items
