from datetime import date

import pytest

from assessments.ai_risk_assessment import evaluate_questionnaire, load_questions
from assessments.classification_override import ClassificationDecision, ClassificationOverride, effective_tier
from assessments.risk_classification import classify
from audit.audit_trail import verify_chain
from governance_workspace import ControlImplementation, GovernanceWorkspace, ValidationRecord
from inventory.schema import AISystem
from lifecycle.lifecycle_engine import decide_approval
from monitoring.model_monitoring import MonitoringResult


def system_values():
    return {"system_id":"AI-001","system_name":"Loan AI","description":"Synthetic","business_unit":"Lending","business_owner":"Owner","technical_owner":"Tech","risk_owner":"Risk","model_type":"Model","ai_type":"Predictive AI","vendor_or_internal":"internal","provider":"Internal","deployment_status":"Registered","lifecycle_stage":"INTAKE","business_purpose":"Decision support","customer_facing":True,"decision_impact":"HIGH","autonomy_level":"MEDIUM","financial_impact":"HIGH","personal_data":True,"sensitive_data":True,"data_classification":"Restricted","external_data":False,"jurisdiction":"Switzerland","regulatory_scope":"Institution-specific","explainability_requirement":"HIGH","human_oversight_required":True,"validation_status":"NOT STARTED","risk_rating":"UNCLASSIFIED","residual_risk":"UNCLASSIFIED","last_assessment_date":"","next_revalidation_date":"","monitoring_frequency":"Monthly","open_findings":0,"exceptions":0,"retirement_date":""}


def high_result():
    return classify({"decision_impact":"high","financial_impact":"high","autonomy_level":"medium","personal_data":True,"sensitive_data":True,"regulatory_relevance":"high"})


def test_intake_creates_valid_session_system_and_audit():
    ws=GovernanceWorkspace(); item=ws.register({**system_values(),"system_id":"ignored"})
    assert item.system_id=="AI-001" and item.lifecycle_stage=="INTAKE"
    assert ws.systems[item.system_id] is item
    assert ws.audit_events[0].event_type=="USE_CASE_REGISTERED" and verify_chain(ws.audit_events)


def test_classification_persists_and_controls_are_created():
    ws=GovernanceWorkspace(systems={"AI-001":AISystem.from_dict(system_values())}); decision=ws.classify_system("AI-001",{"decision_impact":"high","financial_impact":"high","sensitive_data":True,"regulatory_relevance":"high"})
    assert ws.classifications["AI-001"] is decision
    assert set(ws.control_status["AI-001"])==set(decision.calculated.mandatory_controls)


def test_override_states_preserve_calculated_tier_and_change_effective_tier_only_when_approved():
    decision=ClassificationDecision(high_result()); original=decision.calculated.risk_tier
    assert effective_tier(decision)==original
    decision.override=ClassificationOverride.propose(original,"CRITICAL","Customer harm not fully represented.","AI Governance")
    assert effective_tier(decision)==original
    decision.override=decision.override.decide(False,"Model Risk")
    assert effective_tier(decision)==original
    decision.override=ClassificationOverride.propose(original,"CRITICAL","Customer harm not fully represented.","AI Governance").decide(True,"Model Risk")
    assert effective_tier(decision)=="CRITICAL" and decision.calculated.risk_tier==original


def test_override_requires_rationale_and_separate_approver():
    with pytest.raises(ValueError,match="rationale"): ClassificationOverride.propose("HIGH","CRITICAL","","AI Governance")
    proposed=ClassificationOverride.propose("HIGH","CRITICAL","Material context","AI Governance")
    with pytest.raises(ValueError,match="distinct"): proposed.decide(True,"AI Governance")


def test_effective_tier_drives_controls_authority_and_audit():
    ws=GovernanceWorkspace(systems={"AI-001":AISystem.from_dict(system_values())}); ws.classify_system("AI-001",{"decision_impact":"high","financial_impact":"high","sensitive_data":True,"regulatory_relevance":"high"}); ws.propose_override("AI-001","CRITICAL","Customer impact requires enhanced governance.","AI Governance"); ws.decide_override("AI-001",True,"Model Risk")
    assert len(ws.control_status["AI-001"])==22
    assert ws.classification_for_tier("CRITICAL").required_approval_level=="Executive Risk Committee"
    assert ws.audit_events[-1].event_type=="CLASSIFICATION_OVERRIDE_APPROVED"


def test_negative_assessment_answer_creates_finding_and_na_is_ignored():
    questions=load_questions(); answers={q.question_id:"NOT APPLICABLE" for q in questions}; answers["Q15"]="NO"
    result=evaluate_questionnaire("AI-001",answers)
    assert len(result.findings)==1 and result.findings[0].severity=="HIGH"
    assert result.residual_risk=="HIGH" and "blocked" in result.findings[0].lifecycle_impact.lower()
    clean=evaluate_questionnaire("AI-001",{q.question_id:"NOT APPLICABLE" for q in questions})
    assert clean.findings==() and clean.residual_risk=="LOW"


def test_strong_evidence_reduces_residual_risk_and_partial_is_moderate():
    questions=load_questions(); yes={q.question_id:"YES" for q in questions}; assert evaluate_questionnaire("AI-001",yes).residual_risk=="LOW"
    yes["Q04"]="PARTIAL"; assert evaluate_questionnaire("AI-001",yes).residual_risk=="MODERATE"


def test_failed_control_and_validation_conditions_govern_approval():
    controls={"CTRL-001":ControlImplementation("CTRL-001","FAILED"),"CTRL-009":ControlImplementation("CTRL-009","EVIDENCED","Owner","EVD")}; assessment={"assessment_status":"APPROVED"}
    blocked=decide_approval("CRITICAL",assessment,ValidationRecord(status="VALIDATED",evidence_reference="VAL"),controls,[],True); assert blocked.decision=="BLOCKED"
    controls["CTRL-001"]=ControlImplementation("CTRL-001","EVIDENCED","Owner","EVD")
    conditional=decide_approval("CRITICAL",assessment,ValidationRecord(status="VALIDATED WITH CONDITIONS",conditions=["Monthly review"],conditions_accepted=True,evidence_reference="VAL"),controls,[],True); assert conditional.decision=="APPROVED WITH CONDITIONS" and conditional.decision_authority=="Executive Risk Committee"
    not_accepted=decide_approval("CRITICAL",assessment,ValidationRecord(status="VALIDATED WITH CONDITIONS",conditions=["Monthly review"],conditions_accepted=False),controls,[],True); assert not_accepted.decision=="BLOCKED"


def test_red_monitoring_creates_one_finding_and_revalidation():
    ws=GovernanceWorkspace(systems={"AI-001":AISystem.from_dict(system_values())}); result=MonitoringResult("RED",("data_drift",),("Create finding",))
    ws.trigger_red_monitoring("AI-001",result); ws.trigger_red_monitoring("AI-001",result)
    assert len(ws.findings)==1
    assert ws.revalidation_status["AI-001"]["status"]=="REVALIDATION REQUIRED"
    assert {e.event_type for e in ws.audit_events}>={"MONITORING_THRESHOLD_BREACHED","FINDING_CREATED","REVALIDATION_TRIGGERED"}
    assert verify_chain(ws.audit_events)
