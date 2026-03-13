"""
Model repository — pricing lookups for the metering hot path.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import LLMModel


async def get_model_by_name(db: AsyncSession, model_name: str) -> Optional[LLMModel]:
    """Return a model by its API name (e.g. 'gpt-4o'). None if not in catalog."""
    result = await db.execute(
        select(LLMModel).where(
            LLMModel.name == model_name,
            LLMModel.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()
