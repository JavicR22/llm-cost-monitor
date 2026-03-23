"""Pydantic schemas for alert rules and alert events."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

AlertRuleType = Literal["budget_soft", "budget_hard", "anomaly", "circuit_breaker"]
AlertScope = Literal["hourly", "daily", "monthly"]


class AlertRuleCreate(BaseModel):
    type: AlertRuleType
    scope: AlertScope
    threshold_value: Optional[Decimal] = None
    anomaly_multiplier: Optional[Decimal] = None
    is_active: bool = True

    @field_validator("threshold_value")
    @classmethod
    def threshold_required_for_budget(cls, v, info):
        rule_type = info.data.get("type")
        if rule_type in ("budget_soft", "budget_hard", "circuit_breaker") and v is None:
            raise ValueError(f"threshold_value is required for rule type '{rule_type}'")
        return v

    @field_validator("anomaly_multiplier")
    @classmethod
    def multiplier_required_for_anomaly(cls, v, info):
        rule_type = info.data.get("type")
        if rule_type == "anomaly" and v is None:
            raise ValueError("anomaly_multiplier is required for rule type 'anomaly'")
        return v


class AlertRuleUpdate(BaseModel):
    threshold_value: Optional[Decimal] = None
    anomaly_multiplier: Optional[Decimal] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    scope: str
    threshold_value: Optional[Decimal]
    anomaly_multiplier: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Alert Events
# ---------------------------------------------------------------------------

AlertSeverity = Literal["info", "warning", "critical"]
AlertEventType = Literal["soft_limit", "hard_limit", "anomaly", "circuit_breaker"]


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    alert_rule_id: Optional[uuid.UUID]
    severity: str
    type: str
    message: str
    triggered_value: Decimal
    threshold_value: Decimal
    notification_sent: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Circuit Breaker status
# ---------------------------------------------------------------------------

class CircuitBreakerStatus(BaseModel):
    is_open: bool
