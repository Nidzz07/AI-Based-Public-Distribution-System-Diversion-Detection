"""Synthetic data for LEAKPROOF. 60 shops: 3 fixtures + 57 generated.

Run:  python seed.py      (from backend/)

The data is synthetic. That is a declared scoping decision, not a gap — see
"Declared limitations" in PROJECT-BRIEF.md.

Two rules govern this file:

1. random.seed(4521) is set once, before any generation. Never remove it and
   never change it. Everything downstream — the demo, the fixture assertions,
   the screenshots in the deck — assumes this exact stream.
2. Seed writes RAW INPUTS ONLY. Variances, gap_hop, coverage_pct, scores and
   traces are derived by engine/ at evaluation time, so cases, rule_hits and
   audit_log are left empty here. Precomputing them would give the project two
   derivation paths that could disagree, which is precisely the failure mode
   the audit trail exists to rule out.

Scoping decisions inside this file, kept explicit:
  * Transactions are written for the scored cycle (2026-08) only. Earlier
    cycles carry ladder readings for the trend chart but no per-card rows.
  * Generated shops are held below the fixture archetypes in severity, so the
    demo case (#4521) stays top of the ranked list.
"""

import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from app.db import Base, SessionLocal, engine
from app.models import (
    Complaint,
    Cycle,
    Delivery,
    RulebookVersion,
    Shop,
    Transaction,
)

# Set before any generation. Do not move, do not change. See docstring.
random.seed(4521)

# The demo is frozen to a moment in time: this is when case C-0041 opens, and
# every complaint window is measured backwards from here.
ANCHOR = datetime(2026, 8, 14, 9, 12, 0)
SCORED_PERIOD = "2026-08"
HISTORY_PERIODS = ["2026-06", "2026-07"]
PERIOD_START = {
    "2026-06": datetime(2026, 6, 1),
    "2026-07": datetime(2026, 7, 1),
    "2026-08": datetime(2026, 8, 1),
}

RULES_PATH = Path(__file__).resolve().parent / "app" / "rules.yaml"

BLOCKS = {
    "Sitapur": [
        "Sitapur",
        "Biswan",
        "Misrikh",
        "Laharpur",
        "Mahmudabad",
        "Sidhauli",
        "Hargaon",
        "Maholi",
    ],
    "Barabanki": ["Barabanki", "Fatehpur", "Ramnagar", "Dewa", "Haidergarh"],
}

COMPLAINT_SOURCES = ["portal", "helpline", "walk_in"]
COMPLAINT_CATEGORIES = [
    "short_weight",
    "shop_closed",
    "overcharging",
    "quality",
    "epos_failure",
    "refused_entitlement",
]
COMPLAINT_TEXTS = {
    "short_weight": "Received less than the entitled quantity; dealer refused to re-weigh.",
    "shop_closed": "Shop found closed during notified distribution hours.",
    "overcharging": "Dealer charged above the notified issue price.",
    "quality": "Grain issued was of poor quality and partly spoiled.",
    "epos_failure": "ePoS machine reported failure but the entitlement was marked issued.",
    "refused_entitlement": "Entitlement refused despite a valid ration card.",
}

DEALER_FIRST = ["Ram", "Shyam", "Anil", "Sunita", "Kamla", "Rakesh", "Vinod", "Meena", "Suresh"]
DEALER_LAST = ["Verma", "Singh", "Yadav", "Gupta", "Mishra", "Pandey", "Sharma", "Rastogi"]


# ---------------------------------------------------------------------------
# Fixture shops — hardcoded to docs/contract/fixtures.md. Do not "improve".
# ---------------------------------------------------------------------------

