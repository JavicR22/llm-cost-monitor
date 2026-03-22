"""
FinOps report repository — read-only aggregation queries.
All queries group by the requested dimension and date bucket.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ServiceAPIKey
from app.models.usage_log import UsageLog
from app.models.project import Project
from app.models.team import Team
from app.models.user import User

GroupBy = Literal["day", "week", "month"]

_TRUNC = {
    "day": "day",
    "week": "week",
    "month": "month",
}


async def spend_by_project(
    db: AsyncSession,
    org_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy = "day",
) -> list[dict]:
    """Total cost grouped by project and date bucket."""
    trunc = _TRUNC[group_by]
    result = await db.execute(
        select(
            UsageLog.project_id,
            Project.name.label("project_name"),
            func.date_trunc(trunc, UsageLog.created_at).label("period"),
            func.sum(UsageLog.cost_usd).label("total_cost"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("total_tokens"),
            func.count(UsageLog.id).label("requests"),
        )
        .join(Project, Project.id == UsageLog.project_id, isouter=True)
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.project_id.is_not(None),
            func.date(UsageLog.created_at) >= from_date,
            func.date(UsageLog.created_at) <= to_date,
        )
        .group_by(UsageLog.project_id, Project.name, text("period"))
        .order_by(text("period"), Project.name)
    )
    return [
        {
            "project_id": str(row.project_id),
            "project_name": row.project_name,
            "period": row.period.date().isoformat() if row.period else None,
            "total_cost": Decimal(row.total_cost),
            "total_tokens": row.total_tokens,
            "requests": row.requests,
        }
        for row in result
    ]


async def spend_by_team(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy = "day",
) -> list[dict]:
    """Total cost grouped by team within a project."""
    trunc = _TRUNC[group_by]
    result = await db.execute(
        select(
            UsageLog.team_id,
            Team.name.label("team_name"),
            func.date_trunc(trunc, UsageLog.created_at).label("period"),
            func.sum(UsageLog.cost_usd).label("total_cost"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("total_tokens"),
            func.count(UsageLog.id).label("requests"),
        )
        .join(Team, Team.id == UsageLog.team_id, isouter=True)
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.project_id == project_id,
            UsageLog.team_id.is_not(None),
            func.date(UsageLog.created_at) >= from_date,
            func.date(UsageLog.created_at) <= to_date,
        )
        .group_by(UsageLog.team_id, Team.name, text("period"))
        .order_by(text("period"), Team.name)
    )
    return [
        {
            "team_id": str(row.team_id),
            "team_name": row.team_name,
            "period": row.period.date().isoformat() if row.period else None,
            "total_cost": Decimal(row.total_cost),
            "total_tokens": row.total_tokens,
            "requests": row.requests,
        }
        for row in result
    ]


async def spend_by_member(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    from_date: date,
    to_date: date,
    group_by: GroupBy = "day",
) -> list[dict]:
    """Developers attributed to this project via service keys, with usage totals.

    Includes developers who have an attributed key but zero usage — they show
    with total_cost=0 so they always appear in the Developers tab.
    """
    # 1. All users with a service key attributed to this project
    keys_result = await db.execute(
        select(ServiceAPIKey.owner_user_id)
        .where(
            ServiceAPIKey.organization_id == org_id,
            ServiceAPIKey.project_id == project_id,
            ServiceAPIKey.owner_user_id.is_not(None),
        )
        .distinct()
    )
    attributed_ids: set[uuid.UUID] = {row[0] for row in keys_result}

    # 2. Usage aggregation per user in the date range
    usage_result = await db.execute(
        select(
            UsageLog.user_id,
            func.sum(UsageLog.cost_usd).label("total_cost"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("total_tokens"),
            func.count(UsageLog.id).label("requests"),
        )
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.project_id == project_id,
            UsageLog.user_id.is_not(None),
            func.date(UsageLog.created_at) >= from_date,
            func.date(UsageLog.created_at) <= to_date,
        )
        .group_by(UsageLog.user_id)
    )
    usage_by_user = {row.user_id: row for row in usage_result}

    # 3. Union: attributed developers + anyone who has usage (e.g. key reassigned)
    all_ids = attributed_ids | set(usage_by_user.keys())
    if not all_ids:
        return []

    # 4. Fetch user details in one query
    users_result = await db.execute(select(User).where(User.id.in_(all_ids)))
    users: dict[uuid.UUID, User] = {u.id: u for u in users_result.scalars()}

    rows = []
    for user_id in all_ids:
        user = users.get(user_id)
        if not user:
            continue
        usage = usage_by_user.get(user_id)
        rows.append(
            {
                "user_id": str(user_id),
                "user_name": user.name,
                "user_email": user.email,
                "period": None,
                "total_cost": Decimal(str(usage.total_cost)) if usage else Decimal("0"),
                "total_tokens": int(usage.total_tokens or 0) if usage else 0,
                "requests": int(usage.requests) if usage else 0,
            }
        )

    rows.sort(key=lambda r: (r["user_name"] or "").lower())
    return rows


async def spend_summary(
    db: AsyncSession,
    org_id: uuid.UUID,
    from_date: date,
    to_date: date,
) -> list[dict]:
    """Flat summary: org → projects (with totals). No date bucketing."""
    result = await db.execute(
        select(
            UsageLog.project_id,
            Project.name.label("project_name"),
            Project.budget_limit.label("budget_limit"),
            func.sum(UsageLog.cost_usd).label("total_cost"),
            func.sum(UsageLog.tokens_input + UsageLog.tokens_output).label("total_tokens"),
            func.count(UsageLog.id).label("requests"),
        )
        .join(Project, Project.id == UsageLog.project_id, isouter=True)
        .where(
            UsageLog.organization_id == org_id,
            UsageLog.project_id.is_not(None),
            func.date(UsageLog.created_at) >= from_date,
            func.date(UsageLog.created_at) <= to_date,
        )
        .group_by(UsageLog.project_id, Project.name, Project.budget_limit)
        .order_by(func.sum(UsageLog.cost_usd).desc())
    )
    return [
        {
            "project_id": str(row.project_id),
            "project_name": row.project_name,
            "budget_limit": Decimal(row.budget_limit) if row.budget_limit else None,
            "total_cost": Decimal(row.total_cost),
            "total_tokens": row.total_tokens,
            "requests": row.requests,
        }
        for row in result
    ]
