import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

ModelCategory = Enum("flagship", "mid", "economy", name="model_category")


class Provider(UUIDMixin, Base):
    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    llm_models: Mapped[list["LLMModel"]] = relationship(back_populates="provider")
    provider_api_keys: Mapped[list["ProviderAPIKey"]] = relationship(back_populates="provider_ref")


class LLMModel(UUIDMixin, Base):
    """Catalog of LLM models with pricing. Named LLMModel to avoid conflict with SQLAlchemy's 'Model'."""

    __tablename__ = "models"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. gpt-4o
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    cost_per_1m_input_tokens: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    cost_per_1m_output_tokens: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)

    category: Mapped[str] = mapped_column(ModelCategory, nullable=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_code: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    pricing_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    provider: Mapped["Provider"] = relationship(back_populates="llm_models")
    usage_logs: Mapped[list["UsageLog"]] = relationship(back_populates="model")
    benchmarks: Mapped[list["ModelBenchmark"]] = relationship(back_populates="model")
    suggestions_as_current: Mapped[list["OptimizationSuggestion"]] = relationship(
        back_populates="current_model", foreign_keys="OptimizationSuggestion.current_model_id"
    )
    suggestions_as_suggested: Mapped[list["OptimizationSuggestion"]] = relationship(
        back_populates="suggested_model", foreign_keys="OptimizationSuggestion.suggested_model_id"
    )
    shadow_tests_as_original: Mapped[list["ShadowTestResult"]] = relationship(
        back_populates="original_model", foreign_keys="ShadowTestResult.original_model_id"
    )
    shadow_tests_as_test: Mapped[list["ShadowTestResult"]] = relationship(
        back_populates="test_model", foreign_keys="ShadowTestResult.test_model_id"
    )
