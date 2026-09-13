"""Simple population stability index (PSI) demonstration."""
from __future__ import annotations

import math


def population_stability_index(baseline: list[float], current: list[float]) -> float:
    if len(baseline) != len(current) or not baseline:
        raise ValueError("Distributions must be non-empty and have equal bins")
    if abs(sum(baseline) - 1) > .01 or abs(sum(current) - 1) > .01:
        raise ValueError("Distributions must sum to 1")
    epsilon = 1e-6
    return sum((max(c, epsilon) - max(b, epsilon)) * math.log(max(c, epsilon) / max(b, epsilon)) for b, c in zip(baseline, current))


def interpret_psi(psi: float, amber: float = .10, red: float = .25) -> str:
    return "RED" if psi >= red else "AMBER" if psi >= amber else "GREEN"
