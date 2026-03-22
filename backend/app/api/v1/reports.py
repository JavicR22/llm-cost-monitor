import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.repositories.finops_report_repo import GroupBy
from app.services.finops import report_service

router = APIRouter(prefix="/reports", tags=["finops-reports"])


@router.get("/projects", response_model=list[dict])
async def projects_spend(
    user: CurrentUser,
    db: DB,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    group_by: GroupBy = Query("day"),
) -> Any:
    """Cost totals grouped by project and date bucket."""
    return await report_service.get_projects_spend(
        db, user.organization_id, from_date, to_date, group_by
    )


@router.get("/projects/{project_id}/teams", response_model=list[dict])
async def teams_spend(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    group_by: GroupBy = Query("day"),
) -> Any:
    """Cost totals grouped by team within a project."""
    return await report_service.get_teams_spend(
        db, user.organization_id, project_id, from_date, to_date, group_by
    )


@router.get("/projects/{project_id}/members", response_model=list[dict])
async def members_spend(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    group_by: GroupBy = Query("day"),
) -> Any:
    """Cost totals grouped by developer within a project."""
    return await report_service.get_members_spend(
        db, user.organization_id, project_id, from_date, to_date, group_by
    )


@router.get("/summary", response_model=list[dict])
async def summary(
    user: CurrentUser,
    db: DB,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> Any:
    """Global summary: all projects with totals vs budget_limit."""
    return await report_service.get_summary(
        db, user.organization_id, from_date, to_date
    )
