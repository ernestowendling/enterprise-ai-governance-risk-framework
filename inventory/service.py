"""Persistence-agnostic inventory services."""
from __future__ import annotations

import csv
from pathlib import Path

from inventory.schema import AISystem, InventoryValidationError


def load_inventory(path: str | Path) -> tuple[list[AISystem], list[str]]:
    systems, errors = [], []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            try:
                systems.append(AISystem.from_dict(row))
            except InventoryValidationError as exc:
                errors.append(f"Row {row_number}: {exc}")
    return systems, errors


def validate_unique_ids(systems: list[AISystem]) -> None:
    ids = [item.system_id for item in systems]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise InventoryValidationError(f"Duplicate system IDs: {', '.join(duplicates)}")
