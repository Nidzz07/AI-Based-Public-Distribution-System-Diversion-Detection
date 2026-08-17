"""Case endpoints: the ranked list, the case sheet, notes and recompute.

Cases are DERIVED, never seeded. seed.py writes raw readings and stops; the
first request to this router opens every case by running the engine over those
readings. That gives the project exactly one derivation path — the score a
judge sees on screen and the score an auditor re-derives six months later come
out of the same function, because there is no second place a score is made.

Re-running seed.py drops the cases table, and the next request rebuilds it.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine import complaints as complaints_engine
from ..engine import stats
from ..engine.audit import log, recompute as recompute_case
from ..engine.reconcile import reconcile
from ..engine.rulebook import load as load_rulebook
from ..engine.score import compute
from ..models import Case, Complaint, Cycle, Delivery, RuleHit, Shop, Transaction
from ..schemas import CaseDetail, CaseListItem, NoteIn, RecomputeOut

router = APIRouter(prefix="/cases", tags=["cases"])

# The cycle the demo scores. Earlier cycles exist for trend, but a case is
# opened against one allocation month.
SCORED_PERIOD = "2026-08"

# #4521 is C-0041 in docs/contract/case_detail.json and on the deck. Case ids
# are otherwise assigned in shop order; the demo case keeps the id already in
# print rather than the one its position would give it.
PINNED_CASE_IDS = {"4521": "C-0041"}


# ---------------------------------------------------------------------------
# Derivation. This router orchestrates the engine and assembles responses; the
# computation lives in engine/ — reconcile (F1), rulebook (F2), score (F3/F5),
# complaints (F4), stats (badge). Nothing is calculated inline here.
# ---------------------------------------------------------------------------


def _stored_inputs(db: Session, cycle: Cycle):
    """Everything the engine needs for one cycle, read back from the database.

    Transactions come back as distinct card ids only. reconcile() wants a
    sequence it can count distinct cards from, and pulling 40,000 full rows to
    count them would be the same answer at a hundred times the cost.
    """
    delivery = db.query(Delivery).filter(Delivery.cycle_id == cycle.id).first()
    txns = db.query(Transaction.card_id).filter(Transaction.cycle_id == cycle.id).distinct().all()
    return delivery, txns


def _derive(db: Session, shop: Shop, cycle: Cycle, rulebook: dict, anchor):
    """Run the full engine over one shop-cycle's stored inputs."""
    delivery, txns = _stored_inputs(db, cycle)
    features = reconcile(cycle, delivery, txns, shop)
    complaints_count = complaints_engine.link(db, shop.id, anchor=anchor, rulebook=rulebook)
    return features, compute(features, rulebook, complaints_count)


def _assign_case_ids(shop_ids):
    """C-0001, C-0002, ... in shop order, with the pinned demo id reserved."""
    reserved = set(PINNED_CASE_IDS.values())
    assigned = {}
    counter = 1
    for shop_id in shop_ids:
        if shop_id in PINNED_CASE_IDS:
            assigned[shop_id] = PINNED_CASE_IDS[shop_id]
            continue
        candidate = f"C-{counter:04d}"
        while candidate in reserved:
            counter += 1
            candidate = f"C-{counter:04d}"
        assigned[shop_id] = candidate
        counter += 1
    return assigned


def ensure_cases(db: Session) -> None:
    """Open a case for every shop's scored cycle, once, if none exist yet.

    Writes the case, its full trace (fired, passed AND skipped rows), the
    complaint links, and the audit events that make the case re-derivable.
    """
    if db.query(Case).count() > 0:
        return

    rulebook = load_rulebook()
    anchor = complaints_engine.ANCHOR
    version = rulebook.get("version")

    shops = db.query(Shop).order_by(Shop.id).all()
    cycles = {
        cycle.shop_id: cycle
        for cycle in db.query(Cycle).filter(Cycle.period == SCORED_PERIOD).all()
    }

    # Pass 1: derive everything, so the z-score has a population to compare
    # against before any case is written.
    derived = []
    for shop in shops:
        cycle = cycles.get(shop.id)
        if cycle is None:
            continue
        features, result = _derive(db, shop, cycle, rulebook, anchor)
        derived.append((shop, cycle, features, result))

    z_by_shop = stats.z_scores_from_features(
        {shop.id: features for shop, _, features, _ in derived}
    )
    case_ids = _assign_case_ids([shop.id for shop, _, _, _ in derived])

    # Pass 2: write.
    for shop, cycle, features, result in derived:
        case_id = case_ids[shop.id]
        bonus = result["complaint_bonus"]
        z_score = z_by_shop.get(shop.id)

        db.add(
            Case(
                id=case_id,
                shop_id=shop.id,
                cycle_id=cycle.id,
                score=result["score"],
                severity=result["severity"],
                status="OPEN",
                opened_at=anchor,
                gap_hop=result["gap_hop"],
                coverage_pct=result["coverage_pct"],
                rulebook_version=result["rulebook_version"],
                complaint_count=bonus["count"],
                complaint_window_days=bonus["window_days"],
                complaint_contribution=bonus["contribution"],
                z_score=z_score,
                z_confirms=stats.confirms(z_score),
                memo=result["memo"],
            )
        )

        for hit in result["rule_hits"]:
            db.add(RuleHit(case_id=case_id, **hit))

        log(
            db,
            case_id,
            "system",
            "CASE_OPENED",
            {
                "shop_id": shop.id,
                "period": cycle.period,
                "score": result["score"],
                "severity": result["severity"],
                "coverage_pct": result["coverage_pct"],
                "gap_hop": result["gap_hop"],
            },
            rulebook_version=version,
            at=anchor,
        )

        for hit in result["rule_hits"]:
            if hit["status"] != "fired":
                continue
            log(
                db,
                case_id,
                "system",
                "RULE_FIRED",
                {
                    "rule_id": hit["rule_id"],
                    "raw_value": hit["raw_value"],
                    "threshold": hit["threshold"],
                    "contribution": hit["contribution"],
                },
                rulebook_version=version,
                at=anchor,
            )

        # Attaches the matched complaints to this case. The count was already
        # derived in pass 1; this call is what writes the link.
        linked = complaints_engine.link(
            db, shop.id, anchor=anchor, case_id=case_id, rulebook=rulebook
        )
        if linked:
            log(
                db,
                case_id,
                "system",
                "COMPLAINT_LINKED",
                {
                    "count": linked,
                    "window_days": bonus["window_days"],
                    "contribution": bonus["contribution"],
                },
                rulebook_version=version,
                at=anchor,
            )

    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def _shop_ref(shop: Shop) -> dict:
    return {
        "id": shop.id,
        "name": shop.name,
        "block": shop.block,
        "lat": shop.lat,
        "lng": shop.lng,
    }


