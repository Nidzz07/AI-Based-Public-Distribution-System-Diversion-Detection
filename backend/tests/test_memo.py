"""Plain-language memo.

The memo is an f-string template. It is not AI-generated and no test here
should ever be read as implying that it is — "template now, LLM later" is a
declared scoping decision.

The #4521 memo is asserted byte-for-byte against docs/contract/case_detail.json,
and the expected string is READ FROM that file rather than copied into this
module — the contract and the engine output cannot drift apart without this
test failing.
"""

import json
from pathlib import Path

from app.engine.memo import build_memo
from app.engine.reconcile import reconcile
from app.engine.score import compute

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "contract" / "case_detail.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _result(raw, rulebook):
    features = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
    return compute(features, rulebook, raw["complaints_in_window"])


def test_4521_memo_matches_the_frozen_contract_exactly(raw_4521, rulebook):
    assert _result(raw_4521, rulebook)["memo"] == CONTRACT["memo"]


def test_4521_memo_records_the_corroborating_complaints(raw_4521, rulebook):
    memo = _result(raw_4521, rulebook)["memo"]
    assert "7 complaints" in memo
    assert "14 days" in memo


def test_4102_memo_names_what_could_not_be_checked(raw_4102, rulebook):
    """F5 in prose: the officer must see the gap in the evidence, not just the score."""
    memo = _result(raw_4102, rulebook)["memo"]
    assert memo.startswith("Shop #4102 flagged MEDIUM (55/100):")
    assert "weighing shortfall of 6.1%" in memo
    assert "52-hour delivery gap" in memo
    assert "Not evaluated: Vehicle deviated from registered route" in memo
    assert "the reading was unavailable" in memo
    # No bonus fired, so no corroboration claim may appear.
    assert "complaints" not in memo


def test_4788_memo_describes_the_counter_skim(raw_4788, rulebook):
    memo = _result(raw_4788, rulebook)["memo"]
    assert memo.startswith("Shop #4788 flagged MEDIUM (53/100):")
    assert "counter shortfall of 8.7%" in memo
    assert "6 complaints" in memo


def test_memo_with_nothing_fired_says_so_plainly():
    memo = build_memo(
        shop_id="4999",
        score=0,
        severity="LOW",
        rule_hits=[],
        complaint_bonus={"count": 0, "window_days": 14, "contribution": 0},
    )
    assert memo == "Shop #4999 flagged LOW (0/100): no rules fired."


def test_memo_never_claims_to_be_generated(raw_4521, rulebook):
    memo = _result(raw_4521, rulebook)["memo"].lower()
    for overclaim in ("ai", "generated", "model", "llm"):
        assert overclaim not in memo.split()
