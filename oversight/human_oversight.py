"""Proportionate human-oversight patterns."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OversightPlan:
    pattern: str
    reviewer: str
    review_point: str
    override_required: bool
    stop_authority: str
    evidence: tuple[str, ...]


def determine_pattern(decision_impact: str, autonomy: str, customer_facing: bool) -> OversightPlan:
    if decision_impact.upper() == "HIGH" or (customer_facing and autonomy.upper() in {"MEDIUM", "HIGH"}):
        return OversightPlan("HUMAN-IN-THE-LOOP", "Authorised business decision-maker", "Before consequential output is actioned", True, "Business Owner / Risk Owner", ("review decision", "override rationale", "reviewer identity", "timestamp"))
    if autonomy.upper() == "MEDIUM":
        return OversightPlan("HUMAN-ON-THE-LOOP", "Operational supervisor", "Sampled and exception-based review", True, "Service Owner", ("sample log", "exceptions", "overrides"))
    return OversightPlan("HUMAN-IN-COMMAND", "Business Owner", "Periodic governance review", False, "Business Owner", ("periodic review record",))
