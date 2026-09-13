"""Domain-based AI risk assessment and residual-risk judgement."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from findings import Finding

DOMAINS = ("Strategic", "Customer / Conduct", "Model", "Data", "Privacy", "Security", "Operational", "Legal / Regulatory", "Third-Party", "Explainability", "Bias / Fairness", "Human Oversight", "Reputational", "Generative AI")
LEVELS = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class DomainAssessment:
    domain: str
    inherent_risk: str
    control_effectiveness: str
    residual_risk: str
    finding: str = ""


@dataclass(frozen=True)
class AssessmentQuestion:
    question_id: str
    risk_domain: str
    question: str
    answer_options: tuple[str, ...]
    material: bool
    evidence_expectation: str
    negative_finding: str
    owner: str
    lifecycle_implication: str


@dataclass(frozen=True)
class StructuredAssessmentResult:
    domain_risk: dict[str, str]
    control_effectiveness: str
    residual_risk: str
    findings: tuple[Finding, ...]
    remediation_requirements: tuple[str, ...]
    approval_conditions: tuple[str, ...]
    reviewer_comments: str
    assessment_status: str


def load_questions(path: str | Path | None = None) -> tuple[AssessmentQuestion, ...]:
    location = Path(path) if path else Path(__file__).with_name("questionnaire.yaml")
    raw = yaml.safe_load(location.read_text(encoding="utf-8"))["questions"]
    return tuple(AssessmentQuestion(item["question_id"], item["risk_domain"], item["question"], tuple(item["answer_options"]), bool(item.get("material", False)), item["evidence_expectation"], item.get("negative_finding", ""), item.get("owner", "Business Owner"), item.get("lifecycle_implication", "Remediation required")) for item in raw)


def evaluate_questionnaire(system_id: str, answers: dict[str, str], reviewer_comments: str = "", status: str = "IN REVIEW", questions: tuple[AssessmentQuestion, ...] | None = None) -> StructuredAssessmentResult:
    """Evaluate evidence gaps as a decision aid; expert judgement remains authoritative."""
    question_set = questions or load_questions()
    domain_counts: dict[str, list[int]] = {}
    findings: list[Finding] = []
    weights = {"YES": 0, "PARTIAL": 1, "NO": 2, "NOT APPLICABLE": 0}
    for question in question_set:
        answer = answers.get(question.question_id, "NOT APPLICABLE").upper()
        if answer not in question.answer_options:
            raise ValueError(f"Invalid answer for {question.question_id}: {answer}")
        if answer == "NOT APPLICABLE":
            continue
        domain_counts.setdefault(question.risk_domain, []).append(weights[answer])
        if question.material and answer in {"NO", "PARTIAL"} and question.negative_finding:
            severity = "HIGH" if answer == "NO" else "MODERATE"
            findings.append(Finding(f"FND-{system_id}-{question.question_id}", system_id, "RISK ASSESSMENT", question.negative_finding, f"Question {question.question_id} answered {answer}.", severity, question.owner, datetime.now(timezone.utc).isoformat(), (date.today()+timedelta(days=45)).isoformat(), "OPEN", question.evidence_expectation, "", "", question.lifecycle_implication))
    domain_risk = {domain: "HIGH" if max(values) == 2 else "MODERATE" if max(values) == 1 else "LOW" for domain, values in domain_counts.items()}
    material_answers = [weights[answers.get(q.question_id, "NOT APPLICABLE").upper()] for q in question_set if answers.get(q.question_id, "NOT APPLICABLE").upper() != "NOT APPLICABLE"]
    effectiveness = "INEFFECTIVE" if any(v == 2 for v in material_answers) else "PARTIALLY EFFECTIVE" if any(v == 1 for v in material_answers) else "EFFECTIVE"
    residual = "HIGH" if any(f.severity == "HIGH" for f in findings) else "MODERATE" if findings else "LOW"
    conditions = tuple(f.lifecycle_impact for f in findings)
    return StructuredAssessmentResult(domain_risk, effectiveness, residual, tuple(findings), tuple(f.remediation for f in findings), conditions, reviewer_comments, status)


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
