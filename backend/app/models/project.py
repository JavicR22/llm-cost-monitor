import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Project(UUIDMixin, TimestampMixin, Base):
    """
    FinOps cost attribution layer 1.
    Groups service keys (and their usage) under a named project with optional budget.
    """

    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    teams: Mapped[list["Team"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    service_api_keys: Mapped[list["ServiceAPIKey"]] = relationship(back_populates="project")
