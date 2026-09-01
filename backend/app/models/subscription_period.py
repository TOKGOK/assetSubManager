from pydantic import BaseModel, Field
from typing import Literal


class SubscriptionPeriod(BaseModel):
    id: int
    name: str
    rule_type: Literal["daily_interval", "monthly_day", "yearly_date", "custom"]
    interval_days: int = 0
    interval_hours: int = 0
    month_day: int = 0
    month: int = 0
    day: int = 0
    is_default: bool = False
    created_at: str = ""
    updated_at: str = ""


class CreateSubscriptionPeriodRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    rule_type: Literal["daily_interval", "monthly_day", "yearly_date", "custom"]
    interval_days: int = Field(default=0, ge=0)
    interval_hours: int = Field(default=0, ge=0)
    month_day: int = Field(default=0, ge=0, le=31)
    month: int = Field(default=0, ge=0, le=12)
    day: int = Field(default=0, ge=0, le=31)


class UpdateSubscriptionPeriodRequest(BaseModel):
    name: str | None = None
    rule_type: Literal["daily_interval", "monthly_day", "yearly_date", "custom"] | None = None
    interval_days: int | None = Field(default=None, ge=0)
    interval_hours: int | None = Field(default=None, ge=0)
    month_day: int | None = Field(default=None, ge=0, le=31)
    month: int | None = Field(default=None, ge=0, le=12)
    day: int | None = Field(default=None, ge=0, le=31)
