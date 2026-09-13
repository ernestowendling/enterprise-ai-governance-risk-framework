"""Connected Streamlit interface for the AI governance operating model."""
from __future__ import annotations
import csv
from dataclasses import asdict
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
import yaml
from assessments.ai_risk_assessment import evaluate_questionnaire, load_questions
from assessments.classification_override import effective_tier
from audit.audit_trail import verify_chain
from governance_workspace import ControlImplementation, GovernanceWorkspace, ValidationRecord
from inventory.service import load_inventory
from monitoring.drift_monitoring import interpret_psi, population_stability_index
from monitoring.fairness_monitoring import outcome_rates, requires_review, selection_rate_ratio
from monitoring.model_monitoring import evaluate
from oversight.human_oversight import determine_pattern

ROOT=Path(__file__).parent
st.set_page_config(page_title="Enterprise AI Governance",page_icon="◈",layout="wide")
st.markdown("""<style>.stApp{background:#f7f9fb;color:#17253b}[data-testid="stSidebar"]{background:#102a43}[data-testid="stSidebar"] *{color:#f5f8fa!important}.block-container{padding-top:2rem;max-width:1450px}h1,h2,h3{color:#16324f}.eyebrow{font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:#52758f;font-weight:700}[data-testid="stMetric"]{background:white;border:1px solid #dfe6ec;padding:1rem;border-radius:6px}</style>""",unsafe_allow_html=True)

def risk_attributes(system):
    raw=system.as_dict()
    return {**raw,"regulatory_relevance":"high" if raw["regulatory_scope"] else "low","model_complexity":"high" if raw["model_type"] in {"Gradient boosting","Large language model","Time-series ensemble"} else "medium","bias_impact":"high" if raw["sensitive_data"] and raw["decision_impact"]=="HIGH" else "medium","operational_criticality":"high" if raw["financial_impact"]=="HIGH" else "medium","cybersecurity_impact":"high" if raw["external_data"] or raw["sensitive_data"] else "medium","human_oversight":"present" if raw["human_oversight_required"] else "not_required"}

def make_workspace():
    systems,errors=load_inventory(ROOT/"inventory"/"ai_inventory.csv")
    if errors: raise ValueError("; ".join(errors))
    ws=GovernanceWorkspace(systems={x.system_id:x for x in systems}); ws.classify_system("AI-001",risk_attributes(ws.systems["AI-001"])); ws.audit_events.clear(); return ws

if "governance_workspace" not in st.session_state: st.session_state.governance_workspace=make_workspace()
ws:GovernanceWorkspace=st.session_state.governance_workspace
library=pd.DataFrame(yaml.safe_load((ROOT/"controls"/"control_library.yaml").read_text(encoding="utf-8"))["controls"])
thresholds=yaml.safe_load((ROOT/"monitoring"/"thresholds.yaml").read_text(encoding="utf-8")); monitoring=pd.read_csv(ROOT/"data"/"synthetic_monitoring.csv")
PAGES=["Executive Overview","AI Inventory","Register AI Use Case","Risk Classification","Risk Assessment","Control Requirements","Lifecycle & Approval","Monitoring","Bias & Fairness","Human Oversight","Findings & Exceptions","Regulatory Mapping","Swiss Banking Context","Audit Trail"]
st.sidebar.markdown("## ◈ AI Governance"); st.sidebar.caption("Connected governance workspace"); page=st.sidebar.radio("Governance view",PAGES); st.sidebar.caption("Synthetic reference implementation · v2.0")

def heading(title,text): st.markdown('<div class="eyebrow">Enterprise AI Governance & Risk</div>',unsafe_allow_html=True); st.title(title); st.caption(text)
def frame(): return pd.DataFrame([x.as_dict() for x in ws.systems.values()])
def choose():
    sid=st.selectbox("AI system",list(ws.systems),format_func=lambda x:f"{x} · {ws.systems[x].system_name}"); return sid,ws.systems[sid]