# ration_cards is chosen so that txn_card_ratio lands exactly on the fixture
# value with a whole number of transacting cards (e.g. 0.88 * 1200 = 1056).
FIXTURES = [
    {
        "id": "4521",
        "name": "FPS Sitapur-12",
        "block": "Sitapur",
        "district": "Sitapur",
        "lat": 27.57,
        "lng": 80.68,
        "ration_cards": 1200,
        "dealer_name": "Ram Verma",
        "allocated_kg": 12000.0,
        "dispatched_kg": 12000.0,
        "weighed_kg": 11015.0,  # -8.21% against dispatch
        "dispensed_kg": 10980.0,  # -0.32% against receipt
        "delivery_gap_hours": 61,
        "gps_deviation_km": 3.4,
        "gps_available": True,
        "txn_card_ratio": 0.88,
        "hour_violations_month": 1,
        "complaints_in_window": 7,
        "complaints_outside_window": 2,  # proves the 14-day window is applied
    },
    {
        "id": "4102",
        "name": "FPS Barabanki-7",
        "block": "Barabanki",
        "district": "Barabanki",
        "lat": 26.93,
        "lng": 81.19,
        "ration_cards": 900,
        "dealer_name": "Sunita Singh",
        "allocated_kg": 8000.0,
        "dispatched_kg": 8000.0,
        "weighed_kg": 7512.0,  # -6.10%
        "dispensed_kg": 7490.0,  # -0.29%
        "delivery_gap_hours": 52,
        "gps_deviation_km": None,  # no GPS unit fitted -> gps_deviation skipped
        "gps_available": False,
        "txn_card_ratio": 0.71,
        "hour_violations_month": 1,
        "complaints_in_window": 2,  # below min_complaints, bonus must not fire
        "complaints_outside_window": 1,
    },
    {
        "id": "4788",
        "name": "FPS Hargaon-3",
        "block": "Hargaon",
        "district": "Sitapur",
        "lat": 27.65,
        "lng": 80.55,
        "ration_cards": 1000,
        "dealer_name": "Rakesh Yadav",
        "allocated_kg": 9000.0,
        "dispatched_kg": 9000.0,
        "weighed_kg": 8970.0,  # -0.33%
        "dispensed_kg": 8190.0,  # -8.70%, counter skim
        "delivery_gap_hours": 44,
        "gps_deviation_km": 0.8,
        "gps_available": True,
        "txn_card_ratio": 0.55,
        "hour_violations_month": 4,
        "complaints_in_window": 6,
        "complaints_outside_window": 0,
    },
]


