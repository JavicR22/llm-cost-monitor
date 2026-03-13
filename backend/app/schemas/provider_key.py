from datetime import datetime
from typing import Optional
from typing import Literal

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "anthropic", "google", "mistral"]


class ProviderKeyCreate(BaseModel):
    provider: ProviderName
    raw_key: str = Field(min_length=10, description="Provider API key — stored encrypted, never returned")
    label: Optional[str] = Field(None, max_length=100)


class ProviderKeyResponse(BaseModel):
    id: str
    provider: str
    key_prefix: str        # sk-...***xyz — safe to display
    label: Optional[str]
    is_active: bool
    created_at: datetime
    last_validated_at: Optional[datetime]

    model_config = {"from_attributes": True}