if page=="Executive Overview":
    heading(page,"Portfolio exposure and active governance decisions from the connected workspace."); inv=frame(); active=[f for f in ws.findings if f.status not in {"CLOSED","RISK ACCEPTED"}]; tiers=[effective_tier(ws.classifications[x.system_id]) if x.system_id in ws.classifications else x.risk_rating for x in inv.itertuples()]
    vals=[len(inv),sum(x in {"HIGH","CRITICAL"} for x in tiers),pd.to_datetime(inv.next_revalidation_date,errors="coerce").dt.date.lt(date.today()).sum(),len(active),sum(f.severity=="CRITICAL" for f in active),int(inv.exceptions.sum()),int((inv.vendor_or_internal=="vendor").sum()),len(ws.revalidation_status)]
    labels=["AI systems","High / critical","Overdue reviews","Open findings","Critical findings","Exceptions","Vendor AI","Revalidation"]
    for offset in (0,4):
        for c,l,v in zip(st.columns(4),labels[offset:offset+4],vals[offset:offset+4]): c.metric(l,v)
    a,b=st.columns(2); a.bar_chart(pd.Series(tiers).value_counts()); b.bar_chart(inv.lifecycle_stage.value_counts())
    if ws.monitoring_results.get("AI-001"): st.error("AI-001 · RED monitoring · critical finding open · event-driven revalidation required")
elif page=="AI Inventory":
    heading(page,"Authoritative session inventory for ownership, lifecycle and risk."); st.dataframe(frame(),width="stretch",hide_index=True); st.caption("Session changes do not modify repository CSV files.")
elif page=="Register AI Use Case":
    heading(page,"Create a usable session record before development or procurement.")
    with st.form("intake"):
        a,b=st.columns(2); name=a.text_input("System name"); unit=b.text_input("Business unit"); purpose=st.text_area("Business purpose and intended use"); owner=a.text_input("Business owner"); tech=b.text_input("Technical owner"); risk=a.text_input("Risk owner"); model=b.text_input("Model type",value="Rules-based"); impact=a.selectbox("Decision impact",["LOW","MEDIUM","HIGH"]); autonomy=b.selectbox("Autonomy",["LOW","MEDIUM","HIGH"]); customer=a.checkbox("Customer-facing"); personal=b.checkbox("Personal data"); submit=st.form_submit_button("Register use case")
    if submit:
        if not all([name,unit,purpose,owner,tech,risk]): st.error("Purpose and all accountable owners are required.")
        else:
            item=ws.register({"system_name":name,"business_unit":unit,"business_purpose":purpose,"description":purpose,"business_owner":owner,"technical_owner":tech,"risk_owner":risk,"model_type":model,"decision_impact":impact,"autonomy_level":autonomy,"customer_facing":customer,"personal_data":personal,"human_oversight_required":impact=="HIGH"}); st.success(f"{item.system_id} · {item.system_name} · INTAKE · Next action: risk classification")
elif page=="Risk Classification":
    heading(page,"Calculated classification is preserved; approved expert judgement sets the effective tier."); sid,system=choose(); decision=ws.classifications.get(sid)
    if st.button("Calculate and persist classification",disabled=decision is not None): ws.classify_system(sid,risk_attributes(system)); st.rerun()
    if decision:
        a,b,c=st.columns(3); a.metric("Calculated tier",decision.calculated.risk_tier); b.metric("Effective tier",effective_tier(decision)); c.metric("Score",decision.calculated.inherent_risk_score); st.dataframe(pd.DataFrame({"Rationale":decision.calculated.rationale}),hide_index=True,width="stretch")
        with st.expander("Governed expert override"):
            tier=st.selectbox("Proposed tier",["LOW","MODERATE","HIGH","CRITICAL"]); rationale=st.text_area("Override rationale"); requester=st.selectbox("Requester role",["AI Governance","Model Risk","Compliance","Business Owner"])
            if st.button("Propose override"):
                try: ws.propose_override(sid,tier,rationale,requester); st.rerun()
                except ValueError as e: st.error(str(e))
            if decision.override:
                st.json(asdict(decision.override)); approver=st.selectbox("Approver role",["Model Risk","AI Governance Committee","Executive Risk Committee","AI Governance"]); x,y=st.columns(2)
                if x.button("Approve",disabled=decision.override.status!="PROPOSED"):
                    try: ws.decide_override(sid,True,approver); st.rerun()
                    except ValueError as e: st.error(str(e))
                if y.button("Reject",disabled=decision.override.status!="PROPOSED"): ws.decide_override(sid,False,approver); st.rerun()
        st.caption("Policy-as-code supports expert judgement; it does not replace it.")
