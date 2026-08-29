from datetime import date
from typing import Any, Protocol


class NarrativeProvider(Protocol):
    """Extension point for a future LLM provider; no provider is required today."""

    def build(self, lead: Any, thesis: Any, score: int, reasons: list[str]) -> tuple[str, str]: ...


class RuleBasedNarrativeProvider:
    def build(self, lead: Any, thesis: Any, score: int, reasons: list[str]) -> tuple[str, str]:
        age = (date.today().year - lead.year_founded) if lead.year_founded else None
        traits: list[str] = []
        if age:
            traits.append(f"an established {age}-year operating history")
        if lead.employee_count:
            traits.append(f"a {lead.employee_count}-person team")
        if lead.industry:
            traits.append(f"exposure to {lead.industry.lower()}")
        if lead.owner_name:
            traits.append("an identified owner contact")

        fit = "strong" if score >= 75 else "possible" if score >= 50 else "limited"
        evidence = ", ".join(traits[:3]) or "the currently available company profile"
        rationale = (
            f"{lead.company_name} shows {fit} alignment with the “{thesis.name}” thesis based on "
            f"{evidence}. The {score}/100 score is rules-based; verify financial performance, customer "
            "concentration, and owner objectives before advancing the opportunity."
        )

        owner = lead.owner_name.split()[0] if lead.owner_name else "there"
        market = lead.location or "your market"
        category = lead.industry or "business services"
        opener = (
            f"Hi {owner}, I came across {lead.company_name} while researching established {category.lower()} "
            f"companies in {market}. I was impressed by the business you have built and would value a brief, "
            "confidential conversation to learn about your long-term goals. I am focused on responsible, "
            "long-term ownership—not a quick flip—and would be glad to work around your schedule."
        )
        return rationale, opener


def get_narrative_provider() -> NarrativeProvider:
    # A future provider can be selected here by configuration. The deterministic
    # provider is intentionally the only implementation required for the demo.
    return RuleBasedNarrativeProvider()
