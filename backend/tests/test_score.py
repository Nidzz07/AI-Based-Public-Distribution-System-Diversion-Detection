"""F3 + F5 — composite score, reasoning trace, coverage.

These are the acceptance criteria. Every expected number comes from
docs/contract/fixtures.md; none of them is a recording of what the code did.

Invariant 1: #4521 scores EXACTLY 87 (30 + 25 + 22 + 10). If a change makes
it 86 or 88, the change is wrong, not the 87.
"""

import pytest

from app.engine.reconcile import locate_gap, reconcile
from app.engine.score import compute


def _features(raw):
    return reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])


def _result(raw, rulebook):
    return compute(_features(raw), rulebook, raw["complaints_in_window"])


# --- Acceptance: #4521 Sitapur ----------------------------------------------


def test_4521_scores_exactly_87(raw_4521, rulebook):
    assert _result(raw_4521, rulebook)["score"] == 87


def test_4521_is_high_with_full_coverage(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    assert result["severity"] == "HIGH"
    assert result["coverage_pct"] == 100
    assert result["gap_hop"] == "dispatch_to_receipt"


def test_4521_score_is_the_sum_of_fired_rules_plus_the_bonus(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    fired = [h["contribution"] for h in result["rule_hits"] if h["status"] == "fired"]
    assert sorted(fired, reverse=True) == [30, 25, 22]
    assert result["complaint_bonus"] == {"count": 7, "window_days": 14, "contribution": 10}
    assert sum(fired) + result["complaint_bonus"]["contribution"] == 87


# --- Acceptance: #4102 Barabanki --------------------------------------------


def test_4102_scores_exactly_55(raw_4102, rulebook):
    assert _result(raw_4102, rulebook)["score"] == 55


def test_4102_is_medium_with_reduced_coverage(raw_4102, rulebook):
    result = _result(raw_4102, rulebook)
    assert result["severity"] == "MEDIUM"
    assert result["coverage_pct"] == 83
    assert result["gap_hop"] == "dispatch_to_receipt"


def test_4102_gps_deviation_is_none(raw_4102):
    assert _features(raw_4102)["gps_deviation_km"] is None


def test_4102_bonus_does_not_fire_below_three_complaints(raw_4102, rulebook):
    assert _result(raw_4102, rulebook)["complaint_bonus"] == {
        "count": 2,
        "window_days": 14,
        "contribution": 0,
    }


def test_4102_coverage_counts_the_skipped_rule_not_the_weight(raw_4102, rulebook):
    """5 of 6 rules evaluated -> 83%. Skipped weight is not redistributed."""
    result = _result(raw_4102, rulebook)
    skipped = [h for h in result["rule_hits"] if h["status"] == "skipped"]
    assert [h["rule_id"] for h in skipped] == ["gps_deviation"]
    assert result["coverage_pct"] == round(5 / 6 * 100)


# --- Acceptance: #4788 Hargaon ----------------------------------------------


def test_4788_scores_exactly_53(raw_4788, rulebook):
    assert _result(raw_4788, rulebook)["score"] == 53


def test_4788_is_medium_and_localises_the_counter(raw_4788, rulebook):
    result = _result(raw_4788, rulebook)
    assert result["severity"] == "MEDIUM"
    assert result["gap_hop"] == "receipt_to_counter"
    assert result["coverage_pct"] == 100


def test_4788_fires_the_counter_ladder_plus_bonus(raw_4788, rulebook):
    result = _result(raw_4788, rulebook)
    fired = [h["contribution"] for h in result["rule_hits"] if h["status"] == "fired"]
    assert sorted(fired, reverse=True) == [20, 15, 8]
    assert result["complaint_bonus"]["contribution"] == 10


# --- Shape, bands and the display cap ---------------------------------------


def test_result_carries_the_full_trace_and_rulebook_version(raw_4521, rulebook):
    result = _result(raw_4521, rulebook)
    assert result["rulebook_version"] == "1.0.0"
    assert len(result["rule_hits"]) == len(rulebook["rules"])
    assert isinstance(result["memo"], str) and result["memo"]


def test_severity_bands(rulebook):
    """HIGH >= 75, MEDIUM >= 50, else LOW — read from rules.yaml."""
    bands = [
        (-90.0, 61, 3.4, 0.5, 10, 7, "HIGH"),  # everything fires
        (-6.0, 52, 0.1, 0.9, 0, 0, "MEDIUM"),  # 30 + 25 = 55
        (-1.0, 10, 0.1, 0.9, 0, 0, "LOW"),  # nothing fires
    ]
    for d2r, gap, gps, ratio, hours, complaints, expected in bands:
        features = {
            "variance_dispatch_to_receipt": d2r,
            "variance_receipt_to_counter": -0.1,
            "delivery_gap_hours": gap,
            "gps_deviation_km": gps,
            "txn_card_ratio": ratio,
            "hour_violations_month": hours,
        }
        assert compute(features, rulebook, complaints)["severity"] == expected


def test_display_score_caps_at_100_but_the_raw_total_survives(rulebook):
    """Invariant 3: 130 is arithmetically possible. Cap the display, keep the raw."""
    everything = {
        "variance_dispatch_to_receipt": -40.0,
        "variance_receipt_to_counter": -40.0,
        "delivery_gap_hours": 96,
        "gps_deviation_km": 9.9,
        "txn_card_ratio": 0.1,
        "hour_violations_month": 9,
    }
    result = compute(everything, rulebook, 7)
    assert result["score"] == 100
    assert result["score_raw"] == 130


def test_a_skipped_rule_never_contributes(rulebook):
    result = compute({}, rulebook, 0)
    assert result["score"] == 0
    assert result["coverage_pct"] == 0
    assert all(h["status"] == "skipped" for h in result["rule_hits"])


def test_zscore_is_not_an_input_to_the_score(raw_4521, rulebook):
    """Invariant 5: the statistical layer is a confirming badge, worth ZERO."""
    features = _features(raw_4521)
    baseline = compute(features, rulebook, 7)["score"]
    louder = compute({**features, "z_score": 9.9}, rulebook, 7)["score"]
    assert baseline == louder == 87


@pytest.mark.parametrize(
    "count,expected",
    [(0, 0), (2, 0), (3, 10), (7, 10)],
)
def test_bonus_threshold_is_three_complaints(rulebook, count, expected):
    result = compute({}, rulebook, count)
    assert result["complaint_bonus"]["contribution"] == expected
    assert result["complaint_bonus"]["window_days"] == 14
