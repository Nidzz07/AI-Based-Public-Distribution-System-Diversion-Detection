"""F2 — versioned YAML rulebook, asserted against docs/contract/fixtures.md
and the frozen trace rows in docs/contract/case_detail.json.

Written before engine/rulebook.py had any logic.
"""

import pytest

from app.engine.reconcile import reconcile
from app.engine.rulebook import evaluate, load


def _hits_by_id(features, rulebook):
    return {h["rule_id"]: h for h in evaluate(features, rulebook)}


def _features(raw):
    return reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])


def test_load_reads_the_yaml_file_at_runtime(rulebook):
    assert rulebook["version"] == "1.0.0"
    assert rulebook["updated_by"] == "District Supply Office, Sitapur"
    assert rulebook["severity_bands"] == {"high": 75, "medium": 50}
    assert [r["id"] for r in rulebook["rules"]] == [
        "weighing_variance",
        "delivery_gap",
        "gps_deviation",
        "counter_variance",
        "transaction_mismatch",
        "operating_hours",
    ]
    assert rulebook["corroboration"]["complaint_bonus"] == {
        "min_complaints": 3,
        "window_days": 14,
        "weight": 10,
    }


def test_weights_total_120_and_bonus_is_10(rulebook):
    """Invariant 3: 120 + 10 = 130 possible. Do not renormalise to 100."""
    assert sum(r["weight"] for r in rulebook["rules"]) == 120
    assert rulebook["corroboration"]["complaint_bonus"]["weight"] == 10


def test_load_from_explicit_path_matches_default(rulebook):
    from app.engine import rulebook as rulebook_mod

    assert load(rulebook_mod.RULES_PATH) == rulebook


def test_every_rule_produces_exactly_one_trace_row(raw_4521, rulebook):
    hits = evaluate(_features(raw_4521), rulebook)
    assert len(hits) == len(rulebook["rules"])
    assert [h["rule_id"] for h in hits] == [r["id"] for r in rulebook["rules"]]
    for hit in hits:
        assert set(hit) == {
            "rule_id",
            "label",
            "raw_value",
            "threshold",
            "contribution",
            "severity",
            "status",
        }


def test_4521_trace_matches_the_frozen_contract(raw_4521, rulebook):
    """The three fired rows are copied from docs/contract/case_detail.json."""
    hits = _hits_by_id(_features(raw_4521), rulebook)

    assert hits["weighing_variance"] == {
        "rule_id": "weighing_variance",
        "label": "Weighing shortfall beyond tolerance",
        "raw_value": "-8.21%",
        "threshold": "-5.0%",
        "contribution": 30,
        "severity": "high",
        "status": "fired",
    }
    assert hits["delivery_gap"] == {
        "rule_id": "delivery_gap",
        "label": "Delivery-to-dispatch gap exceeded",
        "raw_value": "61 hrs",
        "threshold": "48 hrs",
        "contribution": 25,
        "severity": "high",
        "status": "fired",
    }
    assert hits["gps_deviation"] == {
        "rule_id": "gps_deviation",
        "label": "Vehicle deviated from registered route",
        "raw_value": "3.4 km",
        "threshold": "2.0 km",
        "contribution": 22,
        "severity": "high",
        "status": "fired",
    }


def test_4521_non_firing_rules_are_passed_and_contribute_zero(raw_4521, rulebook):
    hits = _hits_by_id(_features(raw_4521), rulebook)
    for rule_id, raw_value in (
        ("counter_variance", "-0.32%"),
        ("transaction_mismatch", "0.88"),
        ("operating_hours", "1"),
    ):
        assert hits[rule_id]["status"] == "passed"
        assert hits[rule_id]["contribution"] == 0
        assert hits[rule_id]["raw_value"] == raw_value


def test_4102_fires_two_rules(raw_4102, rulebook):
    hits = _hits_by_id(_features(raw_4102), rulebook)
    fired = {rid: h["contribution"] for rid, h in hits.items() if h["status"] == "fired"}
    assert fired == {"weighing_variance": 30, "delivery_gap": 25}


def test_4102_missing_gps_is_skipped_never_passed(raw_4102, rulebook):
    """Invariant 4. A rule we could not evaluate is not a rule that passed."""
    hit = _hits_by_id(_features(raw_4102), rulebook)["gps_deviation"]
    assert hit["status"] == "skipped"
    assert hit["status"] != "passed"
    assert hit["contribution"] == 0
    assert hit["raw_value"] is None
    # The threshold still shows, so the trace says WHAT we could not check.
    assert hit["threshold"] == "2.0 km"


def test_4788_fires_the_counter_skim_rules(raw_4788, rulebook):
    hits = _hits_by_id(_features(raw_4788), rulebook)
    fired = {rid: h["contribution"] for rid, h in hits.items() if h["status"] == "fired"}
    assert fired == {
        "counter_variance": 20,
        "transaction_mismatch": 15,
        "operating_hours": 8,
    }
    assert hits["counter_variance"]["raw_value"] == "-8.70%"
    assert hits["transaction_mismatch"]["raw_value"] == "0.55"
    assert hits["operating_hours"]["raw_value"] == "4"


def test_gte_operator_fires_exactly_on_the_threshold(rulebook):
    """operating_hours is `gte 3`: 3 fires, 2 does not."""
    features = {"hour_violations_month": 3}
    assert _hits_by_id(features, rulebook)["operating_hours"]["status"] == "fired"
    features = {"hour_violations_month": 2}
    assert _hits_by_id(features, rulebook)["operating_hours"]["status"] == "passed"


def test_lt_operator_does_not_fire_exactly_on_the_threshold(rulebook):
    """weighing_variance is `lt -5.0`: -5.0 itself is within tolerance."""
    features = {"variance_dispatch_to_receipt": -5.0}
    assert _hits_by_id(features, rulebook)["weighing_variance"]["status"] == "passed"
    features = {"variance_dispatch_to_receipt": -5.01}
    assert _hits_by_id(features, rulebook)["weighing_variance"]["status"] == "fired"


def test_a_field_absent_from_features_is_skipped(rulebook):
    """Absent and None are the same thing: we could not check."""
    for hit in evaluate({}, rulebook):
        assert hit["status"] == "skipped"
        assert hit["contribution"] == 0


def test_unknown_operator_is_refused_loudly(rulebook):
    broken = {**rulebook, "rules": [{**rulebook["rules"][0], "operator": "approximately"}]}
    with pytest.raises(ValueError):
        evaluate({"variance_dispatch_to_receipt": -8.21}, broken)
