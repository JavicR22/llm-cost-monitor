"""Pydantic schemas for notification channels."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


ChannelType = Literal["email"]  # slack / sms in Phase 2


class NotificationChannelCreate(BaseModel):
    type: ChannelType = "email"
    email: EmailStr


class NotificationChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    display_hint: str       # masked e.g. "u***@example.com"
    is_active: bool
    created_at: datetime
