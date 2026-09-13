from monitoring.drift_monitoring import interpret_psi, population_stability_index
from monitoring.model_monitoring import evaluate


THRESHOLDS={"performance":{"direction":"min","amber":.78,"red":.72},"data_drift":{"direction":"max","amber":.1,"red":.25}}


def test_monitoring_statuses_and_revalidation_action():
    assert evaluate({"performance":.9,"data_drift":.02},THRESHOLDS).status == "GREEN"
    assert evaluate({"performance":.76,"data_drift":.12},THRESHOLDS).status == "AMBER"
    result=evaluate({"performance":.70,"data_drift":.30},THRESHOLDS)
    assert result.status == "RED"
    assert "Trigger event-driven revalidation" in result.actions


def test_drift_metric_and_thresholds():
    assert population_stability_index([.5,.5],[.5,.5]) == 0
    psi=population_stability_index([.8,.2],[.4,.6])
    assert interpret_psi(psi) == "RED"
