import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

ProviderName = Enum("openai", "anthropic", "google", "mistral", name="provider_name")


class ServiceAPIKey(UUIDMixin, TimestampMixin, Base):
    """Our service keys — clients use these to authenticate against our proxy."""

    __tablename__ = "service_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 hex
    key_prefix: Mapped[str] = mapped_column(String(50), nullable=False)  # lcm_...***abc
    label: Mapped[Optional[str]] = mapped_column(String(100))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="service_api_keys")
    usage_logs: Mapped[list["UsageLog"]] = relationship(back_populates="service_api_key")


class ProviderAPIKey(UUIDMixin, TimestampMixin, Base):
    """Client-owned provider keys (OpenAI/Anthropic/etc) — stored Fernet-encrypted."""

    __tablename__ = "provider_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(ProviderName, nullable=False)  # denormalized for fast lookups
    key_ciphertext: Mapped[str] = mapped_column(String(1000), nullable=False)  # Fernet ciphertext
    key_prefix: Mapped[str] = mapped_column(String(50), nullable=False)  # sk-...***xyz

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="provider_api_keys")
    provider_ref: Mapped["Provider"] = relationship(back_populates="provider_api_keys")
    usage_logs: Mapped[list["UsageLog"]] = relationship(back_populates="provider_api_key")
