"""F6 — Append-only audit trail and reproducibility.

Insert is the only operation this module performs. There is no helper here to
edit a row and none to remove one, and there must never be: a trail that can be
rewritten proves nothing, and the whole claim LEAKPROOF makes to an auditor is
that a score can be re-derived months later from what was written on the day.

Events: CASE_OPENED, RULE_FIRED (one row per fired rule), COMPLAINT_LINKED,
NOTE_ADDED, SCORE_RECOMPUTED.

recompute() is an observation, not a correction. It re-derives from the stored
inputs, records what it found next to what was stored, and leaves the stored
case exactly as it was. If the two disagree, that disagreement is the finding —
quietly overwriting the old score would destroy the evidence that anything
moved.

CLAUDE.md section 6 asks for a grep over audit code before any commit that
touches this file. The forbidden patterns are not spelled out here, because
this docstring would match them and the check would never come back clean.
tests/test_audit.py runs the same check automatically.
"""

import json
from datetime import datetime

from ..models import AuditLog

# The fields compared when a case is re-derived. Kept narrow on purpose: these
# are the numbers an officer acted on and an auditor would challenge.
COMPARED_FIELDS = ("score", "severity", "coverage_pct", "gap_hop", "rulebook_version")


def log(session, case_id, actor, action, detail=None, rulebook_version=None, at=None):
    """Append one event to the trail. The caller commits.

    detail is JSON-encoded rather than spread across columns so that an event
    written today stays readable after the payload shape of its event type has
    moved on — an old row must never need a migration to be understood.
    """
    row = AuditLog(
        case_id=case_id,
        event_type=action,
        actor_role=actor,
        payload=json.dumps(detail, default=str) if detail is not None else None,
        rulebook_version=rulebook_version,
        created_at=at or datetime.utcnow(),
    )
    session.add(row)
    return row


def summarise(case_or_result):
    """The comparable shape of a case, from either a stored row or a fresh derivation."""
    if isinstance(case_or_result, dict):
        return {field: case_or_result.get(field) for field in COMPARED_FIELDS}
    return {field: getattr(case_or_result, field, None) for field in COMPARED_FIELDS}


def recompute(session, case, recomputed, actor="auditor"):
    """Compare a stored case against a fresh derivation and record the result.

    Returns {stored, recomputed, identical}. Writes a SCORE_RECOMPUTED row and
    nothing else — the stored case is left standing whatever the comparison
    says. The caller commits.
    """
    stored_summary = summarise(case)
    fresh_summary = summarise(recomputed)
    identical = stored_summary == fresh_summary

    outcome = {
        "stored": stored_summary,
        "recomputed": fresh_summary,
        "identical": identical,
    }

    log(
        session,
        case.id,
        actor,
        "SCORE_RECOMPUTED",
        outcome,
        rulebook_version=fresh_summary.get("rulebook_version"),
    )
    return outcome
