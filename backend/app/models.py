"""The nine LEAKPROOF tables.

Column notes worth keeping in mind while reading:

* Raw inputs are stored; derived numbers are not. Variances, gap_hop,
  coverage_pct and score are produced by engine/ at evaluation time and only
  persisted on `cases` / `rule_hits` once a case has actually been opened.
  Nothing in seed.py precomputes them — one derivation path, one truth.
* "Unavailable" is modelled explicitly (gps_available, nullable weighed_kg /
  dispensed_kg) rather than as a zero or a magic number. F5 depends on being
  able to tell "we could not check" apart from "we checked and it was fine".
* audit_log is append-only. Nothing in this file, or anywhere else, may offer
  an update or delete path for it.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Shop(Base):
    """A fair-price shop (FPS). The unit an officer inspects."""

    __tablename__ = "shops"

    # Real FPS codes are strings, not counters — #4521 stays "4521".
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    block: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Denominator of txn_card_ratio: cards attached to this shop.
    ration_cards: Mapped[int] = mapped_column(Integer, nullable=False)

    # Licensed counter hours, used to judge hour_violations_month.
    opens_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    closes_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=17)

    dealer_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cycles: Mapped[list["Cycle"]] = relationship(back_populates="shop")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="shop")
    cases: Mapped[list["Case"]] = relationship(back_populates="shop")


class Cycle(Base):
    """One monthly allocation cycle for one shop — the four-hop ladder.

    allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg
    """

    __tablename__ = "cycles"
    __table_args__ = (UniqueConstraint("shop_id", "period", name="uq_cycle_shop_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    # "2026-08" — the allocation month this cycle belongs to.
    period: Mapped[str] = mapped_column(String(7), nullable=False)

    # Hop 1: government allocation order.
    allocated_kg: Mapped[float] = mapped_column(Float, nullable=False)
    # Hop 2: FCI depot weighbridge at dispatch.
    dispatched_kg: Mapped[float] = mapped_column(Float, nullable=False)
    # Hop 3: shop-side weighing scale at receipt. Nullable — a scale can be
    # offline, and that must degrade coverage rather than read as zero.
    weighed_kg: Mapped[float | None] = mapped_column(Float)
    # Hop 4: sum of ePoS counter dispensing. Nullable for the same reason.
    dispensed_kg: Mapped[float | None] = mapped_column(Float)

    # Counter sessions opened outside licensed hours during this cycle.
    hour_violations_month: Mapped[int | None] = mapped_column(Integer)

    opened_on: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_on: Mapped[datetime | None] = mapped_column(DateTime)

    shop: Mapped["Shop"] = relationship(back_populates="cycles")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="cycle")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="cycle")
    cases: Mapped[list["Case"]] = relationship(back_populates="cycle")


class Delivery(Base):
    """The transport leg: depot dispatch to shop arrival, with GPS."""

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    vehicle_no: Mapped[str] = mapped_column(String(24), nullable=False)
    route_id: Mapped[str] = mapped_column(String(24), nullable=False)

    # delivery_gap_hours = arrival_ts - dispatch_ts. arrival_ts is nullable:
    # a consignment can be in transit or its arrival scan can be missing.
    dispatch_ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_ts: Mapped[datetime | None] = mapped_column(DateTime)

    # Max distance between the vehicle track and its registered route.
    gps_deviation_km: Mapped[float | None] = mapped_column(Float)
    # False when the vehicle has no working GPS unit fitted. Keeps "no device"
    # distinguishable from "device reported 0.0 km deviation".
    gps_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    cycle: Mapped["Cycle"] = relationship(back_populates="deliveries")


class Transaction(Base):
    """One beneficiary collection at the ePoS counter."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    # Distinct card_id count over shop.ration_cards gives txn_card_ratio.
    card_id: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    txn_ts: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # ePoS auth mode, kept because a spike in manual overrides is the kind of
    # signal a later rule would want.
    auth_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="biometric")
    # True when the sale happened outside the shop's licensed hours.
    outside_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cycle: Mapped["Cycle"] = relationship(back_populates="transactions")