def make_generated_shops(count: int) -> list[dict]:
    """57 shops with plausible values across four archetypes.

    Kept deliberately below the fixture archetypes: a generated shop may fire
    one or two rules, but the combination that produces #4521's 87 is reserved
    for the fixture so the ranked list opens on the demo case.
    """
    taken_ids = {f["id"] for f in FIXTURES}
    used_names: set[str] = set()
    shops: list[dict] = []

    for _ in range(count):
        shop_id = str(random.randint(4000, 4999))
        while shop_id in taken_ids:
            shop_id = str(random.randint(4000, 4999))
        taken_ids.add(shop_id)

        district = random.choice(["Sitapur", "Sitapur", "Barabanki"])
        block = random.choice(BLOCKS[district])
        name = f"FPS {block}-{random.randint(1, 40)}"
        while name in used_names:
            name = f"FPS {block}-{random.randint(1, 40)}"
        used_names.add(name)

        # Sitapur sits around 27.57N 80.68E; Barabanki around 26.93N 81.19E.
        base_lat, base_lng = (27.57, 80.68) if district == "Sitapur" else (26.93, 81.19)

        ration_cards = random.randrange(400, 1600, 50)
        allocated = float(random.randrange(4000, 14000, 500))

        # Paper diversion at the depot is rare; dispatch usually matches the
        # allocation order exactly.
        dispatched = allocated if random.random() > 0.10 else allocated - random.randrange(50, 300, 25)

        archetype = random.choices(
            ["clean", "transport", "counter", "sloppy"],
            weights=[62, 14, 14, 10],
        )[0]

        if archetype == "transport":
            receipt_pct = random.uniform(-9.0, -5.2)
            counter_pct = random.uniform(-0.6, -0.05)
            gap_hours = random.randint(49, 72)
            gps_km = round(random.uniform(2.1, 4.5), 1)
        elif archetype == "counter":
            receipt_pct = random.uniform(-1.0, -0.05)
            counter_pct = random.uniform(-9.5, -5.2)
            gap_hours = random.randint(18, 47)
            gps_km = round(random.uniform(0.1, 1.8), 1)
        elif archetype == "sloppy":
            # Nothing leaks; the shop is just badly run. Exercises the low-
            # severity rules without inflating the score.
            receipt_pct = random.uniform(-1.5, -0.1)
            counter_pct = random.uniform(-1.5, -0.1)
            gap_hours = random.randint(20, 47)
            gps_km = round(random.uniform(0.1, 1.9), 1)
        else:
            receipt_pct = random.uniform(-0.9, 0.2)
            counter_pct = random.uniform(-0.9, 0.1)
            gap_hours = random.randint(8, 44)
            gps_km = round(random.uniform(0.0, 1.6), 1)

        weighed = round(dispatched * (1 + receipt_pct / 100), 1)
        dispensed = round(weighed * (1 + counter_pct / 100), 1)

        # F5 coverage: a scale that failed to report, and vehicles with no GPS
        # unit. Both must degrade coverage rather than read as compliant.
        scale_offline = random.random() < 0.05
        gps_available = random.random() > 0.12

        if archetype == "sloppy":
            hour_violations = random.randint(3, 7)
            txn_ratio = round(random.uniform(0.45, 0.62), 2)
        else:
            hour_violations = random.randint(0, 2)
            txn_ratio = round(random.uniform(0.62, 0.96), 2)

        if archetype == "clean":
            complaints_in = random.randint(0, 2)
        else:
            complaints_in = random.randint(1, 5)

        shops.append(
            {
                "id": shop_id,
                "name": name,
                "block": block,
                "district": district,
                "lat": round(base_lat + random.uniform(-0.35, 0.35), 4),
                "lng": round(base_lng + random.uniform(-0.35, 0.35), 4),
                "ration_cards": ration_cards,
                "dealer_name": f"{random.choice(DEALER_FIRST)} {random.choice(DEALER_LAST)}",
                "allocated_kg": allocated,
                "dispatched_kg": float(dispatched),
                "weighed_kg": None if scale_offline else weighed,
                "dispensed_kg": None if scale_offline else dispensed,
                "delivery_gap_hours": gap_hours,
                "gps_deviation_km": gps_km if gps_available else None,
                "gps_available": gps_available,
                "txn_card_ratio": txn_ratio,
                "hour_violations_month": hour_violations,
                "complaints_in_window": complaints_in,
                "complaints_outside_window": random.randint(0, 2),
            }
        )

    return shops


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_shop(db, spec: dict) -> Shop:
    opens_hour = 9
    closes_hour = 17
    shop = Shop(
        id=spec["id"],
        name=spec["name"],
        block=spec["block"],
        district=spec["district"],
        lat=spec["lat"],
        lng=spec["lng"],
        ration_cards=spec["ration_cards"],
        opens_hour=opens_hour,
        closes_hour=closes_hour,
        dealer_name=spec["dealer_name"],
        created_at=datetime(2024, 4, 1),
    )
    db.add(shop)
    return shop


def write_scored_cycle(db, spec: dict) -> Cycle:
    """The 2026-08 cycle — the one the engine will score."""
    start = PERIOD_START[SCORED_PERIOD]
    cycle = Cycle(
        shop_id=spec["id"],
        period=SCORED_PERIOD,
        allocated_kg=spec["allocated_kg"],
        dispatched_kg=spec["dispatched_kg"],
        weighed_kg=spec["weighed_kg"],
        dispensed_kg=spec["dispensed_kg"],
        hour_violations_month=spec["hour_violations_month"],
        opened_on=start,
        closed_on=start + timedelta(days=27),
    )
    db.add(cycle)
    db.flush()  # need cycle.id for deliveries and transactions
    return cycle


