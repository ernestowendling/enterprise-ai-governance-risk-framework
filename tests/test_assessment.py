from assessments.ai_risk_assessment import assess_domain, residual_level


def test_residual_risk_and_findings():
    assert residual_level("CRITICAL","PARTIALLY EFFECTIVE") == "HIGH"
    result=assess_domain("Model","CRITICAL","PARTIALLY EFFECTIVE")
    assert result.finding
    assert assess_domain("Data","MODERATE","EFFECTIVE").residual_risk == "LOW"
