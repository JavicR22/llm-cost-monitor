from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ServiceKeyCreate(BaseModel):
    label: Optional[str] = Field(None, max_length=100, examples=["Production app"])


class ServiceKeyResponse(BaseModel):
    id: str
    label: Optional[str]
    key_prefix: str        # lcm_sk_live_...***abcd — safe to display
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ServiceKeyCreateResponse(ServiceKeyResponse):
    """Returned only at creation — includes the raw key shown exactly once."""
    raw_key: str
