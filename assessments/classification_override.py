"""Governed expert override without losing the calculated classification."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from assessments.risk_classification import ClassificationResult

TIERS = ("LOW", "MODERATE", "HIGH", "CRITICAL")


@dataclass(frozen=True)
class ClassificationOverride:
    calculated_tier: str
    proposed_tier: str
    direction: str
    rationale: str
    requester_role: str
    approver_role: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "PROPOSED"

    @classmethod
    def propose(cls, calculated: str, proposed: str, rationale: str, requester: str) -> "ClassificationOverride":
        if calculated not in TIERS or proposed not in TIERS:
            raise ValueError("Unknown risk tier")
        if not rationale.strip():
            raise ValueError("Override rationale is required")
        direction = "UPWARD" if TIERS.index(proposed) > TIERS.index(calculated) else "DOWNWARD" if TIERS.index(proposed) < TIERS.index(calculated) else "NO CHANGE"
        return cls(calculated, proposed, direction, rationale.strip(), requester)

    def decide(self, approve: bool, approver: str) -> "ClassificationOverride":
        if not self.rationale:
            raise ValueError("Override rationale is required")
        if approve and approver.strip().lower() == self.requester_role.strip().lower():
            raise ValueError("Override approver must be distinct from requester")
        return replace(self, approver_role=approver, status="APPROVED" if approve else "REJECTED", timestamp=datetime.now(timezone.utc).isoformat())


@dataclass
class ClassificationDecision:
    calculated: ClassificationResult
    override: ClassificationOverride | None = None


def effective_tier(decision: ClassificationDecision) -> str:
    return decision.override.proposed_tier if decision.override and decision.override.status == "APPROVED" else decision.calculated.risk_tier
