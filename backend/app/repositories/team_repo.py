import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team


@dataclass(slots=True)
class TeamCreate:
    project_id: uuid.UUID
    name: str
    budget_limit: Optional[Decimal] = None


@dataclass(slots=True)
class TeamUpdate:
    name: Optional[str] = None
    budget_limit: Optional[Decimal] = None


async def list_teams(db: AsyncSession, project_id: uuid.UUID) -> list[Team]:
    result = await db.execute(
        select(Team)
        .where(Team.project_id == project_id)
        .order_by(Team.created_at.desc())
    )
    return list(result.scalars().all())


async def get_team(
    db: AsyncSession, team_id: uuid.UUID, project_id: uuid.UUID
) -> Optional[Team]:
    return await db.scalar(
        select(Team).where(
            Team.id == team_id,
            Team.project_id == project_id,
        )
    )


async def get_team_by_id(db: AsyncSession, team_id: uuid.UUID) -> Optional[Team]:
    return await db.scalar(select(Team).where(Team.id == team_id))


async def create_team(db: AsyncSession, data: TeamCreate) -> Team:
    team = Team(
        project_id=data.project_id,
        name=data.name,
        budget_limit=data.budget_limit,
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def update_team(db: AsyncSession, team: Team, data: TeamUpdate) -> Team:
    if data.name is not None:
        team.name = data.name
    if data.budget_limit is not None:
        team.budget_limit = data.budget_limit
    await db.commit()
    await db.refresh(team)
    return team


async def delete_team(db: AsyncSession, team: Team) -> None:
    await db.delete(team)
    await db.commit()
