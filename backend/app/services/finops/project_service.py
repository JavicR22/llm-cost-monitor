import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.project_repo import (
    ProjectCreate,
    ProjectUpdate,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.schemas.project import ProjectCreate as ProjectCreateSchema
from app.schemas.project import ProjectResponse, ProjectUpdate as ProjectUpdateSchema

log = structlog.get_logger()


async def list_org_projects(db: AsyncSession, org_id: uuid.UUID) -> list[ProjectResponse]:
    projects = await list_projects(db, org_id)
    return [_to_response(p) for p in projects]


async def create_org_project(
    db: AsyncSession, org_id: uuid.UUID, data: ProjectCreateSchema
) -> ProjectResponse:
    project = await create_project(
        db,
        ProjectCreate(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            budget_limit=data.budget_limit,
        ),
    )
    log.info("project_created", org_id=str(org_id), project_id=str(project.id), name=project.name)
    return _to_response(project)


async def patch_project(
    db: AsyncSession, project_id: uuid.UUID, org_id: uuid.UUID, data: ProjectUpdateSchema
) -> ProjectResponse:
    project = await get_project(db, project_id, org_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    project = await update_project(
        db,
        project,
        ProjectUpdate(
            name=data.name,
            description=data.description,
            budget_limit=data.budget_limit,
        ),
    )
    return _to_response(project)


async def remove_project(
    db: AsyncSession, project_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    project = await get_project(db, project_id, org_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    await delete_project(db, project)
    log.info("project_deleted", org_id=str(org_id), project_id=str(project_id))


def _to_response(project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        budget_limit=project.budget_limit,
        created_at=project.created_at,
    )
