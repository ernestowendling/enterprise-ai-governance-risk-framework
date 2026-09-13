"""Monitoring thresholds translated into governance actions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringResult:
    status: str
    breaches: tuple[str, ...]
    actions: tuple[str, ...]


def evaluate(metrics: dict[str, float], thresholds: dict[str, dict[str, float]]) -> MonitoringResult:
    amber, red = [], []
    for metric, value in metrics.items():
        if metric not in thresholds:
            continue
        direction = thresholds[metric].get("direction", "max")
        if direction == "min":
            if value < thresholds[metric]["red"]: red.append(metric)
            elif value < thresholds[metric]["amber"]: amber.append(metric)
        else:
            if value > thresholds[metric]["red"]: red.append(metric)
            elif value > thresholds[metric]["amber"]: amber.append(metric)
    if red:
        return MonitoringResult("RED", tuple(red + amber), ("Create finding", "Escalate to risk owner", "Trigger event-driven revalidation", "Consider suspension"))
    if amber:
        return MonitoringResult("AMBER", tuple(amber), ("Create monitoring alert", "Increase review frequency", "Assign investigation"))
    return MonitoringResult("GREEN", (), ("Continue scheduled monitoring",))
