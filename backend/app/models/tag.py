import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Tag(UUIDMixin, TimestampMixin, Base):
    """Cost tagging by feature/department/environment. Applied to usage_logs via JSONB tags array."""

    __tablename__ = "tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "feature:chatbot", "dept:engineering"
    color: Mapped[Optional[str]] = mapped_column(String(7))  # hex color e.g. #3B82F6

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="tags")
