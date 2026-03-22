from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)
    org_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    personal_key: str | None = None  # shown once on first login for admin users


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    org_id: str
    last_login_at: str | None = None
    assigned_project_id: Optional[uuid.UUID] = None
    assigned_team_id: Optional[uuid.UUID] = None
    has_seen_key_modal: bool = False

    model_config = {"from_attributes": True}


class MemberInvite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(default="viewer")  # "admin" | "viewer"


class MemberRoleUpdate(BaseModel):
    role: str  # "admin" | "viewer"
