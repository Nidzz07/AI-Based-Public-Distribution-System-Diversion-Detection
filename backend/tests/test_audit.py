"""F6 — append-only audit trail and reproducibility.

Invariant 6: audit_log is insert-only. No in-place edit, no removal, no helper
anywhere that could perform either. CLAUDE.md asks for a grep before any commit
that touches audit code; test_audit_code_contains_no_mutation_calls runs that
same check automatically so it cannot be forgotten.
"""

import json
from datetime import datetime
from pathlib import Path

from app.engine.audit import log, recompute
from app.models import AuditLog, Case, Cycle

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# The two patterns from CLAUDE.md section 6, assembled from fragments so that
# this file — which lives at a path containing "audit" — does not itself match
# the grep it exists to enforce.
#
# Joined with str.join rather than with +: the compiler folds adjacent string
# literals into one constant, which would put the whole pattern back into
# __pycache__ and trip the grep on a build artifact instead of on real code.
FORBIDDEN_CALLS = ("".join((".dele", "te(")), "".join(("UPD", "ATE")))

AUDITED_SOURCES = (APP_DIR / "engine" / "audit.py", APP_DIR / "routers" / "audit.py")


def _case(db, case_id="C-0041", score=87):
    cycle = Cycle(
        shop_id="4521",
        period="2026-08",
        allocated_kg=12000.0,
        dispatched_kg=12000.0,
        weighed_kg=11015.0,
        dispensed_kg=10980.0,
        hour_violations_month=1,
        opened_on=datetime(2026, 8, 1),
    )
    db.add(cycle)
    db.flush()
    case = Case(
        id=case_id,
        shop_id="4521",
        cycle_id=cycle.id,
        score=score,
        severity="HIGH",
        status="OPEN",
        opened_at=datetime(2026, 8, 14, 9, 12),
        gap_hop="dispatch_to_receipt",
        coverage_pct=100,
        rulebook_version="1.0.0",
        complaint_count=7,
        complaint_window_days=14,
        complaint_contribution=10,
    )
    db.add(case)
    db.commit()
    return case


def test_log_inserts_one_row(db):
    _case(db)
    log(db, "C-0041", "officer", "CASE_OPENED", {"score": 87})
    db.commit()

    rows = db.query(AuditLog).all()
    assert len(rows) == 1
    assert rows[0].case_id == "C-0041"
    assert rows[0].event_type == "CASE_OPENED"
    assert rows[0].actor_role == "officer"
    assert json.loads(rows[0].payload) == {"score": 87}


def test_log_appends_and_leaves_earlier_rows_untouched(db):
    _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87})
    db.commit()
    first = db.query(AuditLog).one()
    first_id, first_payload, first_at = first.id, first.payload, first.created_at

    for rule_id in ("weighing_variance", "delivery_gap", "gps_deviation"):
        log(db, "C-0041", "system", "RULE_FIRED", {"rule_id": rule_id})
    db.commit()

    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    assert len(rows) == 4
    assert rows[0].id == first_id
    assert rows[0].payload == first_payload
    assert rows[0].created_at == first_at
    assert [r.event_type for r in rows[1:]] == ["RULE_FIRED"] * 3


def test_log_records_the_rulebook_in_force(db):
    _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87}, rulebook_version="1.0.0")
    db.commit()
    assert db.query(AuditLog).one().rulebook_version == "1.0.0"


def test_recompute_reports_identical_when_nothing_moved(db):
    case = _case(db)
    result = recompute(
        db,
        case,
        {
            "score": 87,
            "severity": "HIGH",
            "coverage_pct": 100,
            "gap_hop": "dispatch_to_receipt",
            "rulebook_version": "1.0.0",
        },
    )
    db.commit()

    assert result["identical"] is True
    assert result["stored"]["score"] == 87
    assert result["recomputed"]["score"] == 87


def test_recompute_reports_a_divergence_without_rewriting_the_case(db):
    """A recompute is an observation, not a correction. The stored case stands."""
    case = _case(db)
    result = recompute(
        db,
        case,
        {
            "score": 55,
            "severity": "MEDIUM",
            "coverage_pct": 83,
            "gap_hop": "dispatch_to_receipt",
            "rulebook_version": "1.0.0",
        },
    )
    db.commit()

    assert result["identical"] is False
    assert result["stored"]["score"] == 87
    assert result["recomputed"]["score"] == 55
    assert db.query(Case).one().score == 87


def test_recompute_writes_a_new_row_rather_than_touching_an_old_one(db):
    case = _case(db)
    log(db, "C-0041", "system", "CASE_OPENED", {"score": 87})
    db.commit()
    before = db.query(AuditLog).count()

    derived = {
        "score": 87,
        "severity": "HIGH",
        "coverage_pct": 100,
        "gap_hop": "dispatch_to_receipt",
        "rulebook_version": "1.0.0",
    }
    recompute(db, case, derived)
    db.commit()

    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    assert len(rows) == before + 1
    assert rows[-1].event_type == "SCORE_RECOMPUTED"
    assert json.loads(rows[-1].payload)["identical"] is True
    assert rows[0].event_type == "CASE_OPENED"


def test_audit_code_contains_no_mutation_calls():
    """Invariant 6, enforced in the suite rather than only in a pre-commit grep."""
    for source in AUDITED_SOURCES:
        text = source.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_CALLS:
            assert pattern not in text, f"{source.name} contains '{pattern}'"


def test_audit_module_exposes_no_mutation_helper():
    from app.engine import audit

    exported = [name for name in dir(audit) if not name.startswith("_")]
    for name in exported:
        assert "remov" not in name.lower()
        assert "purge" not in name.lower()
        assert "edit" not in name.lower()
