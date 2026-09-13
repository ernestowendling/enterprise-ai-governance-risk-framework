"""Streamlit demonstration interface for the governance operating model."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from assessments.ai_risk_assessment import DOMAINS, assess_domain
from assessments.risk_classification import classify
from audit.audit_trail import append_event
from inventory.service import load_inventory
from lifecycle.lifecycle_engine import evaluate_transition
from monitoring.drift_monitoring import interpret_psi, population_stability_index
from monitoring.fairness_monitoring import outcome_rates, requires_review, selection_rate_ratio
from monitoring.model_monitoring import evaluate
from oversight.human_oversight import determine_pattern

ROOT = Path(__file__).parent
st.set_page_config(page_title="Enterprise AI Governance", page_icon="◈", layout="wide")
st.markdown("""<style>
:root{--ink:#17253b;--blue:#174d73;--line:#dfe6ec;--paper:#f7f9fb}
.stApp{background:#f7f9fb;color:var(--ink)} [data-testid="stSidebar"]{background:#102a43}
[data-testid="stSidebar"] *{color:#f5f8fa!important}.block-container{padding-top:2rem;max-width:1450px}
h1,h2,h3{color:#16324f;letter-spacing:-.02em}.eyebrow{font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:#52758f;font-weight:700}
.notice{background:#fff;border-left:4px solid #174d73;padding:1rem 1.2rem;border-radius:3px;box-shadow:0 1px 4px #dfe6ec}
[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:1rem;border-radius:6px}
</style>""", unsafe_allow_html=True)

systems, inventory_errors = load_inventory(ROOT / "inventory" / "ai_inventory.csv")
inventory = pd.DataFrame([s.as_dict() for s in systems])
controls_doc = yaml.safe_load((ROOT / "controls" / "control_library.yaml").read_text(encoding="utf-8"))
controls = pd.DataFrame(controls_doc["controls"])
thresholds = yaml.safe_load((ROOT / "monitoring" / "thresholds.yaml").read_text(encoding="utf-8"))
monitoring = pd.read_csv(ROOT / "data" / "synthetic_monitoring.csv")

PAGES = ["Executive Overview", "AI Inventory", "Register AI Use Case", "Risk Classification", "Risk Assessment", "Control Requirements", "Lifecycle & Approval", "Monitoring", "Bias & Fairness", "Human Oversight", "Findings & Exceptions", "Regulatory Mapping", "Audit Trail"]
st.sidebar.markdown("## ◈ AI Governance")
st.sidebar.caption("Enterprise control centre")
page = st.sidebar.radio("Governance view", PAGES)
st.sidebar.markdown("---")
st.sidebar.caption("Reference implementation · synthetic data · v1.0")

def heading(title: str, text: str) -> None:
    st.markdown('<div class="eyebrow">Enterprise AI Governance & Risk</div>', unsafe_allow_html=True)
    st.title(title); st.caption(text)

def flagship() -> dict:
    return inventory.loc[inventory.system_id == "AI-001"].iloc[0].to_dict()

def attributes_from(row: dict) -> dict:
    return {**row, "regulatory_relevance": "high" if row["regulatory_scope"] else "low", "model_complexity": "high" if row["model_type"] in {"Gradient boosting", "Large language model", "Time-series ensemble"} else "medium", "bias_impact": "high" if row["sensitive_data"] and row["decision_impact"] == "HIGH" else "medium", "operational_criticality": "high" if row["financial_impact"] == "HIGH" else "medium", "cybersecurity_impact": "high" if row["external_data"] or row["sensitive_data"] else "medium", "human_oversight": "present" if row["human_oversight_required"] else "not_required"}

if page == "Executive Overview":
    heading(page, "Management view of portfolio exposure, control health and intervention priorities.")
    high = inventory.risk_rating.isin(["HIGH", "CRITICAL"]).sum()
    overdue = pd.to_datetime(inventory.next_revalidation_date, errors="coerce").dt.date.lt(date.today()).sum()
    cols = st.columns(6)
    for col, label, value in zip(cols, ["AI systems", "High / critical", "Open findings", "Overdue revalidations", "Exceptions", "Vendor AI"], [len(inventory), high, int(inventory.open_findings.sum()), int(overdue), int(inventory.exceptions.sum()), int((inventory.vendor_or_internal == "vendor").sum())]):
        col.metric(label, value)
    left, right = st.columns(2)
    with left: st.subheader("Portfolio by risk tier"); st.bar_chart(inventory.risk_rating.value_counts())
    with right: st.subheader("Portfolio by lifecycle stage"); st.bar_chart(inventory.lifecycle_stage.value_counts())
    st.markdown('<div class="notice"><b>Management attention</b><br>AI-001 entered RED monitoring status in August. A finding, escalation and event-driven revalidation are required before continued risk acceptance.</div>', unsafe_allow_html=True)
elif page == "AI Inventory":
    heading(page, "Authoritative register for ownership, risk, lifecycle and review obligations.")
    tier = st.multiselect("Risk tier", sorted(inventory.risk_rating.unique()), default=sorted(inventory.risk_rating.unique()))
    st.dataframe(inventory[inventory.risk_rating.isin(tier)], use_container_width=True, hide_index=True)
    if inventory_errors: st.error("; ".join(inventory_errors))
elif page == "Register AI Use Case":
    heading(page, "Capture a use before development, procurement or material change.")
    with st.form("intake"):
        a,b = st.columns(2); name=a.text_input("System name"); unit=b.text_input("Business unit")
        purpose=st.text_area("Business purpose and intended use"); owner=a.text_input("Business owner"); tech=b.text_input("Technical owner")
        customer=a.checkbox("Customer-facing"); personal=b.checkbox("Personal data")
        impact=a.selectbox("Decision impact", ["LOW","MEDIUM","HIGH"]); autonomy=b.selectbox("Autonomy", ["LOW","MEDIUM","HIGH"])
        submitted=st.form_submit_button("Submit to intake")
    if submitted:
        if not all([name, unit, purpose, owner, tech]): st.error("Complete all ownership and purpose fields before submission.")
        else: st.success("Intake validated. In a production implementation this would create a versioned inventory and audit event.")
elif page == "Risk Classification":
    heading(page, "Transparent risk triage determines proportionate controls, review and approval.")
    chosen = st.selectbox("AI system", inventory.system_name, index=0)
    row=inventory.loc[inventory.system_name==chosen].iloc[0].to_dict(); result=classify(attributes_from(row))
    a,b,c=st.columns(3); a.metric("Inherent score", result.inherent_risk_score); b.metric("Calculated tier", result.risk_tier); c.metric("Approval", result.required_approval_level)
    st.subheader("Decision rationale"); st.dataframe(pd.DataFrame({"Triggered factor":result.rationale}), use_container_width=True, hide_index=True)
    st.caption("The score is an ordinal governance aid, not a probability of loss. Expert challenge and local risk appetite remain decisive.")
elif page == "Risk Assessment":
    heading(page, "Structured judgement across material risk domains, controls and residual exposure.")
    domain=st.selectbox("Risk domain", DOMAINS); inherent=st.selectbox("Inherent risk", ["LOW","MODERATE","HIGH","CRITICAL"], index=2); effectiveness=st.selectbox("Control effectiveness", ["INEFFECTIVE","PARTIALLY EFFECTIVE","EFFECTIVE"], index=1)
    assessment=assess_domain(domain,inherent,effectiveness); st.metric("Residual risk",assessment.residual_risk)
    if assessment.finding: st.warning(assessment.finding)
    st.text_area("Reviewer comments"); st.selectbox("Assessment status", ["DRAFT","IN REVIEW","APPROVED","APPROVED WITH CONDITIONS","REJECTED","REVALIDATION REQUIRED"])
elif page == "Control Requirements":
    heading(page, "Mandatory controls connect risk treatment to accountable evidence.")
    row=flagship(); result=classify(attributes_from(row)); required=controls[controls.control_id.isin(result.mandatory_controls)]
    st.info(f"{row['system_name']} · {result.risk_tier} · {len(required)} mandatory controls")
    st.dataframe(required[["control_id","control_name","control_domain","accountable_role","evidence_required","testing_frequency"]], use_container_width=True, hide_index=True)
elif page == "Lifecycle & Approval":
    heading(page, "Evidence-based gates prevent uncontrolled movement into production.")
    current=st.selectbox("Current stage", ["ASSESSMENT","VALIDATION","APPROVAL","PRE-PRODUCTION"], index=1); targets={"ASSESSMENT":"VALIDATION","VALIDATION":"APPROVAL","APPROVAL":"DEVELOPMENT","PRE-PRODUCTION":"PRODUCTION"}; target=targets[current]
    st.write(f"Requested transition: **{current} → {target}**")
    validation=st.checkbox("Independent validation complete", value=True); oversight=st.checkbox("Human-oversight control evidenced", value=True); approval=st.checkbox("Governance approval granted", value=True)
    decision=evaluate_transition(current,target,{"risk_tier":"CRITICAL","assessment_approved":True,"validation_status":"VALIDATED" if validation else "PENDING","human_oversight_required":True,"human_oversight_control":oversight,"approval_granted":approval})
    (st.success if decision.allowed else st.error)(("Gate passed: " if decision.allowed else "Gate blocked: ")+" ".join(decision.reasons))
elif page == "Monitoring":
    heading(page, "Operational signals are translated into findings, escalation and revalidation.")
    st.line_chart(monitoring.set_index("date")[["performance","fairness_ratio"]]); st.line_chart(monitoring.set_index("date")[["data_drift","output_drift","error_rate"]])
    latest=monitoring.iloc[-1]; result=evaluate({k:float(latest[k]) for k in thresholds}, thresholds)
    st.error(f"Latest status: {result.status} · Breaches: {', '.join(result.breaches)}")
    st.write("Governance response: " + " → ".join(result.actions))
    psi=population_stability_index([.20,.30,.30,.20],[.10,.20,.30,.40]); st.metric("Illustrative PSI",f"{psi:.3f}",interpret_psi(psi))
elif page == "Bias & Fairness":
    heading(page, "Outcome disparities prompt contextual investigation, not an automated legal conclusion.")
    records=list(csv.DictReader((ROOT/"data"/"synthetic_fairness.csv").open(encoding="utf-8"))); records=[{**r,"approved":int(r["approved"])} for r in records]
    rates=outcome_rates(records); ratio=selection_rate_ratio(rates); a,b=st.columns(2); a.bar_chart(pd.Series(rates,name="Outcome rate")); b.metric("Selection-rate ratio",f"{ratio:.2f}")
    if requires_review(ratio): st.warning("Review trigger breached. Compliance and the business owner must investigate data, policy, model behaviour and legitimate contextual factors.")
    st.caption("A single metric cannot establish whether treatment is legally or ethically fair.")
elif page == "Human Oversight":
    heading(page, "Oversight must provide competent review, effective override and stop authority.")
    plan=determine_pattern("HIGH","MEDIUM",True); st.subheader(plan.pattern); st.write({"Reviewer":plan.reviewer,"Review point":plan.review_point,"Override":plan.override_required,"Stop authority":plan.stop_authority,"Evidence":", ".join(plan.evidence)})
elif page == "Findings & Exceptions":
    heading(page, "Control gaps are owned, time-bound, escalated and independently visible.")
    findings=pd.DataFrame([{"ID":"FND-001","System":"AI-001","Severity":"CRITICAL","Finding":"Monitoring threshold breach","Owner":"Retail Lending Risk Owner","Due":"2026-09-30","Status":"OPEN"},{"ID":"FND-002","System":"AI-007","Severity":"HIGH","Finding":"Drift investigation overdue","Owner":"Payments Model Owner","Due":"2026-09-20","Status":"OPEN"}]); st.dataframe(findings,use_container_width=True,hide_index=True)
    st.subheader("Exceptions"); st.dataframe(inventory[inventory.exceptions>0][["system_id","system_name","exceptions","risk_owner"]],use_container_width=True,hide_index=True)
elif page == "Regulatory Mapping":
    heading(page, "External expectations are translated into policy, process, control and evidence.")
    mapping=yaml.safe_load((ROOT/"controls"/"regulatory_mapping.yaml").read_text(encoding="utf-8")); st.warning(mapping["disclaimer"])
    for item in mapping["mappings"]:
        with st.expander(item["framework"]): st.write(item)
else:
    heading(page, "Synthetic event history demonstrates traceability and tamper evidence.")
    events=[]
    for i,(kind,old,new,why,evidence) in enumerate([("USE_CASE_REGISTERED","","INTAKE","Business sponsor submitted use case","INT-001"),("CLASSIFICATION_COMPLETED","INTAKE","CLASSIFIED","Rules v1.0 assigned CRITICAL tier","CLS-001"),("VALIDATION_COMPLETED","VALIDATION","APPROVAL","Independent validation completed with conditions","VAL-001"),("APPROVAL_GRANTED","APPROVAL","PRODUCTION","Committee accepted residual risk conditions","APR-001"),("MONITORING_THRESHOLD_BREACHED","MONITORING","REVALIDATION","Drift and fairness thresholds breached","MON-2026-08")],1):
        append_event(events,event_id=f"EVT-{i:03}",timestamp=f"2026-0{min(i+2,9)}-01T09:00:00+00:00",system_id="AI-001",event_type=kind,actor_role="AI Governance" if i<3 else "Risk Owner",previous_status=old,new_status=new,rationale=why,evidence_reference=evidence)
    st.dataframe(pd.DataFrame([e.__dict__ for e in events]),use_container_width=True,hide_index=True)
    st.caption("Hash chaining is illustrative tamper evidence; production audit records require access control, immutability, retention and independent assurance.")

st.markdown("---"); st.caption("A reference implementation using synthetic data for demonstration purposes and not a production risk-management system.")
