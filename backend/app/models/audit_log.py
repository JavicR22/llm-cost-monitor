import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import Base, UUIDMixin

AuditAction = Enum(
    "key_created",
    "key_revoked",
    "login",
    "login_failed",
    "logout",
    "budget_changed",
    "circuit_breaker_triggered",
    "circuit_breaker_released",
    "member_invited",
    name="audit_action",
)


class AuditLog(UUIDMixin, Base):
    """Immutable append-only log. No ondelete cascade — audit trails must be preserved."""

    __tablename__ = "audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    action: Mapped[str] = mapped_column(AuditAction, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    details: Mapped[Optional[dict]] = mapped_column(JSONB)  # {"before": {...}, "after": {...}}
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="audit_logs")
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
