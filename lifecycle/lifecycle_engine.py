"""Controlled lifecycle transitions and governance gate decisions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ORDER = ("IDEA", "INTAKE", "CLASSIFIED", "ASSESSMENT", "VALIDATION", "APPROVAL", "DEVELOPMENT", "PRE-PRODUCTION", "PRODUCTION", "MONITORING", "REVALIDATION", "RETIRED")


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_transition(current: str, target: str, context: dict) -> GateDecision:
    current, target = current.upper(), target.upper()
    if target in {"SUSPENDED", "RETIRED"}:
        return GateDecision(True, ("Controlled exit transition permitted.",))
    if current not in ORDER or target not in ORDER or ORDER.index(target) != ORDER.index(current) + 1:
        return GateDecision(False, ("Transitions must follow the controlled lifecycle sequence.",))
    reasons = []
    if target == "CLASSIFIED" and not context.get("classification_complete"):
        reasons.append("Risk classification is incomplete.")
    if target == "VALIDATION" and not context.get("assessment_approved"):
        reasons.append("Risk assessment is not approved.")
    if target in {"APPROVAL", "PRODUCTION"} and context.get("risk_tier") in {"HIGH", "CRITICAL"} and context.get("validation_status") != "VALIDATED":
        reasons.append("Independent validation is mandatory for high/critical AI.")
    if target in {"APPROVAL", "PRODUCTION"} and context.get("human_oversight_required") and not context.get("human_oversight_control"):
        reasons.append("Mandatory human-oversight control is missing.")
    if target == "PRODUCTION" and not context.get("approval_granted"):
        reasons.append("Governance approval has not been granted.")
    return GateDecision(not reasons, tuple(reasons) if reasons else ("Mandatory gate evidence is complete.",))


def revalidation_overdue(next_date: str, as_of: date | None = None) -> bool:
    return date.fromisoformat(next_date) < (as_of or date.today())


def event_driven_revalidation(events: set[str]) -> bool:
    triggers = {"material_model_change", "material_data_change", "new_use", "performance_degradation", "drift_breach", "regulatory_change", "material_incident", "provider_version_change"}
    return bool(events & triggers)