class Complaint(Base):
    """A public grievance filed against a shop. Feeds the F4 bonus."""

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)

    filed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # portal | helpline | walk_in
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    # Set by engine/complaints.py when a complaint falls inside a case window.
    # Null means unlinked, not unexamined.
    linked_case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id"), index=True)

    shop: Mapped["Shop"] = relationship(back_populates="complaints")


class Case(Base):
    """A scored, openable case. One cycle of one shop, evaluated once."""

    __tablename__ = "cases"

    # Human-facing identifier printed on the case sheet: "C-0041".
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    shop_id: Mapped[str] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), nullable=False, index=True)

    # Rule weights sum to 120 and the bonus adds 10; this is the DISPLAY score,
    # capped at 100. Do not renormalise the weights to make the cap disappear.
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)  # HIGH | MEDIUM | LOW
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Worst hop from locate_gap(): dispatch_to_receipt | receipt_to_counter |
    # allocation_to_dispatch.
    gap_hop: Mapped[str | None] = mapped_column(String(32))
    # Share of rules we were able to evaluate (rule-count based, not
    # weight-based). Skipped rules pull this down; they never count as passed.
    coverage_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Which rulebook produced this score — a case must stay re-derivable after
    # the rulebook moves on.
    rulebook_version: Mapped[str] = mapped_column(String(16), nullable=False)

    complaint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complaint_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    complaint_contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Badge only. Contributes ZERO to score, by design.
    z_score: Mapped[float | None] = mapped_column(Float)
    z_confirms: Mapped[bool | None] = mapped_column(Boolean)

    # Plain-language summary from engine/memo.py. An f-string template, not an
    # LLM, and never to be described as one.
    memo: Mapped[str | None] = mapped_column(Text)

    shop: Mapped["Shop"] = relationship(back_populates="cases")
    cycle: Mapped["Cycle"] = relationship(back_populates="cases")
    rule_hits: Mapped[list["RuleHit"]] = relationship(back_populates="case")


class RuleHit(Base):
    """One row of the reasoning trace: what we checked and what happened."""

    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)

    rule_id: Mapped[str] = mapped_column(String(48), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)

    # Stored as display strings ("-8.21%", "61 hrs") so the trace an auditor
    # reads months later is the trace we rendered on the day, units included.
    raw_value: Mapped[str | None] = mapped_column(String(48))
    threshold: Mapped[str] = mapped_column(String(48), nullable=False)

    contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)  # high | medium | low
    # fired | passed | skipped. "skipped" means the input was unavailable.
    status: Mapped[str] = mapped_column(String(8), nullable=False)

    case: Mapped["Case"] = relationship(back_populates="rule_hits")


class AuditLog(Base):
    """Append-only event trail. Insert only — never UPDATE, never DELETE.

    Events: CASE_OPENED, RULE_FIRED, COMPLAINT_LINKED, NOTE_ADDED,
    SCORE_RECOMPUTED. A recompute writes a new row; it does not touch old ones.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Who acted, from the role dropdown: officer | inspector | auditor | system.
    actor_role: Mapped[str] = mapped_column(String(16), nullable=False, default="system")
    # JSON-encoded event body, kept as text so an old row stays readable even
    # if the payload shape of that event type later changes.
    payload: Mapped[str | None] = mapped_column(Text)
    # Rulebook in force when the event was written, for re-derivation.
    rulebook_version: Mapped[str | None] = mapped_column(String(16))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )


class RulebookVersion(Base):
    """A snapshot of rules.yaml as loaded, so a score can be re-derived.

    The YAML file on disk is the runtime source of truth; this table records
    which text was in force when, and is written on load when the version or
    checksum is new.
    """

    __tablename__ = "rulebook_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)

    # Full YAML text plus its sha256, so "same version, edited file" is
    # detectable rather than silently accepted.
    yaml_text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    loaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
