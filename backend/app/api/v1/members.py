"""
Members endpoint — CRUD for users in the current organization.
"""
import uuid

import structlog
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DB, CurrentUser
from app.core.security import hash_password
from app.repositories.member_repo import (
    create_member,
    delete_member,
    get_member,
    list_org_members,
    update_member_role,
)
from app.schemas.auth import MemberInvite, MemberRoleUpdate, UserResponse

log = structlog.get_logger()

router = APIRouter(prefix="/members", tags=["members"])

ROLE_RANK = {"viewer": 0, "admin": 1, "owner": 2}


def _to_response(m) -> UserResponse:
    return UserResponse(
        id=str(m.id),
        email=m.email,
        name=m.name,
        role=m.role,
        org_id=str(m.organization_id),
        last_login_at=m.last_login_at.isoformat() if m.last_login_at else None,
        assigned_project_id=m.assigned_project_id,
        assigned_team_id=m.assigned_team_id,
        has_seen_key_modal=m.has_seen_key_modal,
    )


@router.get("", response_model=list[UserResponse])
async def list_members(user: CurrentUser, db: DB) -> list[UserResponse]:
    """List all members of the current organization."""
    members = await list_org_members(db, user.organization_id)
    return [_to_response(m) for m in members]


@router.post("/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(body: MemberInvite, user: CurrentUser, db: DB) -> UserResponse:
    """Invite a new member to the organization. Requires owner or admin role."""
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can invite members.",
        )

    # Caller cannot invite with a role higher than their own
    if ROLE_RANK.get(body.role, 0) > ROLE_RANK.get(user.role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign a role higher than your own.",
        )

    # Only owner or admin roles are valid for invitation (not owner directly)
    if body.role not in ("admin", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be 'admin' or 'viewer'.",
        )

    pw_hash = hash_password(body.password)
    try:
        member = await create_member(
            db,
            org_id=user.organization_id,
            name=body.name,
            email=body.email,
            password_hash=pw_hash,
            role=body.role,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    log.info("member.invited", inviter=str(user.id), new_member=str(member.id), role=body.role)
    return _to_response(member)


@router.patch("/{member_id}/role", response_model=UserResponse)
async def change_member_role(
    member_id: uuid.UUID, body: MemberRoleUpdate, user: CurrentUser, db: DB
) -> UserResponse:
    """Change a member's role. Only owners can do this."""
    if user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can change member roles.",
        )

    if user.id == member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    if body.role not in ("admin", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be 'admin' or 'viewer'.",
        )

    member = await update_member_role(db, member_id, user.organization_id, body.role)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    log.info("member.role_changed", changed_by=str(user.id), member=str(member_id), new_role=body.role)
    return _to_response(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(member_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Remove a member from the organization. Owner/admin only."""
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can remove members.",
        )

    if user.id == member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself.",
        )

    # Non-owners cannot delete owners
    target = await get_member(db, member_id, user.organization_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if target.role == "owner" and user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an owner can remove another owner.",
        )

    await delete_member(db, member_id, user.organization_id)
    log.info("member.removed", removed_by=str(user.id), member=str(member_id))
