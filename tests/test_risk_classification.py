from assessments.risk_classification import classify, load_rules


def loan_case():
    return {"customer_facing": True, "decision_impact": "high", "financial_impact": "high", "autonomy_level": "medium", "personal_data": True, "sensitive_data": True, "regulatory_relevance": "high", "model_complexity": "high", "vendor_or_internal": "internal", "explainability_requirement": "high", "bias_impact": "high", "operational_criticality": "high", "cybersecurity_impact": "high", "human_oversight": "present"}


def test_loan_case_is_critical_from_reusable_rules():
    result = classify(loan_case())
    assert result.risk_tier == "CRITICAL"
    assert "CTRL-007" in result.mandatory_controls
    assert result.required_approval_level == "Executive Risk Committee"


def test_low_risk_case_receives_proportionate_treatment():
    result = classify({"customer_facing": False, "decision_impact": "low", "financial_impact": "low", "autonomy_level": "low", "personal_data": False, "sensitive_data": False, "vendor_or_internal": "internal"})
    assert result.risk_tier == "LOW"
    assert result.mandatory_controls == ("CTRL-001", "CTRL-002", "CTRL-003")


def test_tier_boundaries_are_inclusive():
    rules = load_rules(); rules["factors"] = [{"field":"x","equals":"yes","points":6,"rationale":"boundary"}]
    assert classify({"x":"yes"}, rules).risk_tier == "MODERATE"
    rules["factors"][0]["points"] = 12
    assert classify({"x":"yes"}, rules).risk_tier == "HIGH"
    rules["factors"][0]["points"] = 20
    assert classify({"x":"yes"}, rules).risk_tier == "CRITICAL"