elif page=="Risk Assessment":
    heading(page,"Twenty-one evidence questions connect adverse answers to findings and gate implications."); sid,_=choose(); questions=load_questions(); answers={}
    with st.form("assessment"):
        for q in questions: answers[q.question_id]=st.selectbox(f"{q.question_id} · {q.question}",q.answer_options,help=f"{q.risk_domain} · Evidence: {q.evidence_expectation}")
        comments=st.text_area("Reviewer comments"); status=st.selectbox("Assessment status",["DRAFT","IN REVIEW","APPROVED","APPROVED WITH CONDITIONS","REJECTED","REVALIDATION REQUIRED"],index=2); submit=st.form_submit_button("Complete assessment")
    if submit:
        result=evaluate_questionnaire(sid,answers,comments,status); ws.assessments[sid]={**asdict(result),"findings":result.findings}; [ws.add_finding(f) for f in result.findings]; ws.audit(sid,"ASSESSMENT_COMPLETED","ASSESSMENT",status,f"Assessment produced {len(result.findings)} findings.",f"ASM-{sid}"); st.success(f"Persisted · residual {result.residual_risk} · {len(result.findings)} finding(s)")
    if sid in ws.assessments: st.json({k:v for k,v in ws.assessments[sid].items() if k!="findings"})
    st.caption("Structured decision aid only; expert risk, legal and compliance judgement remains necessary.")
elif page=="Control Requirements":
    heading(page,"Effective risk tier drives applicable controls and system-specific evidence status."); sid,_=choose()
    if sid not in ws.classifications: st.info("Complete classification first.")
    else:
        items=ws.control_status[sid]; required=library[library.control_id.isin(items)]; st.info(f"Calculated {ws.classifications[sid].calculated.risk_tier} · Effective {effective_tier(ws.classifications[sid])} · {len(items)} controls"); cid=st.selectbox("Control",list(items)); current=items[cid]; a,b=st.columns(2); status=a.selectbox("Status",["NOT STARTED","IN PROGRESS","EVIDENCED","FAILED","NOT APPLICABLE"]); owner=b.text_input("Control owner",current.control_owner or "Business Owner"); evidence=a.text_input("Evidence reference",current.evidence_reference); reviewer=b.text_input("Reviewer",current.reviewer or "AI Governance"); comments=st.text_area("Comments",current.comments)
        if st.button("Save evidence"): items[cid]=ControlImplementation(cid,status,owner,evidence,reviewer,date.today().isoformat(),comments); ws.audit(sid,"CONTROL_EVIDENCE_ADDED",current.status,status,f"{cid} updated.",evidence or cid,reviewer); st.rerun()
        st.dataframe(pd.DataFrame([asdict(x) for x in items.values()]),width="stretch",hide_index=True)
elif page=="Lifecycle & Approval":
    heading(page,"Decision rights consume effective tier, assessment, validation, controls, oversight and findings."); sid,system=choose(); record=ws.validations.get(sid,ValidationRecord()); statuses=["NOT STARTED","IN PROGRESS","VALIDATED","VALIDATED WITH CONDITIONS","FAILED","REVALIDATION REQUIRED"]; a,b=st.columns(2); vstatus=a.selectbox("Validation status",statuses,index=statuses.index(record.status)); role=b.text_input("Validator role",record.validator_role); scope=st.text_area("Validation scope",record.scope or "Intended use, performance, data, explainability, fairness, oversight and security"); evidence=st.text_input("Evidence reference",record.evidence_reference); conditions=st.text_input("Conditions; separated","; ".join(record.conditions)); accepted=st.checkbox("Conditions explicitly accepted and tracked",record.conditions_accepted)
    if st.button("Save validation"): ws.validations[sid]=ValidationRecord(vstatus,role,date.today().isoformat(),scope,"Fitness assessed subject to limitations.","Synthetic demonstration.",[x.strip() for x in conditions.split(";") if x.strip()],accepted,evidence); ws.audit(sid,"VALIDATION_COMPLETED","VALIDATION",vstatus,"Validation updated.",evidence or f"VAL-{sid}",role); st.rerun()
    if sid in ws.classifications:
        result=ws.approval_decision(sid); a,b,c=st.columns(3); a.metric("Effective tier",effective_tier(ws.classifications[sid])); b.metric("Authority",result.decision_authority); c.metric("Decision",result.decision); (st.success if result.decision.startswith("APPROVED") else st.error)("; ".join(result.rationale))
        if result.outstanding_conditions: st.warning("Conditions: "+"; ".join(result.outstanding_conditions))
        if st.button("Record approval",disabled=result.decision=="BLOCKED"): ws.audit(sid,"APPROVAL_GRANTED","APPROVAL",result.decision,"Authority accepted decision.",f"APR-{sid}",result.decision_authority); st.success("Approval recorded.")
    if sid in ws.revalidation_status: st.error(ws.revalidation_status[sid])
