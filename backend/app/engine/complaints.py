"""F4 — Complaint auto-linking and the corroboration bonus.

Public grievances are the one signal in LEAKPROOF that does not come from a
machine. They are not evidence of diversion on their own, which is why they add
a bounded +10 rather than a rule weight: they corroborate a case the ladder
already built, they do not create one.

Thresholds (window_days, min_complaints, weight) come from rules.yaml, never
from constants in this module — an officer widening the window edits the YAML.
"""

from datetime import datetime, timedelta

from ..models import Complaint
from .rulebook import load

# The demo is frozen to a moment in time: this is when the case opens, and the
# window is measured backwards from here.
#
# Deliberately NOT datetime.now(). The seeded complaints sit at fixed offsets
# behind this instant, so a wall-clock anchor would quietly slide them out of
# the window as real days pass and #4521 would stop scoring 87 — a demo that
# decays overnight. Real deployments would pass the case's opened_at instead,
# which is exactly what the `anchor` argument is for.
ANCHOR = datetime(2026, 8, 14, 9, 12, 0)


def _bonus_config(rulebook=None):
    rulebook = rulebook if rulebook is not None else load()
    return rulebook.get("corroboration", {}).get("complaint_bonus", {})


def complaints_in_window(session, shop_id, anchor=None, window_days=None, rulebook=None):
    """Complaints filed against this shop inside the window, newest first.

    window_days defaults to the rulebook's value (currently 14) rather than to
    a literal here, so the YAML stays the single place the window is set.
    """
    if window_days is None:
        window_days = _bonus_config(rulebook).get("window_days", 14)
    anchor = anchor or ANCHOR
    opens = anchor - timedelta(days=window_days)

    return (
        session.query(Complaint)
        .filter(
            Complaint.shop_id == shop_id,
            Complaint.filed_at >= opens,
            Complaint.filed_at <= anchor,
        )
        .order_by(Complaint.filed_at.desc())
        .all()
    )


def link(session, shop_id, window_days=None, anchor=None, case_id=None, rulebook=None):
    """Match complaints to a case's window and return the count.

    The return value is exactly what score.compute() takes as complaints_count:
    F4 decides WHICH complaints are in scope, F3 decides what they are worth.

    Passing case_id attaches the matched complaints to that case. Complaints
    outside the window keep linked_case_id null — null means unlinked, not
    unexamined, and the ones we looked at and rejected stay in the table where
    an auditor can see the window did something.

    The caller commits. This function does not, so that linking a case and
    writing its audit rows land in one transaction or neither does.
    """
    matched = complaints_in_window(session, shop_id, anchor, window_days, rulebook)

    if case_id is not None:
        for complaint in matched:
            complaint.linked_case_id = case_id

    return len(matched)


def bonus_threshold(rulebook=None):
    """Minimum complaints the rulebook requires before the bonus applies."""
    return _bonus_config(rulebook).get("min_complaints", 3)
