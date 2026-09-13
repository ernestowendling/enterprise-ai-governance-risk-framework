from datetime import date

from lifecycle.lifecycle_engine import evaluate_transition, event_driven_revalidation, revalidation_overdue


def test_high_risk_approval_is_blocked_without_validation():
    result = evaluate_transition("VALIDATION", "APPROVAL", {"risk_tier":"HIGH", "validation_status":"PENDING", "human_oversight_required":False})
    assert not result.allowed
    assert "validation" in result.reasons[0].lower()


def test_required_human_oversight_blocks_approval():
    result = evaluate_transition("VALIDATION", "APPROVAL", {"risk_tier":"HIGH", "validation_status":"VALIDATED", "human_oversight_required":True, "human_oversight_control":False})
    assert not result.allowed


def test_complete_gate_passes_and_skipping_does_not():
    context={"risk_tier":"HIGH","validation_status":"VALIDATED","human_oversight_required":True,"human_oversight_control":True}
    assert evaluate_transition("VALIDATION","APPROVAL",context).allowed
    assert not evaluate_transition("ASSESSMENT","APPROVAL",context).allowed


def test_overdue_and_event_driven_revalidation():
    assert revalidation_overdue("2026-01-01", date(2026, 9, 1))
    assert not revalidation_overdue("2027-01-01", date(2026, 9, 1))
    assert event_driven_revalidation({"drift_breach"})
    assert not event_driven_revalidation({"minor_documentation_change"})
