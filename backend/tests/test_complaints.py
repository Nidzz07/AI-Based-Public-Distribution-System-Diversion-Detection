"""F4 — complaint window matching and the corroboration bonus.

Fixture expectations (docs/contract/fixtures.md): #4521 has 7 complaints in the
window, #4102 has 2 (below the minimum, so no bonus), #4788 has 6. #4521 and
#4102 also carry older complaints that must NOT be counted.
"""

from datetime import timedelta

from app.engine.complaints import ANCHOR, complaints_in_window, link
from app.engine.score import compute
from app.models import Complaint


def test_counts_match_the_fixture_table(db):
    assert link(db, "4521") == 7
    assert link(db, "4102") == 2
    assert link(db, "4788") == 6


def test_older_complaints_are_excluded(db):
    """The window is applied, not decorative — #4521 has 9 complaints in all."""
    assert db.query(Complaint).filter(Complaint.shop_id == "4521").count() == 9
    assert link(db, "4521") == 7


def test_window_days_comes_from_the_rulebook(db):
    """Default window is whatever rules.yaml says, currently 14 days."""
    from app.engine.rulebook import load

    assert load()["corroboration"]["complaint_bonus"]["window_days"] == 14
    # Widening the window past the older complaints picks them up.
    assert link(db, "4521", window_days=120) == 9


def test_a_narrow_window_counts_fewer(db):
    assert link(db, "4521", window_days=1) < 7


def test_complaints_in_window_returns_rows_newest_first(db):
    rows = complaints_in_window(db, "4521")
    assert len(rows) == 7
    assert [r.filed_at for r in rows] == sorted((r.filed_at for r in rows), reverse=True)
    assert all(r.filed_at >= ANCHOR - timedelta(days=14) for r in rows)


def test_link_attaches_the_case_id_to_matched_complaints_only(db):
    link(db, "4521", case_id="C-0041")
    db.commit()

    linked = db.query(Complaint).filter(Complaint.linked_case_id == "C-0041").all()
    assert len(linked) == 7
    assert all(c.shop_id == "4521" for c in linked)

    # Null means unlinked, not unexamined — the older two stay null.
    unlinked = (
        db.query(Complaint)
        .filter(Complaint.shop_id == "4521", Complaint.linked_case_id.is_(None))
        .count()
    )
    assert unlinked == 2


def test_link_without_a_case_id_counts_without_writing(db):
    assert link(db, "4521") == 7
    assert db.query(Complaint).filter(Complaint.linked_case_id.isnot(None)).count() == 0


def test_the_count_feeds_compute_directly(db, rulebook, raw_4521):
    """F4's output is exactly what compute() already takes as complaints_count."""
    from app.engine.reconcile import reconcile

    features = reconcile(
        raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"]
    )
    result = compute(features, rulebook, link(db, "4521"))
    assert result["complaint_bonus"] == {"count": 7, "window_days": 14, "contribution": 10}
    assert result["score"] == 87


def test_4102_stays_below_the_bonus_threshold(db, rulebook):
    result = compute({}, rulebook, link(db, "4102"))
    assert result["complaint_bonus"]["count"] == 2
    assert result["complaint_bonus"]["contribution"] == 0


def test_unknown_shop_has_no_complaints(db):
    assert link(db, "9999") == 0
