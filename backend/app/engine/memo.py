"""Plain-language memo.

THIS IS A TEMPLATE, NOT AN LLM. Nothing in this module calls a model or an
external API; it is a dict of f-string phrasings joined into a sentence. The
honest answer to "what generates the memo?" is "a template" — "template now,
LLM later" is a declared scoping decision, and the code stays truthful about it.

The memo says three things, in the order an officer needs them:
  1. what fired, each with its raw value and the threshold it crossed
  2. whether the public corroborated it
  3. what we could NOT check — F5 in prose, so the gap in the evidence is on
     the page next to the score rather than buried in a coverage badge
"""

# One phrasing per rule in rules.yaml, keyed by rule_id. A rule an officer adds
# to the YAML still gets a sentence (see _clause) — it just gets a generic one,
# because the rulebook is theirs to edit and the memo must not block on us.
PHRASINGS = {
    "weighing_variance": (
        lambda value, threshold: f"weighing shortfall of {abs(value):.1f}% "
        f"against a {abs(threshold):.0f}% tolerance"
    ),
    "delivery_gap": (
        lambda value, threshold: f"a {value:.0f}-hour delivery gap "
        f"against a {threshold:.0f}-hour limit"
    ),
    "gps_deviation": lambda value, threshold: f"a {value:g} km route deviation",
    "counter_variance": (
        lambda value, threshold: f"a counter shortfall of {abs(value):.1f}% "
        f"against a {abs(threshold):.0f}% tolerance"
    ),
    "transaction_mismatch": (
        lambda value, threshold: f"a transaction-to-card ratio of {value:.2f} "
        f"against a {threshold:g} floor"
    ),
    "operating_hours": (
        lambda value, threshold: f"{value:.0f} out-of-hours counter sessions "
        f"against a limit of {threshold:.0f}"
    ),
}


def _number(text):
    """Pull the number back out of a trace string: '-8.21%' -> -8.21, '61 hrs' -> 61.0."""
    if text is None:
        return None
    try:
        return float(text.split()[0].rstrip("%"))
    except (ValueError, IndexError):
        return None


def _clause(hit):
    value = _number(hit["raw_value"])
    threshold = _number(hit["threshold"])
    phrasing = PHRASINGS.get(hit["rule_id"])
    if phrasing is None or value is None or threshold is None:
        # Officer-added rule, or a rule whose value is not numeric: quote the
        # trace row verbatim rather than say nothing.
        return f"{hit['label'].lower()} ({hit['raw_value']} against {hit['threshold']})"
    return phrasing(value, threshold)


def _join(parts):
    """'A', 'A and B', 'A, B, and C' — read aloud in a hearing, not parsed."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def build_memo(shop_id, score, severity, rule_hits, complaint_bonus):
    """One paragraph an officer can act on and an auditor can re-derive."""
    subject = f"Shop #{shop_id}" if shop_id else "This shop"

    fired = [hit for hit in rule_hits if hit["status"] == "fired"]
    findings = _join([_clause(hit) for hit in fired]) if fired else "no rules fired"
    memo = f"{subject} flagged {severity} ({score}/100): {findings}."

    count = complaint_bonus.get("count", 0)
    if complaint_bonus.get("contribution"):
        plural = "" if count == 1 else "s"
        memo += (
            f" Corroborated by {count} complaint{plural} in the preceding "
            f"{complaint_bonus.get('window_days')} days."
        )

    skipped = [hit for hit in rule_hits if hit["status"] == "skipped"]
    if skipped:
        # Named, not counted. "We could not check the vehicle's route" is a
        # different sentence from "the vehicle's route was fine", and the memo
        # is where that distinction has to survive being read out loud.
        # Phrased as "Not evaluated: <label>" rather than "<label> could not be
        # checked", because a rule label is an assertion ("Vehicle deviated from
        # registered route") and must not read as a finding we never made.
        labels = _join([hit["label"] for hit in skipped])
        memo += f" Not evaluated: {labels} — the reading was unavailable."

    return memo
