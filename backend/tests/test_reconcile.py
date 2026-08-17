"""F1 — four-hop reconciliation ladder, asserted against docs/contract/fixtures.md.

Written before engine/reconcile.py had any logic. Every number below is copied
from the fixture table, not from a run of the code.
"""

from app.engine.reconcile import locate_gap, reconcile


def test_4521_variances(raw_4521):
    f = reconcile(raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])
    assert f["variance_dispatch_to_receipt"] == -8.21
    assert f["variance_receipt_to_counter"] == -0.32


def test_4102_variances(raw_4102):
    f = reconcile(raw_4102["cycle"], raw_4102["delivery"], raw_4102["txns"], raw_4102["shop"])
    assert f["variance_dispatch_to_receipt"] == -6.10
    assert f["variance_receipt_to_counter"] == -0.29


def test_4788_variances(raw_4788):
    f = reconcile(raw_4788["cycle"], raw_4788["delivery"], raw_4788["txns"], raw_4788["shop"])
    assert f["variance_dispatch_to_receipt"] == -0.33
    assert f["variance_receipt_to_counter"] == -8.70


def test_delivery_gap_hours(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 61), (raw_4102, 52), (raw_4788, 44)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["delivery_gap_hours"] == expected


def test_txn_card_ratio_counts_distinct_cards(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 0.88), (raw_4102, 0.71), (raw_4788, 0.55)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["txn_card_ratio"] == expected


def test_hour_violations_passed_through(raw_4521, raw_4102, raw_4788):
    for raw, expected in ((raw_4521, 1), (raw_4102, 1), (raw_4788, 4)):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert f["hour_violations_month"] == expected


def test_gps_available_reports_the_reading(raw_4521, raw_4788):
    assert (
        reconcile(raw_4521["cycle"], raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])[
            "gps_deviation_km"
        ]
        == 3.4
    )
    assert (
        reconcile(raw_4788["cycle"], raw_4788["delivery"], raw_4788["txns"], raw_4788["shop"])[
            "gps_deviation_km"
        ]
        == 0.8
    )


def test_gps_unavailable_is_none_not_zero(raw_4102):
    """F5: 'no device fitted' must not read as 'device reported 0.0 km'."""
    f = reconcile(raw_4102["cycle"], raw_4102["delivery"], raw_4102["txns"], raw_4102["shop"])
    assert f["gps_deviation_km"] is None
    assert f["gps_deviation_km"] != 0


def test_locate_gap_picks_the_more_negative_hop(raw_4521, raw_4102, raw_4788):
    for raw, expected in (
        (raw_4521, "dispatch_to_receipt"),
        (raw_4102, "dispatch_to_receipt"),
        (raw_4788, "receipt_to_counter"),
    ):
        f = reconcile(raw["cycle"], raw["delivery"], raw["txns"], raw["shop"])
        assert locate_gap(f) == expected


def test_missing_weighed_kg_degrades_rather_than_zeroes(raw_4521):
    """An offline shop scale yields None variances, never a 100% shortfall."""
    cycle = raw_4521["cycle"]
    offline = type(cycle)(**{**vars(cycle), "weighed_kg": None})
    f = reconcile(offline, raw_4521["delivery"], raw_4521["txns"], raw_4521["shop"])
    assert f["variance_dispatch_to_receipt"] is None
    assert f["variance_receipt_to_counter"] is None


def test_missing_arrival_scan_leaves_gap_unknown(raw_4521):
    delivery = raw_4521["delivery"]
    in_transit = type(delivery)(**{**vars(delivery), "arrival_ts": None})
    f = reconcile(raw_4521["cycle"], in_transit, raw_4521["txns"], raw_4521["shop"])
    assert f["delivery_gap_hours"] is None


def test_locate_gap_returns_none_when_neither_hop_is_measurable():
    assert (
        locate_gap({"variance_dispatch_to_receipt": None, "variance_receipt_to_counter": None})
        is None
    )
