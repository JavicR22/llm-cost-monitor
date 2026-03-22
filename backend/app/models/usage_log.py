import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

TaskType = Enum("code", "vision", "chat", "summary", "classification", "rag", name="task_type")


class UsageLog(UUIDMixin, Base):
    """
    One row per proxied request. Partitioned by created_at at the DB level
    (see migration) to keep queries fast as the table grows.
    """

    __tablename__ = "usage_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    service_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_api_keys.id"), index=True
    )
    provider_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provider_api_keys.id"), index=True
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True
    )

    # FinOps attribution — denormalized from the service key at log time
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    task_type: Mapped[str] = mapped_column(TaskType, nullable=False, server_default="chat")
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    tags: Mapped[Optional[list]] = mapped_column(JSONB)  # ["feature:chatbot", "env:production"]
    request_ip: Mapped[Optional[str]] = mapped_column(String(45))  # supports IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    is_streaming: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="usage_logs")
    service_api_key: Mapped[Optional["ServiceAPIKey"]] = relationship(back_populates="usage_logs")
    provider_api_key: Mapped[Optional["ProviderAPIKey"]] = relationship(back_populates="usage_logs")
    model: Mapped["LLMModel"] = relationship(back_populates="usage_logs")
