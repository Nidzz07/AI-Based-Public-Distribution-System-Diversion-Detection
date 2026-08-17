"""Raw inputs for the three contract fixtures.

These are RAW INPUTS only — the same columns seed.py writes. Variances,
fired rules, coverage_pct, gap_hop and score are never hardcoded here; the
tests derive them through engine/ so that a wrong derivation fails a test
instead of being handed the right answer.

Source of truth: docs/contract/fixtures.md.

SimpleNamespace stands in for a SQLAlchemy row on purpose — the engine reads
these by attribute, exactly as it will read a real Cycle/Delivery/Shop.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.engine import rulebook as rulebook_mod
from app.models import Complaint, Shop

# Case open time, and the anchor every complaint window is measured back from
# (docs/contract/fixtures.md).
CASE_OPENED_AT = datetime(2026, 8, 14, 9, 12, 0)

DISPATCH_TS = datetime(2026, 8, 10, 6, 0, 0)


def _cycle(shop_id, allocated, dispatched, weighed, dispensed, hour_violations):
    return SimpleNamespace(
        id=1,
        shop_id=shop_id,
        period="2026-08",
        allocated_kg=allocated,
        dispatched_kg=dispatched,
        weighed_kg=weighed,
        dispensed_kg=dispensed,
        hour_violations_month=hour_violations,
        opened_on=datetime(2026, 8, 1, 0, 0, 0),
        closed_on=None,
    )


def _delivery(shop_id, gap_hours, gps_deviation_km, gps_available):
    return SimpleNamespace(
        id=1,
        cycle_id=1,
        shop_id=shop_id,
        vehicle_no="UP32-AB-0001",
        route_id="R-01",
        dispatch_ts=DISPATCH_TS,
        arrival_ts=DISPATCH_TS + timedelta(hours=gap_hours),
        gps_deviation_km=gps_deviation_km,
        gps_available=gps_available,
    )


def _txns(shop_id, distinct_cards, duplicates=5):
    """distinct_cards distinct card_ids, plus repeat visits by the first few.

    The duplicates matter: txn_card_ratio counts DISTINCT cards, so a naive
    len(txns) implementation has to fail here rather than pass by luck.
    """
    rows = [
        SimpleNamespace(
            id=i,
            cycle_id=1,
            shop_id=shop_id,
            card_id=f"{shop_id}-CARD-{i:05d}",
            txn_ts=DISPATCH_TS + timedelta(hours=i % 72),
            quantity_kg=5.0,
            auth_mode="biometric",
            outside_hours=False,
        )
        for i in range(distinct_cards)
    ]
    rows.extend(
        SimpleNamespace(
            id=10_000 + i,
            cycle_id=1,
            shop_id=shop_id,
            card_id=f"{shop_id}-CARD-{i:05d}",
            txn_ts=DISPATCH_TS + timedelta(hours=i),
            quantity_kg=5.0,
            auth_mode="manual",
            outside_hours=False,
        )
        for i in range(duplicates)
    )
    return rows


def _shop(shop_id, name, block, ration_cards):
    return SimpleNamespace(
        id=shop_id,
        name=name,
        block=block,
        district="Sitapur",
        lat=27.57,
        lng=80.68,
        ration_cards=ration_cards,
        opens_hour=9,
        closes_hour=17,
        dealer_name=None,
    )


# --- #4521 Sitapur — transport diversion, everything available ---------------
RAW_4521 = {
    "shop": _shop("4521", "FPS Sitapur-12", "Sitapur", 1200),
    "cycle": _cycle("4521", 12000, 12000, 11015, 10980, 1),
    "delivery": _delivery("4521", 61, 3.4, True),
    "txns": _txns("4521", 1056),
    "complaints_in_window": 7,
}

# --- #4102 Barabanki — transport diversion, GPS unit not fitted -------------
RAW_4102 = {
    "shop": _shop("4102", "FPS Barabanki-07", "Barabanki", 900),
    "cycle": _cycle("4102", 8000, 8000, 7512, 7490, 1),
    # gps_available False, so gps_deviation_km must degrade to None -> skipped.
    "delivery": _delivery("4102", 52, None, False),
    "txns": _txns("4102", 639),
    "complaints_in_window": 2,
}

# --- #4788 Hargaon — counter skimming at the shop ---------------------------
RAW_4788 = {
    "shop": _shop("4788", "FPS Hargaon-03", "Hargaon", 1000),
    "cycle": _cycle("4788", 9000, 9000, 8970, 8190, 4),
    "delivery": _delivery("4788", 44, 0.8, True),
    "txns": _txns("4788", 550),
    "complaints_in_window": 6,
}


@pytest.fixture
def rulebook():
    """The real app/rules.yaml, loaded at runtime — never mirrored here."""
    return rulebook_mod.load()


@pytest.fixture
def raw_4521():
    return RAW_4521


@pytest.fixture
def raw_4102():
    return RAW_4102


@pytest.fixture
def raw_4788():
    return RAW_4788


# --- A throwaway database, not backend/leakproof.db --------------------------
#
# In-memory and rebuilt per test: the committed SQLite file is the demo's
# evidence, and a test suite that writes to it would leave the demo in a state
# nobody chose. Complaint timings mirror seed.py — some inside the window, some
# deliberately outside it, so a window check that silently matches everything
# fails a test instead of passing quietly.

COMPLAINTS_IN_WINDOW = {"4521": 7, "4102": 2, "4788": 6}
COMPLAINTS_OUTSIDE_WINDOW = {"4521": 2, "4102": 1, "4788": 0}


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, future=True)()

    for raw in (RAW_4521, RAW_4102, RAW_4788):
        shop = raw["shop"]
        session.add(
            Shop(
                id=shop.id,
                name=shop.name,
                block=shop.block,
                district=shop.district,
                lat=shop.lat,
                lng=shop.lng,
                ration_cards=shop.ration_cards,
                opens_hour=shop.opens_hour,
                closes_hour=shop.closes_hour,
                dealer_name=shop.dealer_name,
            )
        )
        for n in range(COMPLAINTS_IN_WINDOW[shop.id]):
            session.add(_complaint(shop.id, CASE_OPENED_AT - timedelta(days=n % 13, hours=1)))
        for n in range(COMPLAINTS_OUTSIDE_WINDOW[shop.id]):
            # 20+ days back: outside any 14-day window, by a wide margin.
            session.add(_complaint(shop.id, CASE_OPENED_AT - timedelta(days=20 + n * 10)))

    session.commit()
    yield session
    session.close()


def _complaint(shop_id, filed_at):
    return Complaint(
        shop_id=shop_id,
        filed_at=filed_at,
        source="portal",
        category="short_weight",
        text="Received less than the entitled quantity.",
        status="open",
        linked_case_id=None,
    )
