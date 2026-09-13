from dataclasses import replace

from audit.audit_trail import append_event, verify_chain


def test_audit_chain_integrity_and_tamper_detection():
    events=[]
    common={"system_id":"AI-001","actor_role":"AI Governance","rationale":"Evidence reviewed","evidence_reference":"EVD-001"}
    append_event(events,event_id="EVT-1",timestamp="2026-01-01T00:00:00+00:00",event_type="REGISTERED",previous_status="",new_status="INTAKE",**common)
    append_event(events,event_id="EVT-2",timestamp="2026-01-02T00:00:00+00:00",event_type="CLASSIFIED",previous_status="INTAKE",new_status="CLASSIFIED",**common)
    assert verify_chain(events)
    events[0]=replace(events[0],rationale="Tampered")
    assert not verify_chain(events)
