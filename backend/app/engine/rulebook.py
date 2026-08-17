"""F2 — Versioned YAML rulebook.

The rulebook is read from app/rules.yaml at runtime, every time. It is never
mirrored into Python constants: an officer edits the YAML, the next evaluation
uses it, and no code changes. That is the whole point of the feature — the
thresholds belong to the district supply office, not to us.

evaluate() returns one trace row per rule, in rulebook order, with three
possible states:

  fired    the condition was met                 contributes the rule's weight
  passed   we checked and it was within tolerance contributes 0
  skipped  the input was unavailable             contributes 0

"skipped" is not a polite "passed". A rule we could not evaluate is not a rule
that passed, and conflating the two is how audit systems lose credibility.
"""

from pathlib import Path

import yaml

# app/rules.yaml — the officer-editable file, one directory up from engine/.
RULES_PATH = Path(__file__).resolve().parent.parent / "rules.yaml"

# The comparisons the rulebook may express. Deliberately small: a rule an
# officer can read is worth more than an expression language they cannot.
OPERATORS = {
    "lt": lambda value, threshold: value < threshold,
    "lte": lambda value, threshold: value <= threshold,
    "gt": lambda value, threshold: value > threshold,
    "gte": lambda value, threshold: value >= threshold,
    "eq": lambda value, threshold: value == threshold,
}


def load(path=None):
    """Parse rules.yaml into a dict. No caching — see the module docstring."""
    path = Path(path) if path else RULES_PATH
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _with_unit(text, unit):
    """Attach the unit the way the frozen contract prints it: '-8.21%', '61 hrs'."""
    if not unit:
        return text
    return f"{text}{unit}" if unit == "%" else f"{text} {unit}"


def _format_raw_value(value, unit):
    """Render a measurement the way the trace should quote it.

    Percentages carry two decimals because that is the precision the ladder is
    reconciled at (-8.21%, not -8.2%). Everything else prints as measured, with
    a whole number staying whole: a 61.0-hour gap reads "61 hrs".
    """
    if unit == "%":
        return _with_unit(f"{value:.2f}", unit)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return _with_unit(str(value), unit)


def _format_threshold(threshold, unit):
    """Render a threshold verbatim as it stands in rules.yaml.

    Not reformatted to match the raw value: the trace should show the officer
    the number they actually typed ("-5.0%"), so that reading the row and
    reading the rulebook give the same answer.
    """
    return _with_unit(str(threshold), unit)


def evaluate(features, rulebook):
    """Evaluate every rule against one feature dict. Returns the full trace.

    Every rule produces a row, including the ones that passed and the ones we
    could not check — the trace is a record of what was examined, not a list of
    accusations.
    """
    return [_evaluate_rule(rule, features) for rule in rulebook.get("rules", [])]


def _evaluate_rule(rule, features):
    operator = rule["operator"]
    if operator not in OPERATORS:
        raise ValueError(
            f"rules.yaml rule '{rule['id']}' uses unknown operator '{operator}'. "
            f"Supported: {', '.join(sorted(OPERATORS))}."
        )

    unit = rule.get("unit")
    value = features.get(rule["field"])
    hit = {
        "rule_id": rule["id"],
        "label": rule["label"],
        "raw_value": None,
        "threshold": _format_threshold(rule["threshold"], unit),
        "contribution": 0,
        "severity": rule["severity"],
        "status": "skipped",
    }

    # Absent and None are the same finding: there was no reading to check.
    if value is None:
        return hit

    fired = OPERATORS[operator](value, rule["threshold"])
    hit["raw_value"] = _format_raw_value(value, unit)
    hit["status"] = "fired" if fired else "passed"
    hit["contribution"] = rule["weight"] if fired else 0
    return hit
