import uuid
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


@dataclass(slots=True)
class ProjectCreate:
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    budget_limit: Optional[Decimal] = None


@dataclass(slots=True)
class ProjectUpdate:
    name: Optional[str] = None
    description: Optional[str] = None
    budget_limit: Optional[Decimal] = None


async def list_projects(db: AsyncSession, org_id: uuid.UUID) -> list[Project]:
    result = await db.execute(
        select(Project)
        .where(Project.organization_id == org_id)
        .order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project(
    db: AsyncSession, project_id: uuid.UUID, org_id: uuid.UUID
) -> Optional[Project]:
    return await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == org_id,
        )
    )


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(
        organization_id=data.organization_id,
        name=data.name,
        description=data.description,
        budget_limit=data.budget_limit,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(db: AsyncSession, project: Project, data: ProjectUpdate) -> Project:
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.budget_limit is not None:
        project.budget_limit = data.budget_limit
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()
