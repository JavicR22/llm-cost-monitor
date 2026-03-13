"""
Usage log repository — write path only (read path is in dashboard endpoints).
Called exclusively from background tasks — never blocks the response.
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_log import UsageLog


@dataclass(slots=True)
class UsageLogCreate:
    organization_id: uuid.UUID
    model_id: uuid.UUID
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal
    latency_ms: int
    is_streaming: bool
    service_api_key_id: Optional[uuid.UUID] = None
    provider_api_key_id: Optional[uuid.UUID] = None
    task_type: str = "chat"
    request_ip: Optional[str] = None
    user_agent: Optional[str] = None
    tags: Optional[list] = None


async def create_usage_log(db: AsyncSession, data: UsageLogCreate) -> UsageLog:
    """Insert a usage log row. Caller is responsible for commit."""
    row = UsageLog(
        organization_id=data.organization_id,
        model_id=data.model_id,
        tokens_input=data.tokens_input,
        tokens_output=data.tokens_output,
        cost_usd=data.cost_usd,
        latency_ms=data.latency_ms,
        is_streaming=data.is_streaming,
        service_api_key_id=data.service_api_key_id,
        provider_api_key_id=data.provider_api_key_id,
        task_type=data.task_type,
        request_ip=data.request_ip,
        user_agent=data.user_agent,
        tags=data.tags,
    )
    db.add(row)
    await db.commit()
    return row
