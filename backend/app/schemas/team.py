from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str = Field(..., max_length=255)
    budget_limit: Optional[Decimal] = Field(None, gt=0)


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    budget_limit: Optional[Decimal] = Field(None, gt=0)


class TeamResponse(BaseModel):
    id: str
    project_id: str
    name: str
    budget_limit: Optional[Decimal]
    created_at: datetime

    model_config = {"from_attributes": True}
