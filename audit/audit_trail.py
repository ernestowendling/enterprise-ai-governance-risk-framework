"""Append-only, hash-chained illustrative governance audit trail."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    system_id: str
    event_type: str
    actor_role: str
    previous_status: str
    new_status: str
    rationale: str
    evidence_reference: str
    previous_hash: str = "GENESIS"
    event_hash: str = ""


def append_event(events: list[AuditEvent], **values: str) -> AuditEvent:
    values.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    values["previous_hash"] = events[-1].event_hash if events else "GENESIS"
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"))
    values["event_hash"] = hashlib.sha256(payload.encode()).hexdigest()
    event = AuditEvent(**values)
    events.append(event)
    return event


def verify_chain(events: list[AuditEvent]) -> bool:
    previous = "GENESIS"
    for event in events:
        values = asdict(event); supplied = values.pop("event_hash")
        if values["previous_hash"] != previous:
            return False
        expected = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if supplied != expected:
            return False
        previous = supplied
    return True
