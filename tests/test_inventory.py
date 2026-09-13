import csv
from pathlib import Path

import pytest

from inventory.schema import AISystem, InventoryValidationError
from inventory.service import load_inventory, validate_unique_ids

ROOT = Path(__file__).parents[1]


def test_all_synthetic_inventory_records_are_valid_and_unique():
    systems, errors = load_inventory(ROOT / "inventory" / "ai_inventory.csv")
    assert len(systems) == 9
    assert errors == []
    validate_unique_ids(systems)


def test_invalid_record_fails_gracefully():
    with (ROOT / "inventory" / "ai_inventory.csv").open(encoding="utf-8") as handle:
        raw = next(csv.DictReader(handle))
    raw["system_id"] = "bad-id"
    with pytest.raises(InventoryValidationError, match="must start"):
        AISystem.from_dict(raw)


def test_invalid_boolean_is_rejected():
    with (ROOT / "inventory" / "ai_inventory.csv").open(encoding="utf-8") as handle:
        raw = next(csv.DictReader(handle))
    raw["personal_data"] = "perhaps"
    with pytest.raises(InventoryValidationError, match="Invalid boolean"):
        AISystem.from_dict(raw)
