"""Structured governance finding shared across assessments and monitoring."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    finding_id: str
    system_id: str
    source: str
    title: str
    description: str
    severity: str
    owner: str
    created_at: str
    due_date: str
    status: str
    remediation: str
    closure_evidence: str
    related_control: str
    lifecycle_impact: str
