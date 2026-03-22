from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    budget_limit: Optional[Decimal] = Field(None, gt=0)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    budget_limit: Optional[Decimal] = Field(None, gt=0)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    budget_limit: Optional[Decimal]
    created_at: datetime

    model_config = {"from_attributes": True}
