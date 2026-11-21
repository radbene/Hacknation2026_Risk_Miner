"""S5: audit actions, proposal acceptance, bulk-confirm, learning loop, queue and review API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from riskminer.core.upsert import upsert_reviewable
from riskminer.ids import make_id
from riskminer.models import Event, Procedure, Project, ProjectProcedure, Review, Rule


@pytest.fixture
def tx(db_available):
    """Session inside an outer transaction that is always rolled back (API commits become savepoints)."""
    if not db_available:
        pytest.skip("no database")
    from sqlalchemy.orm import Session

    from riskminer.core.db import engine

    conn = engine.connect()
    outer = conn.begin()
    s = Session(bind=conn, join_transaction_mode="create_savepoint", autoflush=False, expire_on_commit=False)
    try:
        yield s
    finally:
        s.close()
        outer.rollback()
        conn.close()


@pytest.fixture
def client(tx):
    from riskminer.api.main import app
    from riskminer.core.db import get_session

    app.dependency_overrides[get_session] = lambda: tx
    try:
        yield TestClient(app, headers={"X-User": "ekspert_test"})
    finally:
        app.dependency_overrides.pop(get_session, None)


def _project(s, code="T-REV-1"):
    pid = make_id("project", code)
    upsert_reviewable(s, Project, {"id": pid, "code": code, "title": "Budowa sieci wodociągowej",
                                   "confidence": 0.9, "method": "import"})
    return pid


def _link(s, pid, ocid="ocds-T-1", conf=1.0, method="ocid"):
    prid = make_id("procedure", ocid)
    s.add(Procedure(id=prid, ocid=ocid, bzp_number=f"2024/BZP {ocid[-3:]}", title="Sieć wod. " + ocid))
    s.flush()
    lid = make_id("project_procedure", pid, prid, None)
    upsert_reviewable(s, ProjectProcedure, {"id": lid, "project_id": pid, "procedure_id": prid,
                                            "method": method, "confidence": conf})
    return lid, prid


def test_accept_edit_reject_reopen_history(tx):
    from riskminer.review import audit, learning

    pid = _project(tx)
    rev = audit.apply_action(tx, "project", pid, "accept", "ekspert")
    p = tx.get(Project, pid)
    assert p.status == "approved" and p.reviewed_by == "ekspert"
    assert rev.before["status"] == "proposed" and rev.after["status"] == "approved"

    rev = audit.apply_action(tx, "project", pid, "edit", "ekspert", {"title": "Rozbudowa sieci", "part_no": "2"},
                             "korekta tytułu")
    assert p.title == "Rozbudowa sieci" and p.part_no == 2 and p.status == "edited"
    assert rev.before["title"] == "Budowa sieci wodociągowej" and rev.after["title"] == "Rozbudowa sieci"

    with pytest.raises(audit.ReviewError):
        audit.apply_action(tx, "project", pid, "edit", "ekspert", {"status": "approved"})

    # expert data is never overwritten by a rerun
    assert upsert_reviewable(tx, Project, {"id": pid, "code": "T-REV-1", "title": "maszyna"}) == "proposal"
    assert p.title == "Rozbudowa sieci" and p.proposal == {"title": "maszyna"}

    audit.apply_action(tx, "project", pid, "reject", "ekspert", comment="nie ten projekt")
    assert learning.is_blacklisted(tx, "project", pid)
    audit.apply_action(tx, "project", pid, "reopen", "ekspert")
    assert not learning.is_blacklisted(tx, "project", pid) and p.status == "proposed"

    rows, total = audit.history(tx, object_id=pid)
    actions = [r.action for r in rows]
    assert total == len(rows) and {"accept", "edit", "reject", "reopen", "rerun_proposal"} <= set(actions)


def test_accept_and_dismiss_proposal(tx):
    from riskminer.review import audit

    pid = _project(tx, "T-REV-2")
    audit.apply_action(tx, "project", pid, "accept", "ekspert")
    upsert_reviewable(tx, Project, {"id": pid, "code": "T-REV-2", "title": "Nowy tytuł z ponownego przetworzenia"})
    rev = audit.apply_action(tx, "project", pid, "accept_proposal", "ekspert")
    p = tx.get(Project, pid)
    assert p.title.startswith("Nowy tytuł") and p.proposal is None and p.status == "approved"
    assert rev.after["title"].startswith("Nowy tytuł")

    upsert_reviewable(tx, Project, {"id": pid, "code": "T-REV-2", "title": "Inny"})
    audit.dismiss_proposal(tx, "project", pid, "ekspert")
    assert p.proposal is None and p.title.startswith("Nowy tytuł")
    with pytest.raises(audit.ReviewError):
        audit.apply_action(tx, "project", pid, "accept_proposal", "ekspert")


def test_bulk_confirm_by_confidence_and_ids(tx):
    from riskminer.review import audit

    pid = _project(tx, "T-REV-3")
    l1, _ = _link(tx, pid, "ocds-T-101", 1.0, "ocid")
    l2, _ = _link(tx, pid, "ocds-T-102", 0.6, "fuzzy")
    l3, _ = _link(tx, pid, "ocds-T-103", 1.0, "notice_no")
    n, _ = audit.bulk_confirm(tx, "project_procedure", "ekspert", min_confidence=1.0, project_id=pid)
    assert n == 2
    assert tx.get(ProjectProcedure, l1).status == "approved" and tx.get(ProjectProcedure, l2).status == "proposed"
    n, skipped = audit.bulk_confirm(tx, "project_procedure", "ekspert", ids=[l2, l3])
    assert (n, skipped) == (1, 1)
    assert tx.query(Review).filter(Review.object_id == l2, Review.action == "bulk_confirm").count() == 1


def test_relink_creates_override_and_blacklist(tx):
    from riskminer.review import audit, learning

    pid = _project(tx, "T-REV-4")
    wrong, _ = _link(tx, pid, "ocds-T-201", 0.55, "fuzzy")
    prid = make_id("procedure", "ocds-T-202")
    tx.add(Procedure(id=prid, ocid="ocds-T-202", title="Właściwe postępowanie"))
    tx.flush()
    rev = audit.relink(tx, wrong, "ekspert", ocid="ocds-T-202", comment="właściwe postępowanie")
    assert tx.get(ProjectProcedure, wrong).status == "rejected"
    new = tx.get(ProjectProcedure, make_id("project_procedure", pid, prid, None))
    assert new.is_override and new.method == "expert" and new.status == "approved"
    assert rev.after["new_link_id"] == str(new.id)
    ov = learning.link_overrides(tx)
    modes = {(o["mode"], o["procedure_id"]) for o in ov if o["project_id"] == str(pid)}
    assert ("force", str(prid)) in modes and ("forbid", str(tx.get(ProjectProcedure, wrong).procedure_id)) in modes
    assert str(wrong) in learning.blacklist(tx, "project_procedure")

    # unknown target: override stored for S1 to fetch
    rev = audit.relink(tx, new.id, "ekspert", notice_number="2025/BZP 00999999/01")
    assert rev.after["pending_fetch"] is True
    assert any(o["notice_number"] == "2025/BZP 00999999/01" for o in learning.link_overrides(tx))


def test_rules_are_versioned(tx):
    from riskminer.review import learning

    r1 = learning.put_rule(tx, "blacklist", "test:x", {"a": 1}, "e")
    assert learning.put_rule(tx, "blacklist", "test:x", {"a": 1}, "e").id == r1.id
    r2 = learning.put_rule(tx, "blacklist", "test:x", {"a": 2}, "e")
    assert r2.version == 2 and not r1.active
    learning.deactivate_rule(tx, "blacklist", "test:x", "e")
    assert tx.query(Rule).filter(Rule.key == "test:x").count() == 3
    assert "test:x" not in {r.key for r in learning.active_rules(tx, "blacklist")}


def test_few_shot_and_recommendation_sources(tx):
    from riskminer.models import Clause
    from riskminer.review import audit, learning

    pid = _project(tx, "T-REV-5")
    eid = make_id("event", "T-REV-5", 1)
    upsert_reviewable(tx, Event, {"id": eid, "project_id": pid, "event_type": "change_deadline",
                                  "quote": "Zmiana terminu z powodu kolizji z siecią gazową", "cause": "kolizja",
                                  "risk_codes": ["R03"], "method": "llm", "confidence": 0.7})
    did = make_id("event", "T-REV-5", 2)
    upsert_reviewable(tx, Event, {"id": did, "project_id": pid, "event_type": "doc_fragment", "quote": "x"})
    audit.apply_action(tx, "event", eid, "exemplary", "ekspert")
    shots = learning.get_few_shot(tx, "causes", k=3)
    assert any(s["object_id"] == str(eid) and s["output"]["risk_codes"] == ["R03"] for s in shots)
    assert all(s["object_id"] != str(did) for s in shots)
    assert tx.get(Event, eid).exemplary and tx.get(Event, eid).status == "approved"
    audit.apply_action(tx, "event", eid, "unexemplary", "ekspert")
    assert all(s["object_id"] != str(eid) for s in learning.get_few_shot(tx, "causes", k=50)
               if not tx.get(Event, eid).exemplary)

    cid = make_id("clause", "T-K-1")
    tx.add(Clause(id=cid, code="T-K-1", risk_code="R03", text="Zamawiający przekaże inwentaryzację sieci…",
                  status="approved"))
    tx.flush()
    src = learning.recommendation_sources(tx, ["R03"])
    assert any(c["id"] == str(cid) for c in src["clauses"])


def test_queue_orders_uncertain_first(tx):
    from riskminer.review import queue

    pid = _project(tx, "T-REV-6")
    _link(tx, pid, "ocds-T-301", 0.95)
    low, _ = _link(tx, pid, "ocds-T-302", 0.3, "fuzzy")
    items, total = queue.queue(tx, project_id=pid, limit=10)
    links = [i for i in items if i["object_type"] == "project_procedure"]
    assert links[0]["object_id"] == low and links[0]["uncertainty"] == pytest.approx(0.7)
    assert links[0]["project_code"] == "T-REV-6" and "ocds-T-302"[-3:] in links[0]["title"]
    assert total >= 3


def test_review_api_roundtrip(client, tx):
    pid = _project(tx, "T-REV-7")
    lid, _ = _link(tx, pid, "ocds-T-401", 0.5, "fuzzy")
    r = client.get("/api/review/queue", params={"project_id": str(pid)})
    assert r.status_code == 200 and r.json()["total"] >= 2
    r = client.post(f"/api/review/project_procedure/{lid}", json={"action": "reject", "comment": "zły"})
    assert r.status_code == 200, r.text
    assert r.json()["reviewer"] == "ekspert_test" and r.json()["after"]["status"] == "rejected"
    r = client.post(f"/api/review/project/{pid}", json={"action": "edit", "changes": {"nope": 1}})
    assert r.status_code == 422
    r = client.post("/api/review/bulk-confirm", json={"object_type": "project", "ids": [str(pid)]})
    assert r.json() == {"confirmed": 1, "skipped": 0}
    r = client.get("/api/history", params={"project_id": str(pid)})
    assert {h["action"] for h in r.json()["items"]} >= {"reject", "bulk_confirm"}
    assert client.get("/api/review/counts").json()["project"] >= 0
