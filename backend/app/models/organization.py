import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

PlanType = Enum("free", "starter", "pro", "enterprise", name="plan_type")


class Organization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(PlanType, nullable=False, server_default="free")

    monthly_budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    daily_budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    circuit_breaker_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    circuit_breaker_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    circuit_breaker_window_minutes: Mapped[Optional[int]]

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    service_api_keys: Mapped[list["ServiceAPIKey"]] = relationship(back_populates="organization")
    provider_api_keys: Mapped[list["ProviderAPIKey"]] = relationship(back_populates="organization")
    usage_logs: Mapped[list["UsageLog"]] = relationship(back_populates="organization")
    alert_rules: Mapped[list["AlertRule"]] = relationship(back_populates="organization")
    alert_events: Mapped[list["AlertEvent"]] = relationship(back_populates="organization")
    notification_channels: Mapped[list["NotificationChannel"]] = relationship(back_populates="organization")
    optimization_suggestions: Mapped[list["OptimizationSuggestion"]] = relationship(back_populates="organization")
    shadow_test_results: Mapped[list["ShadowTestResult"]] = relationship(back_populates="organization")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="organization")
    tags: Mapped[list["Tag"]] = relationship(back_populates="organization")
    projects: Mapped[list["Project"]] = relationship(back_populates="organization")
