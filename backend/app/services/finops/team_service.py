import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.project_repo import get_project
from app.repositories.team_repo import (
    TeamCreate,
    TeamUpdate,
    create_team,
    delete_team,
    get_team,
    list_teams,
    update_team,
)
from app.schemas.team import TeamCreate as TeamCreateSchema
from app.schemas.team import TeamResponse, TeamUpdate as TeamUpdateSchema

log = structlog.get_logger()


async def list_project_teams(
    db: AsyncSession, project_id: uuid.UUID, org_id: uuid.UUID
) -> list[TeamResponse]:
    await _assert_project_belongs_to_org(db, project_id, org_id)
    teams = await list_teams(db, project_id)
    return [_to_response(t) for t in teams]


async def create_project_team(
    db: AsyncSession,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
    data: TeamCreateSchema,
) -> TeamResponse:
    await _assert_project_belongs_to_org(db, project_id, org_id)
    team = await create_team(
        db,
        TeamCreate(
            project_id=project_id,
            name=data.name,
            budget_limit=data.budget_limit,
        ),
    )
    log.info("team_created", project_id=str(project_id), team_id=str(team.id), name=team.name)
    return _to_response(team)


async def patch_team(
    db: AsyncSession,
    team_id: uuid.UUID,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
    data: TeamUpdateSchema,
) -> TeamResponse:
    await _assert_project_belongs_to_org(db, project_id, org_id)
    team = await get_team(db, team_id, project_id)
    if not team:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    team = await update_team(db, team, TeamUpdate(name=data.name, budget_limit=data.budget_limit))
    return _to_response(team)


async def remove_team(
    db: AsyncSession, team_id: uuid.UUID, project_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    await _assert_project_belongs_to_org(db, project_id, org_id)
    team = await get_team(db, team_id, project_id)
    if not team:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    await delete_team(db, team)
    log.info("team_deleted", project_id=str(project_id), team_id=str(team_id))


async def _assert_project_belongs_to_org(
    db: AsyncSession, project_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    project = await get_project(db, project_id, org_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")


def _to_response(team) -> TeamResponse:
    return TeamResponse(
        id=str(team.id),
        project_id=str(team.project_id),
        name=team.name,
        budget_limit=team.budget_limit,
        created_at=team.created_at,
    )
