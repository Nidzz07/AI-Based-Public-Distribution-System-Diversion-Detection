"""F1 — Four-hop reconciliation ladder.

allocated_kg -> dispatched_kg -> weighed_kg -> dispensed_kg

Two variances, two places grain can go:
  dispatched -> weighed    transport-leg diversion
  weighed    -> dispensed  counter skimming at the shop

reconcile() turns one cycle's raw readings into the flat feature dict the
rulebook evaluates. locate_gap() names the worse of the two hops, which is the
sentence an officer actually acts on: "985 kg opened between dispatch and
receipt — not the dealer, the transport leg."

F5 runs through this whole module: a reading we do not have is None, never 0.
A missing shop scale must degrade coverage, not report a 100% shortfall.
"""

DISPATCH_TO_RECEIPT = "dispatch_to_receipt"
RECEIPT_TO_COUNTER = "receipt_to_counter"


def _field(obj, name):
    """Read one field off a SQLAlchemy row, a SimpleNamespace or a dict.

    The engine is fed ORM rows in the app and plain objects in the tests; it
    should not care which, and should never explode on a shape it has not met.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _variance_pct(before, after):
    """Percentage change from one hop to the next, negative when grain is lost.

    Returns None — not 0.0 — when either reading is missing or the earlier hop
    is zero. "We could not measure this hop" and "this hop was clean" are
    different findings and the rest of the pipeline depends on telling them
    apart.
    """
    if before is None or after is None or before == 0:
        return None
    return round((after - before) / before * 100, 2)


def reconcile(cycle, delivery, txns, shop):
    """Derive the feature dict for one shop-cycle from its raw readings.

    Nothing here is stored precomputed: seed.py writes readings, this function
    derives, and it is the only place the variances come from.
    """
    dispatched_kg = _field(cycle, "dispatched_kg")
    weighed_kg = _field(cycle, "weighed_kg")
    dispensed_kg = _field(cycle, "dispensed_kg")

    return {
        "shop_id": _field(shop, "id"),
        "variance_dispatch_to_receipt": _variance_pct(dispatched_kg, weighed_kg),
        "variance_receipt_to_counter": _variance_pct(weighed_kg, dispensed_kg),
        "delivery_gap_hours": _delivery_gap_hours(delivery),
        "gps_deviation_km": _gps_deviation_km(delivery),
        "txn_card_ratio": _txn_card_ratio(txns, shop),
        "hour_violations_month": _field(cycle, "hour_violations_month"),
    }


def _delivery_gap_hours(delivery):
    """Hours between depot dispatch and shop arrival.

    None when the consignment is still in transit or its arrival scan never
    landed — an unrecorded arrival is not an instant delivery.
    """
    dispatch_ts = _field(delivery, "dispatch_ts")
    arrival_ts = _field(delivery, "arrival_ts")
    if dispatch_ts is None or arrival_ts is None:
        return None
    return round((arrival_ts - dispatch_ts).total_seconds() / 3600, 2)


def _gps_deviation_km(delivery):
    """Max distance off the registered route, or None if no GPS unit is fitted.

    gps_available is checked before the reading precisely so that "no device"
    stays distinguishable from "device reported 0.0 km" — the second is a
    passing rule, the first is a rule we could not evaluate at all.
    """
    if not _field(delivery, "gps_available"):
        return None
    return _field(delivery, "gps_deviation_km")


def _txn_card_ratio(txns, shop):
    """Distinct cards that collected, over cards attached to the shop.

    Distinct, not transaction count: one card collecting five times is one
    beneficiary served, and a shop can pad its transaction log.
    """
    ration_cards = _field(shop, "ration_cards")
    if txns is None or not ration_cards:
        return None
    distinct_cards = {_field(t, "card_id") for t in txns}
    distinct_cards.discard(None)
    return round(len(distinct_cards) / ration_cards, 2)


def locate_gap(features):
    """Name the hop where the most grain went missing.

    Whichever variance is more negative wins. A hop we could not measure is not
    a candidate — it is not "0% loss", it is unknown — so a case with only one
    measurable hop localises to that hop, and a case with neither returns None.

    Ties go to the earlier hop: if both hops lost the same share, the grain was
    already short when it reached the shop.
    """
    candidates = [
        (features.get("variance_dispatch_to_receipt"), DISPATCH_TO_RECEIPT),
        (features.get("variance_receipt_to_counter"), RECEIPT_TO_COUNTER),
    ]
    measurable = [c for c in candidates if c[0] is not None]
    if not measurable:
        return None
    return min(measurable, key=lambda c: c[0])[1]
