from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Thesis(Base):
    __tablename__ = "theses"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(120), default="Lower Middle Market Services")
    industries: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    employee_min: Mapped[int] = mapped_column(Integer, default=10)
    employee_max: Mapped[int] = mapped_column(Integer, default=100)
    minimum_years: Mapped[int] = mapped_column(Integer, default=10)
    excluded_keywords: Mapped[list] = mapped_column(JSON, default=list)
    exclude_institutionally_backed: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), index=True)
    domain: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    owner_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_revenue_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    institutionally_backed: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(80), default="CSV import")
    status: Mapped[str] = mapped_column(String(20), default="review", index=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="low", index=True)
    score_breakdown: Mapped[list] = mapped_column(JSON, default=list)
    score_reasons: Mapped[list] = mapped_column(JSON, default=list)
    missing_data: Mapped[list] = mapped_column(JSON, default=list)
    red_flags: Mapped[list] = mapped_column(JSON, default=list)
    acquisition_rationale: Mapped[str] = mapped_column(Text, default="")
    outreach_angle: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
