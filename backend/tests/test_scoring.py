from types import SimpleNamespace

from app.scoring import score_lead


def thesis(**overrides):
    values = {
        "name": "Sunbelt Services",
        "industries": ["HVAC", "Facility Services"],
        "locations": ["Texas", "Florida"],
        "employee_min": 10,
        "employee_max": 100,
        "minimum_years": 10,
        "excluded_keywords": ["software"],
        "exclude_institutionally_backed": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def lead(**overrides):
    values = {
        "company_name": "Acme Mechanical",
        "domain": "acme.example",
        "industry": "Commercial HVAC",
        "location": "Austin, Texas",
        "employee_count": 35,
        "year_founded": 2000,
        "owner_name": "Jane Owner",
        "email": "jane@acme.example",
        "phone": "+1-555-555-0100",
        "description": "Recurring commercial maintenance contracts",
        "institutionally_backed": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_perfect_fit_scores_100_with_traceable_breakdown():
    result = score_lead(lead(), thesis(), current_year=2026)

    assert result.score == 100
    assert result.priority == "high"
    assert sum(item["points"] for item in result.breakdown) == 100
    assert not result.missing_data
    assert not result.red_flags
    assert any("Target-industry" in item["explanation"] for item in result.breakdown)


def test_institutional_backing_and_excluded_keyword_apply_penalties():
    result = score_lead(
        lead(industry="B2B Software", description="Venture backed software", institutionally_backed=True),
        thesis(),
        current_year=2026,
    )

    assert result.score == 30
    assert result.priority == "low"
    assert "Matches an excluded keyword" in result.red_flags
    assert any("Institutionally backed" in flag for flag in result.red_flags)
    penalty = next(item for item in result.breakdown if item["criterion"] == "Exclusion penalties")
    assert penalty["points"] == -45


def test_missing_data_is_reported_instead_of_invented():
    result = score_lead(
        lead(employee_count=None, year_founded=None, owner_name=None, email=None, phone=None),
        thesis(),
        current_year=2026,
    )

    assert result.score == 43
    assert result.priority == "low"
    assert {"Employee count", "Founding year", "Owner or decision-maker", "Email", "Phone"}.issubset(result.missing_data)
    assert "Not identified" not in result.outreach_angle


def test_near_size_range_gets_partial_credit_and_warning():
    result = score_lead(lead(employee_count=130), thesis(), current_year=2026)

    size = next(item for item in result.breakdown if item["criterion"] == "Company size")
    assert size["points"] == 8
    assert "Company size is outside the preferred range" in result.red_flags


def test_same_input_always_produces_same_score_and_narrative():
    first = score_lead(lead(), thesis(), current_year=2026)
    second = score_lead(lead(), thesis(), current_year=2026)

    assert first == second


def test_no_restrictions_award_industry_and_geography_points():
    result = score_lead(lead(industry="Specialty Trade", location="Ohio"), thesis(industries=[], locations=[]), current_year=2026)

    assert result.score == 100
    assert not any("Outside" in flag for flag in result.red_flags)


def test_invalid_contact_formats_do_not_receive_quality_points():
    result = score_lead(lead(email="not-an-email", phone="123"), thesis(), current_year=2026)

    contact = next(item for item in result.breakdown if item["criterion"] == "Contact quality")
    assert contact["points"] == 0
    assert "Email format appears invalid" in result.red_flags
    assert "Phone format appears invalid" in result.red_flags


def test_operating_history_separates_qualified_leads_without_black_box_logic():
    newer = score_lead(lead(year_founded=2014), thesis(), current_year=2026)
    established = score_lead(lead(year_founded=1996), thesis(), current_year=2026)

    assert newer.score < established.score
    assert next(item for item in newer.breakdown if item["criterion"] == "Operating history")["points"] == 11
    assert next(item for item in established.breakdown if item["criterion"] == "Operating history")["points"] == 15


def test_future_founding_year_is_flagged():
    result = score_lead(lead(year_founded=2030), thesis(), current_year=2026)

    assert "Founding year appears invalid" in result.red_flags
    assert next(item for item in result.breakdown if item["criterion"] == "Operating history")["points"] == 0


def test_contact_explanation_does_not_claim_external_verification():
    result = score_lead(lead(), thesis(), current_year=2026)
    contact = next(item for item in result.breakdown if item["criterion"] == "Contact quality")

    assert "Format-valid" in contact["explanation"]
    assert "Verified" not in contact["explanation"]
