from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class ServiceKeyCreate(BaseModel):
    label: Optional[str] = Field(None, max_length=100, examples=["Production app"])
    project_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    owner_user_id: Optional[uuid.UUID] = None


class ServiceKeyAssign(BaseModel):
    """Assign or reassign a service key to a FinOps attribution layer."""
    project_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    owner_user_id: Optional[uuid.UUID] = None


class ServiceKeyResponse(BaseModel):
    id: str
    label: Optional[str]
    key_prefix: str        # lcm_sk_live_...***abcd — safe to display
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    project_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    owner_user_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


class ServiceKeyCreateResponse(ServiceKeyResponse):
    """Returned only at creation — includes the raw key shown exactly once."""
    raw_key: str
