from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_spend_usd: Decimal
    request_count: int
    avg_cost_per_request: Decimal
    total_tokens: int
    # Change vs previous period (same duration)
    spend_change_pct: Optional[float]    # None when no previous data
    request_change_pct: Optional[float]


class DailySpend(BaseModel):
    date: date
    spend_usd: Decimal
    request_count: int


class SpendByModel(BaseModel):
    model_name: str
    display_name: str
    spend_usd: Decimal
    request_count: int
    total_tokens: int
    pct_of_total: float    # 0–100


class ActivityRow(BaseModel):
    id: str
    model_name: str
    display_name: str
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal
    latency_ms: int
    is_streaming: bool
    created_at: datetime


class ActivityResponse(BaseModel):
    items: list[ActivityRow]
    total: int
    page: int
    page_size: int
