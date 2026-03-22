import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Team(UUIDMixin, TimestampMixin, Base):
    """
    FinOps cost attribution layer 2.
    Optional sub-group within a Project (e.g. Frontend, Backend, AI-ML).
    """

    __tablename__ = "teams"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="teams")
    service_api_keys: Mapped[list["ServiceAPIKey"]] = relationship(back_populates="team")
