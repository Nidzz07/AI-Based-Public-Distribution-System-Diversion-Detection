"""Pydantic v2 response shapes.

These mirror docs/contract/case_detail.json key for key. The frontend builds
against that static file until Stage 3, so the two move together or not at all:
renaming a key here without renaming it there breaks the UI silently. If a
change looks necessary, flag it — do not do it on one side only.

The trace list is deliberately a flat list of rule hits including the ones that
passed and the ones we could not evaluate. A rule we could not check is not a
rule that passed, and the response must be able to say so.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["HIGH", "MEDIUM", "LOW"]
RuleSeverity = Literal["high", "medium", "low"]
RuleStatus = Literal["fired", "passed", "skipped"]
GapHop = Literal["allocation_to_dispatch", "dispatch_to_receipt", "receipt_to_counter"]


class ShopRef(BaseModel):
    """Just enough shop to render the case header and drop a map pin."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    block: str
    lat: float
    lng: float


class CycleSummary(BaseModel):
    """The four-hop ladder and the two variances the officer reads off it.

    Variances are percentages against the previous hop, rounded to 2 dp for
    display. Null on either kg field means the reading was unavailable, which
    is what makes the corresponding rule "skipped".
    """

    model_config = ConfigDict(from_attributes=True)

    allocated_kg: float
    dispatched_kg: float
    weighed_kg: float | None = None
    dispensed_kg: float | None = None
    variance_dispatch_to_receipt: float | None = None
    variance_receipt_to_counter: float | None = None


class RuleHitOut(BaseModel):
    """One trace row. raw_value carries its unit so the row reads as evidence.

    raw_value is null only when status is "skipped" — there was no reading to
    quote.
    """

    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    label: str
    raw_value: str | None = None
    threshold: str
    contribution: int
    severity: RuleSeverity
    status: RuleStatus


class ComplaintBonus(BaseModel):
    """F4 corroboration: complaints inside the window, and what they added."""

    model_config = ConfigDict(from_attributes=True)

    count: int
    window_days: int
    contribution: int


class ComplaintOut(BaseModel):
    """One grievance matched into the case's window by F4.

    Added to the contract alongside the same key in case_detail.json — the two
    moved together. PROJECT-BRIEF describes GET /api/cases/{case_id} as
    "case + trace + linked complaints", and the original contract file simply
    had no field for the third of those.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    filed_at: datetime
    source: str
    category: str
    text: str
    status: str


class Statistical(BaseModel):
    """Confirming badge only. `confirms` never moves the score."""

    model_config = ConfigDict(from_attributes=True)

    z_score: float | None = None
    confirms: bool


class CaseDetail(BaseModel):
    """GET /api/cases/{case_id} — the canonical response.

    Frozen shape: docs/contract/case_detail.json is the worked example for
    shop #4521 and is the authority on key names and ordering.
    """

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    shop: ShopRef
    # Display score, capped at 100 even though 130 is arithmetically possible.
    score: int
    severity: Severity
    status: str
    opened_at: datetime
    cycle: CycleSummary
    gap_hop: GapHop | None = None
    # Share of rule weight actually evaluated; skipped rules pull it down.
    coverage_pct: int
    rulebook_version: str
    rule_hits: list[RuleHitOut]
    complaint_bonus: ComplaintBonus
    # The complaints the bonus was counted from, so the officer can read the
    # grievances rather than take the count on trust.
    complaints: list[ComplaintOut] = []
    statistical: Statistical
    # engine/memo.py f-string template output. Not AI-generated.
    memo: str


class CaseListItem(BaseModel):
    """Row in the ranked list on the Officer and Inspector screens."""

    model_config = ConfigDict(from_attributes=True)

    case_id: str
    shop: ShopRef
    score: int
    severity: Severity
    status: str
    opened_at: datetime
    gap_hop: GapHop | None = None
    coverage_pct: int


# ---------------------------------------------------------------------------
# Operational shapes. NOT part of the frozen case-detail contract: these carry
# requests and the trail, and docs/contract/case_detail.json says nothing about
# them, so they are free to change without invariant 8 applying.
# ---------------------------------------------------------------------------


class NoteIn(BaseModel):
    """POST /api/cases/{case_id}/notes — an inspector's field note.

    There is no notes table. A note IS an audit event: writing it anywhere else
    would create a second place the case's history lives.
    """

    text: str
    actor_role: str = "inspector"


class AuditEventOut(BaseModel):
    """One row of the append-only trail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    event_type: str
    actor_role: str
    # Decoded from the stored JSON text so the client does not parse twice.
    payload: dict | None = None
    rulebook_version: str | None = None
    created_at: datetime


class RecomputeOut(BaseModel):
    """POST /api/cases/{case_id}/recompute — stored vs freshly re-derived.

    `identical` is the claim being made: the same inputs and the same rulebook
    still produce the same score. A false here is a finding, not an error.
    """

    stored: dict
    recomputed: dict
    identical: bool
