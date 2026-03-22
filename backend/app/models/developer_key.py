import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class DeveloperAPIKey(UUIDMixin, TimestampMixin, Base):
    """
    Personal API key for a developer user.
    One key per developer (unique user_id constraint).
    SHA-256 hash stored only — raw key shown once at creation.
    Format: lcm_dev_{32 random hex bytes}
    """

    __tablename__ = "developer_api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one key per developer
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(String(50), nullable=False)  # lcm_dev_...***XYZ
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 hex

    label: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="developer_api_key")