@router.get("", response_model=list[CaseListItem])
def list_cases(
    db: Session = Depends(get_db),
    severity: str | None = Query(default=None),
    district: str | None = Query(default=None),
):
    """The ranked case list. Highest score first — that IS the triage order."""
    ensure_cases(db)

    query = db.query(Case, Shop).join(Shop, Case.shop_id == Shop.id)
    if severity:
        query = query.filter(Case.severity == severity.upper())
    if district:
        query = query.filter(Shop.district == district)

    # Ties are broken by corroborating complaints, then by coverage. Two cases
    # on the same score are not equally urgent: the one the public has already
    # complained about seven times is the one to send an inspector to first,
    # and between two of those, the one we could evaluate more fully is the one
    # whose score we can stand behind.
    rows = query.order_by(
        Case.score.desc(),
        Case.complaint_count.desc(),
        Case.coverage_pct.desc(),
        Case.id,
    ).all()
    return [
        CaseListItem(
            case_id=case.id,
            shop=_shop_ref(shop),
            score=case.score,
            severity=case.severity,
            status=case.status,
            opened_at=case.opened_at,
            gap_hop=case.gap_hop,
            coverage_pct=case.coverage_pct,
        )
        for case, shop in rows
    ]


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """One case sheet: ladder, trace, coverage, complaints and memo.

    The score and trace are the STORED ones — what was decided on the day. Only
    the ladder's variances are re-derived here, and those are direct arithmetic
    on the stored readings, not a second scoring path.
    """
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    shop = db.get(Shop, case.shop_id)
    cycle = db.get(Cycle, case.cycle_id)
    delivery, txns = _stored_inputs(db, cycle)
    features = reconcile(cycle, delivery, txns, shop)

    hits = db.query(RuleHit).filter(RuleHit.case_id == case_id).order_by(RuleHit.id).all()
    linked = (
        db.query(Complaint)
        .filter(Complaint.linked_case_id == case_id)
        .order_by(Complaint.filed_at.desc())
        .all()
    )

    return CaseDetail(
        case_id=case.id,
        shop=_shop_ref(shop),
        score=case.score,
        severity=case.severity,
        status=case.status,
        opened_at=case.opened_at,
        cycle={
            "allocated_kg": cycle.allocated_kg,
            "dispatched_kg": cycle.dispatched_kg,
            "weighed_kg": cycle.weighed_kg,
            "dispensed_kg": cycle.dispensed_kg,
            "variance_dispatch_to_receipt": features["variance_dispatch_to_receipt"],
            "variance_receipt_to_counter": features["variance_receipt_to_counter"],
        },
        gap_hop=case.gap_hop,
        coverage_pct=case.coverage_pct,
        rulebook_version=case.rulebook_version,
        rule_hits=hits,
        complaint_bonus={
            "count": case.complaint_count,
            "window_days": case.complaint_window_days,
            "contribution": case.complaint_contribution,
        },
        complaints=linked,
        statistical={"z_score": case.z_score, "confirms": bool(case.z_confirms)},
        memo=case.memo or "",
    )


@router.post("/{case_id}/notes", status_code=201)
def add_note(case_id: str, note: NoteIn, db: Session = Depends(get_db)):
    """An inspector's field note. It lands in the audit trail and nowhere else."""
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    text = note.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="A note needs text")

    row = log(
        db,
        case_id,
        note.actor_role,
        "NOTE_ADDED",
        {"text": text},
        rulebook_version=case.rulebook_version,
    )
    db.commit()
    db.refresh(row)
    return {"id": row.id, "case_id": case_id, "event_type": row.event_type, "text": text}


@router.post("/{case_id}/recompute", response_model=RecomputeOut)
def recompute(case_id: str, db: Session = Depends(get_db)):
    """Re-derive the case from its STORED inputs and report what changed.

    Stored inputs only: the same cycle readings, the same delivery, the same
    complaints in the same window measured from the same anchor. Nothing is
    re-read from a live source and nothing about the case is rewritten — the
    answer is a comparison, and the comparison is written to the trail.
    """
    ensure_cases(db)

    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"No case {case_id}")

    shop = db.get(Shop, case.shop_id)
    cycle = db.get(Cycle, case.cycle_id)
    _, result = _derive(db, shop, cycle, load_rulebook(), case.opened_at)

    outcome = recompute_case(db, case, result)
    db.commit()
    return outcome
