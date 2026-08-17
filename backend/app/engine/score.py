"""F3 + F5 — Composite score, reasoning trace, coverage.

compute() is the single derivation path: features in, a scored case with its
full trace out. Nothing upstream precomputes a score, so a case opened today
and a case re-derived in six months run through this same function.

Invariants this module is answerable for:
  * #4521 scores EXACTLY 87 (30 + 25 + 22 + 10). Not 86, not 88.
  * Weights total 120 and the bonus adds 10, so 130 is arithmetically
    possible. The DISPLAY caps at 100; the raw total is kept as score_raw.
    Do not renormalise the weights to make the cap disappear.
  * A skipped rule contributes 0 and pulls coverage_pct down. It is never
    counted as passed, and its weight is never redistributed to the rules we
    could evaluate — that would quietly inflate a case built on less evidence.
  * The z-score is a confirming badge and contributes ZERO. It is not read
    here, and adding it to the feature dict must not move the score.
"""

from .memo import build_memo
from .reconcile import locate_gap
from .rulebook import evaluate


def compute(features, rulebook, complaints_count):
    """Score one shop-cycle against the rulebook. Returns the whole case body."""
    rule_hits = evaluate(features, rulebook)
    complaint_bonus = _complaint_bonus(rulebook, complaints_count)

    fired_total = sum(hit["contribution"] for hit in rule_hits if hit["status"] == "fired")
    score_raw = fired_total + complaint_bonus["contribution"]
    # Display cap. score_raw is preserved so an auditor can see that a case at
    # 100 was a 130 and not a bare pass of the band.
    score = min(score_raw, 100)

    severity = _severity(score, rulebook)
    shop_id = features.get("shop_id")

    return {
        "score": score,
        "score_raw": score_raw,
        "severity": severity,
        "coverage_pct": _coverage_pct(rule_hits),
        "gap_hop": locate_gap(features),
        "rulebook_version": rulebook.get("version"),
        "rule_hits": rule_hits,
        "complaint_bonus": complaint_bonus,
        "memo": build_memo(shop_id, score, severity, rule_hits, complaint_bonus),
    }


def _complaint_bonus(rulebook, complaints_count):
    """F4's corroboration bonus, read off the rulebook rather than hardcoded.

    complaints_count is the count ALREADY narrowed to the window by
    engine/complaints.py; window_days is echoed here so the case body can show
    what "recent" meant on the day it was scored.
    """
    config = rulebook.get("corroboration", {}).get("complaint_bonus", {})
    min_complaints = config.get("min_complaints", 0)
    weight = config.get("weight", 0)
    count = complaints_count or 0
    return {
        "count": count,
        "window_days": config.get("window_days"),
        "contribution": weight if count >= min_complaints else 0,
    }


def _coverage_pct(rule_hits):
    """Share of rules we were actually able to evaluate.

    Counted per rule, not per weight: coverage answers "how much of the
    rulebook did we get to run?", which is a question about checks performed,
    not about points available. #4102 misses one rule of six and reads 83%.
    """
    if not rule_hits:
        return 100
    evaluated = [hit for hit in rule_hits if hit["status"] != "skipped"]
    return round(len(evaluated) / len(rule_hits) * 100)


def _severity(score, rulebook):
    """HIGH / MEDIUM / LOW, with the band edges taken from rules.yaml.

    Banded on the displayed score: the officer's triage decision should follow
    the number printed on the case sheet.
    """
    bands = rulebook.get("severity_bands", {})
    if score >= bands.get("high", 75):
        return "HIGH"
    if score >= bands.get("medium", 50):
        return "MEDIUM"
    return "LOW"
