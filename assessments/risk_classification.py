"""Transparent, configuration-driven AI risk classification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ClassificationResult:
    inherent_risk_score: int
    risk_tier: str
    rationale: tuple[str, ...]
    mandatory_controls: tuple[str, ...]
    required_review_functions: tuple[str, ...]
    required_approval_level: str
    validation_requirements: tuple[str, ...]
    monitoring_requirements: tuple[str, ...]
    revalidation_frequency_months: int


def load_rules(path: str | Path | None = None) -> dict[str, Any]:
    location = Path(path) if path else Path(__file__).parents[1] / "controls" / "classification_rules.yaml"
    return yaml.safe_load(location.read_text(encoding="utf-8"))


def classify(attributes: dict[str, Any], rules: dict[str, Any] | None = None) -> ClassificationResult:
    config = rules or load_rules()
    score, rationale = 0, []
    normalised = {k: str(v).strip().lower() if not isinstance(v, bool) else v for k, v in attributes.items()}
    for factor in config["factors"]:
        actual = normalised.get(factor["field"])
        expected = factor["equals"]
        match = actual == expected or (isinstance(expected, list) and actual in expected)
        if match:
            score += int(factor["points"])
            rationale.append(factor["rationale"])
    tier_name = next(t["name"] for t in config["tiers"] if int(t["min_score"]) <= score <= int(t["max_score"]))
    tier = config["tier_requirements"][tier_name]
    return ClassificationResult(score, tier_name, tuple(rationale) or ("No elevated factors identified.",), tuple(tier["controls"]), tuple(tier["review_functions"]), tier["approval"], tuple(tier["validation"]), tuple(tier["monitoring"]), int(tier["revalidation_months"]))


def explain(result: ClassificationResult) -> str:
    return f"{result.risk_tier} ({result.inherent_risk_score} points): " + "; ".join(result.rationale)
