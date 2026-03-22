import uuid
from datetime import date

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.finops_report_repo import (
    GroupBy,
    spend_by_member,
    spend_by_project,
    spend_by_team,
    spend_summary,
)
from app.repositories.project_repo import get_project

log = structlog.get_logger()


async def get_projects_spend(
    db: AsyncSession,
    org_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy,
) -> list[dict]:
    return await spend_by_project(db, org_id, from_date, to_date, group_by)


async def get_teams_spend(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy,
) -> list[dict]:
    project = await get_project(db, project_id, org_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return await spend_by_team(db, org_id, project_id, from_date, to_date, group_by)


async def get_members_spend(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy,
) -> list[dict]:
    project = await get_project(db, project_id, org_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return await spend_by_member(db, org_id, project_id, from_date, to_date, group_by)


async def get_summary(
    db: AsyncSession,
    org_id: uuid.UUID,
    from_date: date,
    to_date: date,
) -> list[dict]:
    return await spend_summary(db, org_id, from_date, to_date)