def write_history_cycles(db, spec: dict) -> None:
    """Two prior cycles so the CaseDetail trend chart has something to plot.

    Prior months run close to clean for every shop — the demo narrative is a
    shop that has just started leaking, not one that always has.
    """
    for period in HISTORY_PERIODS:
        start = PERIOD_START[period]
        allocated = spec["allocated_kg"]
        weighed = round(allocated * (1 + random.uniform(-1.2, -0.05) / 100), 1)
        dispensed = round(weighed * (1 + random.uniform(-1.0, -0.05) / 100), 1)
        cycle = Cycle(
            shop_id=spec["id"],
            period=period,
            allocated_kg=allocated,
            dispatched_kg=allocated,
            weighed_kg=weighed,
            dispensed_kg=dispensed,
            hour_violations_month=random.randint(0, 2),
            opened_on=start,
            closed_on=start + timedelta(days=27),
        )
        db.add(cycle)
        db.flush()

        dispatch_ts = start + timedelta(days=4, hours=6)
        db.add(
            Delivery(
                cycle_id=cycle.id,
                shop_id=spec["id"],
                vehicle_no=vehicle_no(),
                route_id=f"R-{spec['block'][:3].upper()}-{random.randint(1, 9)}",
                dispatch_ts=dispatch_ts,
                arrival_ts=dispatch_ts + timedelta(hours=random.randint(10, 40)),
                gps_deviation_km=round(random.uniform(0.0, 1.5), 1),
                gps_available=True,
            )
        )


def write_delivery(db, spec: dict, cycle: Cycle) -> None:
    """The transport leg for the scored cycle.

    delivery_gap_hours is not stored as a number: it is arrival_ts minus
    dispatch_ts, so the trace can quote the two timestamps an officer would
    check against the consignment note.
    """
    dispatch_ts = PERIOD_START[SCORED_PERIOD] + timedelta(days=4, hours=6)
    db.add(
        Delivery(
            cycle_id=cycle.id,
            shop_id=spec["id"],
            vehicle_no=vehicle_no(),
            route_id=f"R-{spec['block'][:3].upper()}-{random.randint(1, 9)}",
            dispatch_ts=dispatch_ts,
            arrival_ts=dispatch_ts + timedelta(hours=spec["delivery_gap_hours"]),
            gps_deviation_km=spec["gps_deviation_km"],
            gps_available=spec["gps_available"],
        )
    )


def write_transactions(db, spec: dict, cycle: Cycle) -> int:
    """One collection per transacting card, for the scored cycle only.

    Distinct card count over shop.ration_cards is txn_card_ratio, so the count
    is derived from the target ratio rather than stored as a number.
    Quantities sum to exactly dispensed_kg — the ladder's fourth rung is the
    sum of what crossed the counter, and the two must not drift apart.
    """
    dispensed = cycle.dispensed_kg
    if dispensed is None:
        # ePoS data unavailable for this cycle: no rows, and the counter rules
        # will be skipped rather than passed.
        return 0

    n_txn = int(round(spec["txn_card_ratio"] * spec["ration_cards"]))
    if n_txn <= 0:
        return 0

    per_txn = round(dispensed / n_txn, 3)
    start = PERIOD_START[SCORED_PERIOD]
    outside_hours_left = spec["hour_violations_month"]

    rows = []
    running = 0.0
    for i in range(n_txn):
        # Last row absorbs the rounding remainder so the total is exact.
        qty = per_txn if i < n_txn - 1 else round(dispensed - running, 3)
        running = round(running + qty, 3)

        outside = outside_hours_left > 0 and random.random() < 0.02
        if outside:
            outside_hours_left -= 1
            hour = random.choice([6, 7, 8, 18, 19, 20])
        else:
            hour = random.randint(9, 16)

        rows.append(
            {
                "cycle_id": cycle.id,
                "shop_id": spec["id"],
                "card_id": f"UP{spec['id']}{i:05d}",
                "txn_ts": start
                + timedelta(days=random.randint(1, 25), hours=hour, minutes=random.randint(0, 59)),
                "quantity_kg": qty,
                "auth_mode": random.choices(
                    ["biometric", "otp", "manual_override"], weights=[88, 9, 3]
                )[0],
                "outside_hours": outside,
            }
        )

    db.bulk_insert_mappings(Transaction, rows)
    return len(rows)