elif page=="Monitoring":
    heading(page,"A RED signal creates one shared finding, escalation and event-driven revalidation."); st.line_chart(monitoring.set_index("date")[["performance","fairness_ratio"]]); st.line_chart(monitoring.set_index("date")[["data_drift","output_drift","error_rate"]]); latest=monitoring.iloc[-1]; result=evaluate({k:float(latest[k]) for k in thresholds},thresholds)
    if st.button("Trigger AI-001 RED monitoring scenario"): ws.trigger_red_monitoring("AI-001",result); st.rerun()
    if ws.monitoring_results.get("AI-001"): st.error(f"RED · {', '.join(ws.monitoring_results['AI-001'].breaches)}"); st.json(ws.revalidation_status["AI-001"])
    psi=population_stability_index([.2,.3,.3,.2],[.1,.2,.3,.4]); st.metric("Illustrative PSI",f"{psi:.3f}",interpret_psi(psi))
elif page=="Bias & Fairness":
    heading(page,"A review signal, not an automated legal or ethical conclusion."); records=list(csv.DictReader((ROOT/"data"/"synthetic_fairness.csv").open(encoding="utf-8"))); records=[{**r,"approved":int(r["approved"])} for r in records]; rates=outcome_rates(records); ratio=selection_rate_ratio(rates); a,b=st.columns(2); a.bar_chart(pd.Series(rates)); b.metric("Selection-rate ratio",f"{ratio:.2f}");
    if requires_review(ratio): st.warning("Compliance and the Business Owner must investigate context, data, policy and model behaviour.")
elif page=="Human Oversight":
    heading(page,"Operational intervention, override, stop authority and retained evidence."); sid,system=choose(); plan=determine_pattern(system.decision_impact,system.autonomy_level,system.customer_facing); st.subheader(plan.pattern); st.json({"reviewer_role":plan.reviewer,"review_point":plan.review_point,"override_capability":plan.override_required,"stop_authority":plan.stop_authority,"escalation_path":"Reviewer → Business Owner → Risk Owner → Committee","evidence":plan.evidence}); st.metric("Control status",ws.control_status.get(sid,{}).get("CTRL-009",ControlImplementation("CTRL-009","NOT APPLICABLE")).status)
elif page=="Findings & Exceptions":
    heading(page,"Assessment and monitoring findings share one remediation population."); st.dataframe(pd.DataFrame([asdict(f) for f in ws.findings]),width="stretch",hide_index=True) if ws.findings else st.info("No findings yet.")
elif page=="Regulatory Mapping":
    heading(page,"Expectation → policy → process → control → evidence → responsible function."); mapping=yaml.safe_load((ROOT/"controls"/"regulatory_mapping.yaml").read_text(encoding="utf-8")); st.warning(mapping["disclaimer"]); [st.json(x) for x in mapping["mappings"]]
elif page=="Swiss Banking Context":
    heading(page,"Operating-model context for a Swiss regulated financial institution—not a compliance determination."); st.markdown((ROOT/"governance"/"swiss_banking_context.md").read_text(encoding="utf-8"))
else:
    heading(page,"One hash-chained sequence records the connected flagship journey."); st.dataframe(pd.DataFrame([asdict(e) for e in ws.audit_events]),width="stretch",hide_index=True) if ws.audit_events else st.info("Run a governance action to append evidence."); st.metric("Hash-chain integrity","VALID" if verify_chain(ws.audit_events) else "FAILED"); st.caption("Illustrative tamper evidence; production requires immutable storage, access control and retention.")
st.markdown("---"); st.caption("Synthetic reference implementation. Not legal advice or a production risk-management system.")

