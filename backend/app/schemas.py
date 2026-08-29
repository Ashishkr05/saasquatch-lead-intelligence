from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ThesisBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industries: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    employee_min: int = Field(ge=1, le=100000)
    employee_max: int = Field(ge=1, le=100000)
    minimum_years: int = Field(ge=0, le=200)
    excluded_keywords: list[str] = Field(default_factory=list)
    exclude_institutionally_backed: bool = True


class ThesisRead(ThesisBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: datetime


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    domain: str | None
    website: str | None
    industry: str | None
    location: str | None
    employee_count: int | None
    year_founded: int | None
    owner_name: str | None
    owner_title: str | None
    email: str | None
    phone: str | None
    description: str | None
    estimated_revenue_m: float | None
    institutionally_backed: bool
    source: str
    status: str
    score: int
    priority: str
    score_breakdown: list[dict]
    score_reasons: list[str]
    missing_data: list[str]
    red_flags: list[str]
    acquisition_rationale: str
    outreach_angle: str
    updated_at: datetime


class StatusUpdate(BaseModel):
    status: Literal["shortlisted", "review", "rejected"]


class Metrics(BaseModel):
    total: int
    high_priority: int
    shortlisted: int
    needs_review: int
    average_score: float
    data_completeness: float


class ImportResult(BaseModel):
    imported: int
    duplicates_skipped: int
    invalid_rows: int
    errors: list[str]

