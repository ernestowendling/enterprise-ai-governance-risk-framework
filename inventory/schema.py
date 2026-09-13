"""Schema validation for the central AI inventory."""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from typing import Any

ALLOWED_TIERS = {"LOW", "MODERATE", "HIGH", "CRITICAL", "UNCLASSIFIED"}
ALLOWED_STAGES = {"IDEA", "INTAKE", "CLASSIFIED", "ASSESSMENT", "VALIDATION", "APPROVAL", "DEVELOPMENT", "PRE-PRODUCTION", "PRODUCTION", "MONITORING", "REVALIDATION", "SUSPENDED", "RETIRED"}


class InventoryValidationError(ValueError):
    """Raised when an inventory record is incomplete or inconsistent."""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if str(value).strip().lower() in {"true", "yes", "1"}:
        return True
    if str(value).strip().lower() in {"false", "no", "0"}:
        return False
    raise InventoryValidationError(f"Invalid boolean value: {value!r}")


@dataclass(frozen=True)
class AISystem:
    system_id: str
    system_name: str
    description: str
    business_unit: str
    business_owner: str
    technical_owner: str
    risk_owner: str
    model_type: str
    ai_type: str
    vendor_or_internal: str
    provider: str
    deployment_status: str
    lifecycle_stage: str
    business_purpose: str
    customer_facing: bool
    decision_impact: str
    autonomy_level: str
    financial_impact: str
    personal_data: bool
    sensitive_data: bool
    data_classification: str
    external_data: bool
    jurisdiction: str
    regulatory_scope: str
    explainability_requirement: str
    human_oversight_required: bool
    validation_status: str
    risk_rating: str
    residual_risk: str
    last_assessment_date: str
    next_revalidation_date: str
    monitoring_frequency: str
    open_findings: int
    exceptions: int
    retirement_date: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AISystem":
        missing = [f.name for f in fields(cls) if f.name not in raw and f.default.__class__.__name__ == "_MISSING_TYPE"]
        if missing:
            raise InventoryValidationError(f"Missing required fields: {', '.join(missing)}")
        values = dict(raw)
        for key in ("customer_facing", "personal_data", "sensitive_data", "external_data", "human_oversight_required"):
            values[key] = _bool(values[key])
        for key in ("open_findings", "exceptions"):
            try:
                values[key] = int(values[key])
            except (TypeError, ValueError) as exc:
                raise InventoryValidationError(f"{key} must be an integer") from exc
            if values[key] < 0:
                raise InventoryValidationError(f"{key} cannot be negative")
        values["risk_rating"] = str(values["risk_rating"]).upper()
        values["lifecycle_stage"] = str(values["lifecycle_stage"]).upper()
        if values["risk_rating"] not in ALLOWED_TIERS:
            raise InventoryValidationError(f"Unknown risk rating: {values['risk_rating']}")
        if values["lifecycle_stage"] not in ALLOWED_STAGES:
            raise InventoryValidationError(f"Unknown lifecycle stage: {values['lifecycle_stage']}")
        if not str(values["system_id"]).startswith("AI-"):
            raise InventoryValidationError("system_id must start with AI-")
        for key in ("last_assessment_date", "next_revalidation_date"):
            if values[key]:
                try:
                    date.fromisoformat(str(values[key]))
                except ValueError as exc:
                    raise InventoryValidationError(f"{key} must be ISO date YYYY-MM-DD") from exc
        return cls(**{f.name: values.get(f.name, f.default) for f in fields(cls)})

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}
