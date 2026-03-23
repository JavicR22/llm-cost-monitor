import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from app.core.dependencies import DB, CurrentUser
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from app.services.finops import project_service, team_service
from app.services.security import audit_service

router = APIRouter(prefix="/projects", tags=["finops-projects"])


# ------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: CurrentUser, db: DB) -> list[ProjectResponse]:
    """List all projects for the current organization."""
    return await project_service.list_org_projects(db, user.organization_id)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> ProjectResponse:
    """Create a new project. Requires owner or admin."""
    _require_owner_or_admin(user)
    project = await project_service.create_org_project(db, user.organization_id, data)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="project_created",
        entity_type="project",
        entity_id=uuid.UUID(project.id),
        details={"name": project.name},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    user: CurrentUser,
    db: DB,
) -> ProjectResponse:
    """Update project name, description, or budget. Requires owner or admin."""
    _require_owner_or_admin(user)
    return await project_service.patch_project(db, project_id, user.organization_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    db: DB,
) -> None:
    """Delete a project and its teams. Requires owner or admin."""
    _require_owner_or_admin(user)
    await project_service.remove_project(db, project_id, user.organization_id)
    background_tasks.add_task(
        audit_service.log,
        org_id=user.organization_id,
        user_id=user.id,
        action="project_deleted",
        entity_type="project",
        entity_id=project_id,
        details={},
        ip=request.client.host if request.client else None,
        ua=request.headers.get("User-Agent"),
    )


# ------------------------------------------------------------------
# Teams — nested under /projects/{project_id}/teams
# ------------------------------------------------------------------


@router.get("/{project_id}/teams", response_model=list[TeamResponse])
async def list_teams(
    project_id: uuid.UUID, user: CurrentUser, db: DB
) -> list[TeamResponse]:
    """List all teams within a project."""
    return await team_service.list_project_teams(db, project_id, user.organization_id)


@router.post("/{project_id}/teams", response_model=TeamResponse, status_code=201)
async def create_team(
    project_id: uuid.UUID,
    data: TeamCreate,
    user: CurrentUser,
    db: DB,
) -> TeamResponse:
    """Create a team inside a project. Requires owner or admin."""
    _require_owner_or_admin(user)
    return await team_service.create_project_team(db, project_id, user.organization_id, data)


@router.patch("/{project_id}/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    project_id: uuid.UUID,
    team_id: uuid.UUID,
    data: TeamUpdate,
    user: CurrentUser,
    db: DB,
) -> TeamResponse:
    """Update a team. Requires owner or admin."""
    _require_owner_or_admin(user)
    return await team_service.patch_team(db, team_id, project_id, user.organization_id, data)


@router.delete("/{project_id}/teams/{team_id}", status_code=204)
async def delete_team(
    project_id: uuid.UUID,
    team_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
) -> None:
    """Delete a team. Requires owner or admin."""
    _require_owner_or_admin(user)
    await team_service.remove_team(db, team_id, project_id, user.organization_id)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _require_owner_or_admin(user) -> None:
    from fastapi import HTTPException, status as http_status
    if user.role not in ("owner", "admin"):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, "Owner or admin role required")
