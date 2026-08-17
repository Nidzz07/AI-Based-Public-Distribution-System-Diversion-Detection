"""The API surface: ranked list, case sheet, notes, recompute, trail, rulebook.

Every test here runs against a COPY of backend/leakproof.db. The committed file
is the demo's evidence and a test run must not leave it in a state nobody chose
— least of all the audit trail, which cannot be tidied up afterwards.

test_case_detail_matches_the_frozen_contract turns CLAUDE.md invariant 8 from a
promise into a check: the contract file and the live response are compared key
for key, so neither can move without the other.
"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = BACKEND_DIR.parent / "docs" / "contract" / "case_detail.json"


@pytest.fixture
def client(tmp_path):
    scratch = tmp_path / "leakproof.db"
    shutil.copy(BACKEND_DIR / "leakproof.db", scratch)

    engine = create_engine(
        f"sqlite:///{scratch}", connect_args={"check_same_thread": False}, future=True
    )
    Session = sessionmaker(bind=engine, autoflush=False, future=True)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_case_detail_matches_the_frozen_contract(client):
    """Invariant 8, enforced: schemas.py and case_detail.json move together."""
    live = client.get("/api/cases/C-0041").json()
    frozen = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert live == frozen


def test_demo_case_scores_87_from_the_live_api(client):
    detail = client.get("/api/cases/C-0041").json()
    assert detail["score"] == 87
    assert detail["severity"] == "HIGH"
    assert detail["coverage_pct"] == 100
    assert detail["gap_hop"] == "dispatch_to_receipt"


def test_ranked_list_opens_on_the_demo_case(client):
    cases = client.get("/api/cases").json()
    assert len(cases) == 60
    assert cases[0]["case_id"] == "C-0041"
    assert [c["score"] for c in cases] == sorted((c["score"] for c in cases), reverse=True)


def test_the_three_fixtures_land_where_the_table_says(client):
    by_shop = {c["shop"]["id"]: c for c in client.get("/api/cases").json()}
    assert (by_shop["4521"]["score"], by_shop["4521"]["severity"]) == (87, "HIGH")
    assert (by_shop["4102"]["score"], by_shop["4102"]["coverage_pct"]) == (55, 83)
    assert by_shop["4788"]["gap_hop"] == "receipt_to_counter"


def test_severity_and_district_filters(client):
    high = client.get("/api/cases?severity=HIGH").json()
    assert high and all(c["severity"] == "HIGH" for c in high)

    barabanki = client.get("/api/cases?district=Barabanki").json()
    assert barabanki and len(barabanki) < 60

    both = client.get("/api/cases?severity=MEDIUM&district=Sitapur").json()
    assert all(c["severity"] == "MEDIUM" for c in both)


def test_trace_carries_all_three_row_states(client):
    """#4102 is the shop with a skipped rule; the trace must show all six rules."""
    hits = client.get("/api/cases/C-0010").json()["rule_hits"]
    assert len(hits) == 6
    statuses = {h["status"] for h in hits}
    assert statuses == {"fired", "passed", "skipped"}
    skipped = [h for h in hits if h["status"] == "skipped"]
    assert skipped[0]["rule_id"] == "gps_deviation"
    assert skipped[0]["raw_value"] is None


def test_unknown_case_is_404(client):
    assert client.get("/api/cases/C-9999").status_code == 404
    assert client.post("/api/cases/C-9999/recompute").status_code == 404


def test_opening_a_case_writes_the_trail(client):
    trail = client.get("/api/audit/C-0041").json()
    events = [row["event_type"] for row in trail]
    assert events[0] == "CASE_OPENED"
    assert events.count("RULE_FIRED") == 3  # one per fired rule
    assert "COMPLAINT_LINKED" in events
    assert [row["created_at"] for row in trail] == sorted(row["created_at"] for row in trail)


def test_note_appends_a_row_and_returns_201(client):
    before = len(client.get("/api/audit/C-0041").json())
    response = client.post(
        "/api/cases/C-0041/notes",
        json={"text": "Dealer absent at 11:40; stock register not produced.", "actor_role": "inspector"},
    )
    assert response.status_code == 201

    trail = client.get("/api/audit/C-0041").json()
    assert len(trail) == before + 1
    assert trail[-1]["event_type"] == "NOTE_ADDED"
    assert trail[-1]["actor_role"] == "inspector"
    assert "Dealer absent" in trail[-1]["payload"]["text"]


def test_empty_note_is_rejected(client):
    assert client.post("/api/cases/C-0041/notes", json={"text": "   "}).status_code == 422


def test_recompute_reproduces_the_score_from_stored_inputs(client):
    result = client.post("/api/cases/C-0041/recompute").json()
    assert result["identical"] is True
    assert result["stored"]["score"] == result["recomputed"]["score"] == 87

    trail = client.get("/api/audit/C-0041").json()
    assert trail[-1]["event_type"] == "SCORE_RECOMPUTED"
    # The case itself is untouched: a recompute observes, it does not correct.
    assert client.get("/api/cases/C-0041").json()["score"] == 87


def test_rulebook_endpoint_serves_the_yaml(client):
    book = client.get("/api/rulebook").json()
    assert book["version"] == "1.0.0"
    assert book["updated_by"] == "District Supply Office, Sitapur"
    assert len(book["rules"]) == 6
    assert sum(rule["weight"] for rule in book["rules"]) == 120
