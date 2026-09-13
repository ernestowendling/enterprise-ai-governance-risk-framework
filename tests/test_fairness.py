from monitoring.fairness_monitoring import outcome_rates, requires_review, selection_rate_ratio


def test_fairness_review_trigger():
    records=[{"group":"A","approved":1},{"group":"A","approved":1},{"group":"B","approved":1},{"group":"B","approved":0}]
    rates=outcome_rates(records)
    assert rates == {"A":1.0,"B":.5}
    assert selection_rate_ratio(rates) == .5
    assert requires_review(.5)
    assert not requires_review(.85)
