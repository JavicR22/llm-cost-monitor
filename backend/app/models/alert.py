import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

AlertRuleType = Enum("budget_soft", "budget_hard", "anomaly", "circuit_breaker", name="alert_rule_type")
AlertScope = Enum("hourly", "daily", "monthly", name="alert_scope")
AlertSeverity = Enum("info", "warning", "critical", name="alert_severity")
AlertEventType = Enum("soft_limit", "hard_limit", "anomaly", "circuit_breaker", name="alert_event_type")
NotificationChannelType = Enum("slack", "email", "sms", name="notification_channel_type")


class AlertRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alert_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(AlertRuleType, nullable=False)
    scope: Mapped[str] = mapped_column(AlertScope, nullable=False)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    anomaly_multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # e.g. 3.0 = 3× average
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="alert_rules")
    events: Mapped[list["AlertEvent"]] = relationship(back_populates="alert_rule")


class AlertEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alert_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    alert_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id")
    )
    severity: Mapped[str] = mapped_column(AlertSeverity, nullable=False)
    type: Mapped[str] = mapped_column(AlertEventType, nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)

    triggered_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_channels: Mapped[Optional[list]] = mapped_column(JSONB)  # ["slack", "email"]

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="alert_events")
    alert_rule: Mapped[Optional["AlertRule"]] = relationship(back_populates="events")


class NotificationChannel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notification_channels"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(NotificationChannelType, nullable=False)
    config_encrypted: Mapped[str] = mapped_column(String(2000), nullable=False)  # Fernet: webhook URL, email, phone
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="notification_channels")