def write_complaints(db, spec: dict) -> int:
    """Grievances against the shop.

    Complaints inside the 14-day window before ANCHOR are what F4 can count.
    Some shops also carry older complaints: they exist to prove the window is
    actually applied, not decorative.
    """
    rows = []
    for _ in range(spec["complaints_in_window"]):
        filed_at = ANCHOR - timedelta(
            days=random.randint(0, 13), hours=random.randint(0, 23), minutes=random.randint(0, 59)
        )
        rows.append(complaint_row(spec["id"], filed_at))

    for _ in range(spec["complaints_outside_window"]):
        filed_at = ANCHOR - timedelta(days=random.randint(20, 90), hours=random.randint(0, 23))
        rows.append(complaint_row(spec["id"], filed_at))

    for row in rows:
        db.add(Complaint(**row))
    return len(rows)


def complaint_row(shop_id: str, filed_at: datetime) -> dict:
    category = random.choice(COMPLAINT_CATEGORIES)
    return {
        "shop_id": shop_id,
        "filed_at": filed_at,
        "source": random.choice(COMPLAINT_SOURCES),
        "category": category,
        "text": COMPLAINT_TEXTS[category],
        "status": random.choices(["open", "closed"], weights=[70, 30])[0],
        "linked_case_id": None,  # engine/complaints.py links these, not seed
    }


def vehicle_no() -> str:
    return f"UP{random.randint(30, 42)}{random.choice('ABCDEFGHJK')}{random.randint(1000, 9999)}"


def write_rulebook_version(db) -> str:
    """Record the rulebook text in force at seed time.

    The YAML file stays the runtime source of truth; this row exists so a
    score can be re-derived against the exact text that produced it.
    """
    yaml_text = RULES_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(yaml_text)
    db.add(
        RulebookVersion(
            version=parsed["version"],
            updated_by=parsed["updated_by"],
            yaml_text=yaml_text,
            checksum=hashlib.sha256(yaml_text.encode("utf-8")).hexdigest(),
            loaded_at=ANCHOR - timedelta(days=30),
            is_active=True,
        )
    )
    return parsed["version"]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def seed() -> None:
    # A rerun rebuilds the file from scratch: same seed, same 60 shops.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    specs = FIXTURES + make_generated_shops(57)

    db = SessionLocal()
    try:
        version = write_rulebook_version(db)

        n_txn = 0
        n_complaints = 0
        for spec in specs:
            write_shop(db, spec)
            db.flush()
            write_history_cycles(db, spec)
            cycle = write_scored_cycle(db, spec)
            write_delivery(db, spec, cycle)
            n_txn += write_transactions(db, spec, cycle)
            n_complaints += write_complaints(db, spec)

        db.commit()

        shops = db.query(Shop).count()
        cycles = db.query(Cycle).count()
        deliveries = db.query(Delivery).count()

        print(f"rulebook version : {version}")
        print(f"shops            : {shops}")
        print(f"cycles           : {cycles}")
        print(f"deliveries       : {deliveries}")
        print(f"transactions     : {n_txn}")
        print(f"complaints       : {n_complaints}")
        print("cases/rule_hits/audit_log left empty - derived by engine/, not seeded")

        assert shops == 60, f"expected 60 shops, got {shops}"
    finally:
        db.close()


if __name__ == "__main__":
    seed()
