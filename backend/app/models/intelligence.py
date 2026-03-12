import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

QualitySource = Enum("public_benchmark", "shadow_test", "client_feedback", name="quality_source")
BenchmarkRecommendation = Enum("best_value", "premium", "economy", "overkill", name="benchmark_recommendation")
SuggestionStatus = Enum("pending", "accepted", "rejected", "dismissed", name="suggestion_status")


class ModelBenchmark(UUIDMixin, Base):
    __tablename__ = "model_benchmarks"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(
        Enum("code", "vision", "chat", "summary", "classification", "rag", name="task_type", create_type=False),
        nullable=False,
    )
    quality_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)  # 0.000 – 1.000
    quality_source: Mapped[str] = mapped_column(QualitySource, nullable=False)
    avg_latency_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    recommendation: Mapped[str] = mapped_column(BenchmarkRecommendation, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    model: Mapped["LLMModel"] = relationship(back_populates="benchmarks")


class OptimizationSuggestion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "optimization_suggestions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    current_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False
    )
    suggested_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(
        Enum("code", "vision", "chat", "summary", "classification", "rag", name="task_type", create_type=False),
        nullable=False,
    )

    affected_requests_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_monthly_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    projected_monthly_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    estimated_savings: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    quality_current: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    quality_suggested: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)

    status: Mapped[str] = mapped_column(SuggestionStatus, nullable=False, server_default="pending")
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="optimization_suggestions")
    current_model: Mapped["LLMModel"] = relationship(
        back_populates="suggestions_as_current", foreign_keys=[current_model_id]
    )
    suggested_model: Mapped["LLMModel"] = relationship(
        back_populates="suggestions_as_suggested", foreign_keys=[suggested_model_id]
    )


class ShadowTestResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "shadow_test_results"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    original_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False
    )
    test_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(
        Enum("code", "vision", "chat", "summary", "classification", "rag", name="task_type", create_type=False),
        nullable=False,
    )

    similarity_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)  # cosine similarity
    cost_original: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    cost_test: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    latency_original_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_test_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="shadow_test_results")
    original_model: Mapped["LLMModel"] = relationship(
        back_populates="shadow_tests_as_original", foreign_keys=[original_model_id]
    )
    test_model: Mapped["LLMModel"] = relationship(
        back_populates="shadow_tests_as_test", foreign_keys=[test_model_id]
    )
