"""Controlled lifecycle transitions and governance gate decisions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone
from typing import Any

ORDER = ("IDEA", "INTAKE", "CLASSIFIED", "ASSESSMENT", "VALIDATION", "APPROVAL", "DEVELOPMENT", "PRE-PRODUCTION", "PRODUCTION", "MONITORING", "REVALIDATION", "RETIRED")


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ApprovalDecision:
    decision: str
    decision_authority: str
    rationale: tuple[str, ...]
    outstanding_conditions: tuple[str, ...]
    evidence: tuple[str, ...]
    timestamp: str


APPROVAL_AUTHORITIES = {"LOW":"Business Owner", "MODERATE":"Business and Risk Owners", "HIGH":"AI Governance Committee", "CRITICAL":"Executive Risk Committee"}


def decide_approval(effective_risk_tier: str, assessment: dict[str, Any], validation: Any, controls: dict[str, Any], findings: list[Any], human_oversight_required: bool) -> ApprovalDecision:
    """Apply explicit decision rights to current governance evidence."""
    blockers, conditions, evidence = [], [], []
    if assessment.get("assessment_status") not in {"APPROVED", "APPROVED WITH CONDITIONS"}:
        blockers.append("Risk assessment is not approved.")
    if effective_risk_tier in {"HIGH", "CRITICAL"}:
        if validation.status not in {"VALIDATED", "VALIDATED WITH CONDITIONS"}:
            blockers.append("Acceptable independent validation is missing.")
        elif validation.status == "VALIDATED WITH CONDITIONS":
            if not validation.conditions_accepted:
                blockers.append("Validation conditions have not been explicitly accepted.")
            else:
                conditions.extend(validation.conditions)
                evidence.append(validation.evidence_reference)
    failed = [cid for cid, item in controls.items() if item.status in {"NOT STARTED", "FAILED"}]
    if failed:
        blockers.append("Mandatory control evidence is incomplete: " + ", ".join(failed))
    if human_oversight_required and controls.get("CTRL-009") and controls["CTRL-009"].status != "EVIDENCED":
        blockers.append("Required human oversight is not evidenced.")
    critical = [f.finding_id for f in findings if f.severity == "CRITICAL" and f.status not in {"CLOSED", "RISK ACCEPTED"}]
    if critical:
        blockers.append("Unresolved critical findings: " + ", ".join(critical))
    evidence.extend(item.evidence_reference for item in controls.values() if item.evidence_reference)
    if blockers:
        decision = "BLOCKED"
    elif conditions or assessment.get("assessment_status") == "APPROVED WITH CONDITIONS":
        decision = "APPROVED WITH CONDITIONS"
        conditions.extend(assessment.get("approval_conditions", []))
    else:
        decision = "APPROVED"
    return ApprovalDecision(decision, APPROVAL_AUTHORITIES[effective_risk_tier], tuple(blockers) if blockers else ("Required governance evidence is complete.",), tuple(dict.fromkeys(conditions)), tuple(dict.fromkeys(filter(None, evidence))), datetime.now(timezone.utc).isoformat())


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
    if target in {"APPROVAL", "PRODUCTION"} and context.get("risk_tier") in {"HIGH", "CRITICAL"} and context.get("validation_status") not in {"VALIDATED", "VALIDATED WITH CONDITIONS"}:
        reasons.append("Independent validation is mandatory for high/critical AI.")
    if context.get("validation_status") == "VALIDATED WITH CONDITIONS" and not context.get("validation_conditions_accepted"):
        reasons.append("Validation conditions require explicit acceptance and tracking.")
    if context.get("failed_mandatory_controls"):
        reasons.append("Mandatory controls are not evidenced: " + ", ".join(context["failed_mandatory_controls"]))
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
