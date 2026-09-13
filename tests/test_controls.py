from pathlib import Path

import yaml


def test_control_library_is_complete_and_unique():
    data = yaml.safe_load((Path(__file__).parents[1] / "controls" / "control_library.yaml").read_text(encoding="utf-8"))["controls"]
    ids = [control["control_id"] for control in data]
    assert len(data) >= 22
    assert len(ids) == len(set(ids))
    required = {"description", "control_objective", "evidence_required", "accountable_role", "test_method", "testing_frequency", "regulatory_mapping"}
    assert all(required <= set(control) for control in data)
