"""Illustrative group outcome analysis; not a legal fairness determination."""
from __future__ import annotations

from collections import defaultdict


def outcome_rates(records: list[dict], group_key: str = "group", outcome_key: str = "approved") -> dict[str, float]:
    totals, positives = defaultdict(int), defaultdict(int)
    for record in records:
        group = str(record[group_key])
        totals[group] += 1
        positives[group] += int(bool(record[outcome_key]))
    return {group: positives[group] / total for group, total in totals.items()}


def selection_rate_ratio(rates: dict[str, float]) -> float:
    values = list(rates.values())
    return min(values) / max(values) if values and max(values) else 0.0


def requires_review(ratio: float, threshold: float = .80) -> bool:
    return ratio < threshold
