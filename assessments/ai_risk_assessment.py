"""Domain-based AI risk assessment and residual-risk judgement."""
from __future__ import annotations

from dataclasses import dataclass

DOMAINS = ("Strategic", "Customer / Conduct", "Model", "Data", "Privacy", "Security", "Operational", "Legal / Regulatory", "Third-Party", "Explainability", "Bias / Fairness", "Human Oversight", "Reputational", "Generative AI")
LEVELS = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class DomainAssessment:
    domain: str
    inherent_risk: str
    control_effectiveness: str
    residual_risk: str
    finding: str = ""


def residual_level(inherent_risk: str, effectiveness: str) -> str:
    inherent = LEVELS[inherent_risk.upper()]
    reduction = {"INEFFECTIVE": 0, "PARTIALLY EFFECTIVE": 1, "EFFECTIVE": 2}[effectiveness.upper()]
    return next(name for name, value in LEVELS.items() if value == max(1, inherent - reduction))


def assess_domain(domain: str, inherent_risk: str, effectiveness: str) -> DomainAssessment:
    if domain not in DOMAINS:
        raise ValueError(f"Unknown risk domain: {domain}")
    residual = residual_level(inherent_risk, effectiveness)
    finding = "Control remediation and approval condition required." if residual in {"HIGH", "CRITICAL"} else ""
    return DomainAssessment(domain, inherent_risk.upper(), effectiveness.upper(), residual, finding)
