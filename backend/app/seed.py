import csv
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Lead, Thesis
from .scoring import apply_score


DEFAULT_THESIS = {
    "name": "Sunbelt Essential Services",
    "industries": ["HVAC", "Facility Services", "Industrial Services", "Commercial Cleaning"],
    "locations": ["Texas", "Florida", "Arizona", "Georgia"],
    "employee_min": 10,
    "employee_max": 100,
    "minimum_years": 10,
    "excluded_keywords": ["software", "restaurant", "consumer app"],
    "exclude_institutionally_backed": True,
}


def parse_bool(value: str | bool | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def optional_int(value):
    try:
        return int(str(value).strip()) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def optional_float(value):
    try:
        return float(str(value).strip()) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def normalize_domain(domain: str | None, website: str | None = None) -> str | None:
    value = (domain or website or "").strip().lower()
    for prefix in ("https://", "http://", "www."):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.split("/")[0] or None


FIELD_LIMITS = {
    "company_name": 200,
    "domain": 200,
    "website": 500,
    "industry": 160,
    "location": 160,
    "owner_name": 160,
    "owner_title": 160,
    "email": 254,
    "phone": 80,
    "source": 80,
}


def validate_import_row(row: dict[str, str | None]) -> list[str]:
    """Return actionable validation errors before a row reaches the database."""
    errors: list[str] = []
    for field, maximum in FIELD_LIMITS.items():
        if len((row.get(field) or "").strip()) > maximum:
            errors.append(f"{field} exceeds {maximum} characters")

    employee_value = (row.get("employee_count") or "").strip()
    employee_count = optional_int(employee_value)
    if employee_value and employee_count is None:
        errors.append("employee_count must be a whole number")
    elif employee_count is not None and not 1 <= employee_count <= 10_000_000:
        errors.append("employee_count must be between 1 and 10,000,000")

    year_value = (row.get("year_founded") or "").strip()
    year_founded = optional_int(year_value)
    if year_value and year_founded is None:
        errors.append("year_founded must be a whole number")
    elif year_founded is not None and not 1800 <= year_founded <= date.today().year:
        errors.append(f"year_founded must be between 1800 and {date.today().year}")

    revenue_value = (row.get("estimated_revenue_m") or "").strip()
    revenue = optional_float(revenue_value)
    if revenue_value and revenue is None:
        errors.append("estimated_revenue_m must be numeric")
    elif revenue is not None and not 0 <= revenue <= 1_000_000:
        errors.append("estimated_revenue_m must be between 0 and 1,000,000")

    website = (row.get("website") or "").strip()
    if website:
        parsed = urlparse(website)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("website must be an absolute http:// or https:// URL")
    return errors


def row_to_lead(row: dict, source: str = "CSV import") -> Lead:
    website = (row.get("website") or "").strip() or None
    return Lead(
        company_name=(row.get("company_name") or "").strip(),
        domain=normalize_domain(row.get("domain"), website),
        website=website,
        industry=(row.get("industry") or "").strip() or None,
        location=(row.get("location") or "").strip() or None,
        employee_count=optional_int(row.get("employee_count")),
        year_founded=optional_int(row.get("year_founded")),
        owner_name=(row.get("owner_name") or "").strip() or None,
        owner_title=(row.get("owner_title") or "").strip() or None,
        email=(row.get("email") or "").strip() or None,
        phone=(row.get("phone") or "").strip() or None,
        description=(row.get("description") or "").strip() or None,
        estimated_revenue_m=optional_float(row.get("estimated_revenue_m")),
        institutionally_backed=parse_bool(row.get("institutionally_backed")),
        source=(row.get("source") or source).strip(),
        status="review",
    )


def seed_database(db: Session) -> None:
    thesis = db.scalar(select(Thesis).limit(1))
    if not thesis:
        thesis = Thesis(**DEFAULT_THESIS)
        db.add(thesis)
        db.flush()

    data_path = Path(__file__).resolve().parents[1] / "data" / "sample_leads.csv"
    with data_path.open(encoding="utf-8-sig", newline="") as handle:
        seed_rows = list(csv.DictReader(handle))

    # Seed records are fictional examples. Keep that provenance accurate even
    # for databases created by an older version that preserved source-like
    # labels such as Apollo or Google Maps from the sample file.
    seed_domains = {normalize_domain(row.get("domain"), row.get("website")) for row in seed_rows}
    existing_seed_leads = db.scalars(select(Lead).where(Lead.domain.in_(seed_domains))).all()
    for lead in existing_seed_leads:
        lead.source = "Synthetic demo"

    existing_leads = db.scalars(select(Lead)).all()
    if existing_leads:
        # Scores and deterministic narratives are persisted as a read cache.
        # Refresh them on startup so scoring-rule releases cannot leave stale
        # evidence in an existing demo database.
        for lead in existing_leads:
            apply_score(lead, thesis)
        db.commit()
        return

    for row in seed_rows:
        lead = row_to_lead(row, source="Demo dataset")
        lead.source = "Synthetic demo"
        apply_score(lead, thesis)
        db.add(lead)
    db.commit()
