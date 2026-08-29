from dataclasses import dataclass
from datetime import date
import re
from typing import Any

from .narratives import get_narrative_provider


@dataclass
class ScoreResult:
    score: int
    priority: str
    breakdown: list[dict]
    reasons: list[str]
    missing_data: list[str]
    red_flags: list[str]
    rationale: str
    outreach_angle: str


def _contains_any(text: str | None, values: list[str]) -> bool:
    haystack = (text or "").lower()
    return any(value.strip().lower() in haystack for value in values if value.strip())


def _valid_email(value: str | None) -> bool:
    return bool(value and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value.strip()))


def _valid_phone(value: str | None) -> bool:
    return bool(value and len(re.sub(r"\D", "", value)) >= 10)


def _add(breakdown: list[dict], criterion: str, points: int, maximum: int, explanation: str) -> None:
    breakdown.append({"criterion": criterion, "points": points, "maximum": maximum, "explanation": explanation})


def score_lead(lead: Any, thesis: Any, current_year: int | None = None) -> ScoreResult:
    current_year = current_year or date.today().year
    breakdown: list[dict] = []
    reasons: list[str] = []
    missing: list[str] = []
    flags: list[str] = []

    combined = " ".join(filter(None, [lead.industry, lead.description]))
    if thesis.industries and _contains_any(combined, thesis.industries):
        industry_points = 25
        reasons.append(f"Matches target industry: {lead.industry or thesis.industries[0]}")
        industry_text = "Target-industry match"
    elif not thesis.industries:
        industry_points = 25
        industry_text = "No industry restriction"
    else:
        industry_points = 0
        industry_text = "Outside selected industries"
        flags.append("Industry does not match the acquisition thesis")
    _add(breakdown, "Industry match", industry_points, 25, industry_text)

    if lead.employee_count is None:
        employee_points = 0
        employee_text = "Employee count unavailable"
        missing.append("Employee count")
    elif thesis.employee_min <= lead.employee_count <= thesis.employee_max:
        employee_points = 20
        employee_text = f"{lead.employee_count} employees is inside the target range"
        reasons.append(f"Company size fits {thesis.employee_min}–{thesis.employee_max} employee target")
    elif thesis.employee_min * 0.5 <= lead.employee_count <= thesis.employee_max * 1.5:
        employee_points = 8
        employee_text = f"{lead.employee_count} employees is near the target range"
        flags.append("Company size is outside the preferred range")
    else:
        employee_points = 0
        employee_text = f"{lead.employee_count} employees is well outside the target range"
        flags.append("Company size is materially outside the preferred range")
    _add(breakdown, "Company size", employee_points, 20, employee_text)

    if thesis.locations and _contains_any(lead.location, thesis.locations):
        geography_points = 15
        geography_text = f"{lead.location} matches a target geography"
        reasons.append(f"Located in target geography: {lead.location}")
    elif not thesis.locations:
        geography_points = 15
        geography_text = "No geographic restriction"
    elif not lead.location:
        geography_points = 0
        geography_text = "Location unavailable"
        missing.append("Location")
    else:
        geography_points = 0
        geography_text = f"{lead.location} is outside target geographies"
        flags.append("Outside the preferred geography")
    _add(breakdown, "Geography", geography_points, 15, geography_text)

    if lead.year_founded and lead.year_founded > current_year:
        age_points = 0
        age_text = "Founding year is in the future"
        flags.append("Founding year appears invalid")
    elif lead.year_founded:
        years = current_year - lead.year_founded
        if years >= thesis.minimum_years:
            # Qualifying businesses receive strong credit, while longer operating
            # histories provide useful deterministic separation within the queue.
            age_points = min(15, 10 + round(max(0, years - thesis.minimum_years) / 3))
            age_text = f"{years} years in operation meets the {thesis.minimum_years}-year minimum"
            reasons.append(f"Established operating history ({years} years)")
        elif years >= thesis.minimum_years * 0.6:
            age_points = 6
            age_text = f"{years} years in operation is below preference"
            flags.append("Operating history is shorter than preferred")
        else:
            age_points = 0
            age_text = f"Only {years} years in operation"
            flags.append("Business may be too young for the thesis")
    else:
        age_points = 0
        age_text = "Founding year unavailable"
        missing.append("Founding year")
    _add(breakdown, "Operating history", age_points, 15, age_text)

    owner_points = 10 if lead.owner_name else 0
    _add(breakdown, "Owner identified", owner_points, 10, "Owner contact is available" if owner_points else "Owner contact unavailable")
    if owner_points:
        reasons.append(f"Decision-maker identified: {lead.owner_name}")
    else:
        missing.append("Owner or decision-maker")

    valid_email = _valid_email(lead.email)
    valid_phone = _valid_phone(lead.phone)
    contact_points = (6 if valid_email else 0) + (4 if valid_phone else 0)
    channels = " and ".join(channel for channel, valid in [("email", valid_email), ("phone", valid_phone)] if valid)
    _add(breakdown, "Contact quality", contact_points, 10, f"Format-valid fields include {channels}" if channels else "No direct contact channel")
    if contact_points == 10:
        reasons.append("Both email and phone are available")
    if lead.email and not valid_email:
        flags.append("Email format appears invalid")
    elif not lead.email:
        missing.append("Email")
    if lead.phone and not valid_phone:
        flags.append("Phone format appears invalid")
    elif not lead.phone:
        missing.append("Phone")

    completeness_fields = [lead.domain, lead.industry, lead.location, lead.employee_count, lead.year_founded, lead.description]
    completeness_points = round(sum(value not in (None, "") for value in completeness_fields) / len(completeness_fields) * 5)
    _add(breakdown, "Data completeness", completeness_points, 5, f"{completeness_points}/5 core profile fields complete")
    for label, value in zip(
        ["Domain", "Industry", "Location", "Employee count", "Founding year", "Description"],
        completeness_fields,
    ):
        if value in (None, "") and label not in missing:
            missing.append(label)

    penalty = 0
    if thesis.excluded_keywords and _contains_any(combined, thesis.excluded_keywords):
        penalty -= 25
        flags.append("Matches an excluded keyword")
    if thesis.exclude_institutionally_backed and lead.institutionally_backed:
        penalty -= 20
        flags.append("Institutionally backed; likely outside owner-operated target profile")
    if penalty:
        _add(breakdown, "Exclusion penalties", penalty, 0, "Thesis exclusions reduce priority")

    total = max(0, min(100, sum(item["points"] for item in breakdown)))
    priority = "high" if total >= 75 else "medium" if total >= 50 else "low"
    rationale, outreach = get_narrative_provider().build(lead, thesis, total, reasons)
    return ScoreResult(total, priority, breakdown, reasons, missing, flags, rationale, outreach)


def apply_score(lead: Any, thesis: Any) -> None:
    result = score_lead(lead, thesis)
    lead.score = result.score
    lead.priority = result.priority
    lead.score_breakdown = result.breakdown
    lead.score_reasons = result.reasons
    lead.missing_data = result.missing_data
    lead.red_flags = result.red_flags
    lead.acquisition_rationale = result.rationale
    lead.outreach_angle = result.outreach_angle
