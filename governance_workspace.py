"""In-memory governance workspace connecting the demonstration lifecycle."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any

from assessments.classification_override import ClassificationDecision, ClassificationOverride, effective_tier
from assessments.risk_classification import ClassificationResult, classify
from audit.audit_trail import AuditEvent, append_event
from findings import Finding
from inventory.schema import AISystem
from lifecycle.lifecycle_engine import ApprovalDecision, decide_approval
from monitoring.model_monitoring import MonitoringResult


@dataclass
class ValidationRecord:
    status: str = "NOT STARTED"
    validator_role: str = "Model Risk"
    validation_date: str = ""
    scope: str = ""
    conclusions: str = ""
    limitations: str = ""
    conditions: list[str] = field(default_factory=list)
    conditions_accepted: bool = False
    evidence_reference: str = ""


@dataclass
class ControlImplementation:
    control_id: str
    status: str = "NOT STARTED"
    control_owner: str = ""
    evidence_reference: str = ""
    reviewer: str = ""
    review_date: str = ""
    comments: str = ""


@dataclass
class GovernanceWorkspace:
    systems: dict[str, AISystem] = field(default_factory=dict)
    classifications: dict[str, ClassificationDecision] = field(default_factory=dict)
    assessments: dict[str, dict[str, Any]] = field(default_factory=dict)
    control_status: dict[str, dict[str, ControlImplementation]] = field(default_factory=dict)
    validations: dict[str, ValidationRecord] = field(default_factory=dict)
    approvals: dict[str, ApprovalDecision] = field(default_factory=dict)
    monitoring_results: dict[str, MonitoringResult] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    exceptions: list[dict[str, Any]] = field(default_factory=list)
    audit_events: list[AuditEvent] = field(default_factory=list)
    revalidation_status: dict[str, dict[str, Any]] = field(default_factory=dict)

    def audit(self, system_id: str, event_type: str, previous: str, new: str, rationale: str, evidence: str, actor: str = "AI Governance") -> AuditEvent:
        return append_event(self.audit_events, event_id=f"EVT-{len(self.audit_events)+1:04}", timestamp=datetime.now(timezone.utc).isoformat(), system_id=system_id, event_type=event_type, actor_role=actor, previous_status=previous, new_status=new, rationale=rationale, evidence_reference=evidence)

    def register(self, values: dict[str, Any]) -> AISystem:
        number = max([int(key.split("-")[1]) for key in self.systems] or [0]) + 1
        system_id = f"AI-{number:03d}"
        defaults = {"description":"Synthetic demonstration use case","business_unit":"Unassigned","business_owner":"Unassigned","technical_owner":"Unassigned","risk_owner":"Unassigned","model_type":"Unspecified","ai_type":"Predictive AI","vendor_or_internal":"internal","provider":"Internal","deployment_status":"Registered","lifecycle_stage":"INTAKE","business_purpose":"Governance intake","customer_facing":False,"decision_impact":"LOW","autonomy_level":"LOW","financial_impact":"LOW","personal_data":False,"sensitive_data":False,"data_classification":"Internal","external_data":False,"jurisdiction":"Switzerland","regulatory_scope":"Institution-specific assessment required","explainability_requirement":"MEDIUM","human_oversight_required":False,"validation_status":"NOT STARTED","risk_rating":"UNCLASSIFIED","residual_risk":"UNCLASSIFIED","last_assessment_date":"","next_revalidation_date":"","monitoring_frequency":"To be determined","open_findings":0,"exceptions":0,"retirement_date":""}
        system = AISystem.from_dict({**defaults, **values, "system_id": system_id, "lifecycle_stage":"INTAKE", "risk_rating":"UNCLASSIFIED"})
        self.systems[system_id] = system
        self.audit(system_id, "USE_CASE_REGISTERED", "", "INTAKE", "Valid intake registered in the session inventory.", f"INT-{system_id}", "Business Owner")
        return system

    def classify_system(self, system_id: str, attributes: dict[str, Any]) -> ClassificationDecision:
        calculated = classify(attributes)
        decision = ClassificationDecision(calculated=calculated)
        self.classifications[system_id] = decision
        self.control_status[system_id] = {control: ControlImplementation(control) for control in calculated.mandatory_controls}
        self.audit(system_id, "CLASSIFICATION_COMPLETED", "INTAKE", "CLASSIFIED", f"Calculated tier {calculated.risk_tier} using rules v1.0.", f"CLS-{system_id}")
        return decision

    def propose_override(self, system_id: str, proposed_tier: str, rationale: str, requester_role: str) -> ClassificationOverride:
        decision = self.classifications[system_id]
        override = ClassificationOverride.propose(decision.calculated.risk_tier, proposed_tier, rationale, requester_role)
        decision.override = override
        self.audit(system_id, "CLASSIFICATION_OVERRIDE_PROPOSED", decision.calculated.risk_tier, proposed_tier, rationale, f"OVR-{system_id}", requester_role)
        return override

    def decide_override(self, system_id: str, approve: bool, approver_role: str) -> ClassificationOverride:
        decision = self.classifications[system_id]
        decision.override = decision.override.decide(approve, approver_role)  # type: ignore[union-attr]
        tier = effective_tier(decision)
        requirements = self.classification_for_tier(tier)
        self.control_status[system_id] = {control: self.control_status.get(system_id, {}).get(control, ControlImplementation(control)) for control in requirements.mandatory_controls}
        self.audit(system_id, "CLASSIFICATION_OVERRIDE_APPROVED" if approve else "CLASSIFICATION_OVERRIDE_REJECTED", decision.calculated.risk_tier, tier, decision.override.rationale, f"OVR-{system_id}", approver_role)
        return decision.override

    def classification_for_tier(self, tier: str) -> ClassificationResult:
        from assessments.risk_classification import load_rules
        rules = load_rules(); req = rules["tier_requirements"][tier]
        return ClassificationResult(0, tier, ("Effective tier requirements applied.",), tuple(req["controls"]), tuple(req["review_functions"]), req["approval"], tuple(req["validation"]), tuple(req["monitoring"]), int(req["revalidation_months"]))

    def add_finding(self, finding: Finding) -> Finding:
        if not any(item.finding_id == finding.finding_id for item in self.findings):
            self.findings.append(finding)
            self.audit(finding.system_id, "FINDING_CREATED", "", finding.status, finding.title, finding.finding_id, "Risk Owner")
        return finding

    def trigger_red_monitoring(self, system_id: str, result: MonitoringResult) -> Finding:
        self.monitoring_results[system_id] = result
        self.audit(system_id, "MONITORING_THRESHOLD_BREACHED", "GREEN", "RED", f"Breaches: {', '.join(result.breaches)}", f"MON-{system_id}", "Technical Owner")
        finding = self.add_finding(Finding(f"FND-MON-{system_id}", system_id, "MONITORING", "RED monitoring threshold breach", "Performance, drift or control threshold requires investigation.", "CRITICAL", "Risk Owner", datetime.now(timezone.utc).isoformat(), (date.today()+timedelta(days=30)).isoformat(), "OPEN", "Investigate root cause, validate controls and determine continued-use conditions.", "", "CTRL-014", "Approval review and event-driven revalidation required"))
        self.revalidation_status[system_id] = {"status":"REVALIDATION REQUIRED","type":"EVENT-DRIVEN","triggers":list(result.breaches),"decision":"INVESTIGATE"}
        self.audit(system_id, "REVALIDATION_TRIGGERED", "MONITORING", "REVALIDATION REQUIRED", "RED monitoring result requires event-driven revalidation.", f"REV-{system_id}", "Model Risk")
        return finding

    def approval_decision(self, system_id: str) -> ApprovalDecision:
        tier = effective_tier(self.classifications[system_id])
        decision = decide_approval(tier, self.assessments.get(system_id, {}), self.validations.get(system_id, ValidationRecord()), self.control_status.get(system_id, {}), [f for f in self.findings if f.system_id == system_id], self.systems[system_id].human_oversight_required)
        self.approvals[system_id] = decision
        return decision

    def snapshot(self) -> dict[str, Any]:
        return {"systems":{k:v.as_dict() for k,v in self.systems.items()},"findings":[asdict(f) for f in self.findings],"revalidation":self.revalidation_status}
