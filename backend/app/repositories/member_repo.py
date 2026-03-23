import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def list_org_members(db: AsyncSession, org_id: uuid.UUID) -> list[User]:
    result = await db.execute(
        select(User)
        .where(User.organization_id == org_id)
        .order_by(User.name)
    )
    return list(result.scalars().all())


async def create_member(
    db: AsyncSession,
    org_id: uuid.UUID,
    name: str,
    email: str,
    password_hash: str,
    role: str,
) -> User:
    member = User(
        organization_id=org_id,
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def get_member(
    db: AsyncSession, member_id: uuid.UUID, org_id: uuid.UUID
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == member_id, User.organization_id == org_id)
    )
    return result.scalar_one_or_none()


async def update_member_role(
    db: AsyncSession, member_id: uuid.UUID, org_id: uuid.UUID, new_role: str
) -> User | None:
    member = await get_member(db, member_id, org_id)
    if member is None:
        return None
    member.role = new_role
    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(
    db: AsyncSession, member_id: uuid.UUID, org_id: uuid.UUID
) -> bool:
    member = await get_member(db, member_id, org_id)
    if member is None:
        return False
    await db.delete(member)
    await db.commit()
    return True
