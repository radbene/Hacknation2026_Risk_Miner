"""S5: knowledge tables in the DB – load from YAML, versioning, derived tables, API, new sector = new files."""

from __future__ import annotations

from tests.test_review import client, tx  # noqa: F401  (fixtures)


def test_infer_columns():
    from riskminer.knowledge.store import infer_columns

    cols = {c["key"]: c for c in infer_columns([{"code": "R01", "risk_codes": ["R01"], "weight": 0.3,
                                                  "status": "draft", "x": True}])}
    assert cols["code"]["label"] == "Kod" and cols["risk_codes"]["type"] == "rcodes"
    assert cols["weight"]["type"] == "number" and cols["status"]["options"] and cols["x"]["type"] == "bool"


def test_load_and_version(tx):  # noqa: F811
    from riskminer.ids import make_id
    from riskminer.knowledge import store
    from riskminer.models import Review, RiskCategory

    rep = store.load_sector(tx, "wodkan", actor="test")
    assert {"risks", "subsectors", "checklist", "thresholds", "checklist_rcodes"} <= set(rep["tables"])
    if "risks" in rep["written"]:
        assert tx.get(RiskCategory, make_id("risk_category", "wodkan", "R01")) is not None
    rep2 = store.load_sector(tx, "wodkan", actor="test")
    assert rep2["written"] == [] and set(rep2["unchanged"]) == set(rep["tables"])

    t1 = store.current(tx, "wodkan", "thresholds")
    rows = [dict(r) for r in t1.rows]
    rows[0]["value"] = 0.95
    t2 = store.save_version(tx, "wodkan", "thresholds", rows, actor="ekspert", comment="wyższy próg")
    assert t2.version == t1.version + 1 and store.current(tx, "wodkan", "thresholds").id == t2.id
    assert store.current(tx, "wodkan", "thresholds", t1.version).rows[0]["value"] != 0.95
    assert len(store.versions(tx, "wodkan", "thresholds")) >= 2
    assert store.rows("thresholds", "wodkan", tx)[0]["value"] == 0.95
    assert tx.query(Review).filter(Review.object_id == t2.id, Review.action == "edit").count() == 1
    # re-import of the unchanged file does not clobber the expert edit
    store.load_sector(tx, "wodkan", actor="test")
    assert store.current(tx, "wodkan", "thresholds").id == t2.id
    checklist = store.current(tx, "wodkan", "checklist_rcodes")
    assert all("no" in r for r in checklist.rows)  # YAML 1.1 'no' → False trap


def test_editing_risks_updates_risk_category(tx):  # noqa: F811
    from riskminer.ids import make_id
    from riskminer.knowledge import store
    from riskminer.models import RiskCategory

    store.load_sector(tx, "wodkan")
    rows = [dict(r) for r in store.current(tx, "wodkan", "risks").rows]
    rows.append({"code": "P-T01", "name": "Ryzyko testowe", "effects": "test"})
    store.save_version(tx, "wodkan", "risks", rows, actor="ekspert")
    rc = tx.get(RiskCategory, make_id("risk_category", "wodkan", "P-T01"))
    assert rc is not None and rc.name == "Ryzyko testowe"


def test_clauses_yaml_seeds_clause(tx):  # noqa: F811
    from riskminer.ids import make_id
    from riskminer.knowledge import store
    from riskminer.models import Clause

    store.save_version(tx, "wodkan", "clauses", [{"code": "T-K-9", "risk_code": "R03", "title": "Kolizje",
                                                  "text": "Zamawiający przekaże…", "status": "draft"}], actor="s3")
    c = tx.get(Clause, make_id("clause", "wodkan", "T-K-9"))
    assert c.status == "proposed" and c.risk_code == "R03"


def test_knowledge_api(client):  # noqa: F811
    r = client.post("/api/knowledge/wodkan/import")
    assert r.status_code == 200, r.text
    secs = {s["code"]: s for s in client.get("/api/knowledge/sectors").json()}
    assert secs["wodkan"]["active"] and "risks" in secs["wodkan"]["tables"] and "drogi" in secs
    tables = {t["name"]: t for t in client.get("/api/knowledge/wodkan/tables").json()}
    assert tables["risks"]["n_rows"] == 15
    t = client.get("/api/knowledge/wodkan/tables/porady").json()
    assert t["columns"] and t["rows"]
    r = client.put("/api/knowledge/wodkan/tables/porady", json={"rows": t["rows"][:3], "comment": "skrót"})
    assert r.status_code == 200 and r.json()["version"] == t["version"] + 1
    r = client.post(f"/api/knowledge/wodkan/tables/porady/restore/{t['version']}")
    assert len(r.json()["rows"]) == len(t["rows"])
    vers = client.get("/api/knowledge/wodkan/tables/porady/versions").json()
    assert [v["version"] for v in vers][:3] == [t["version"] + 2, t["version"] + 1, t["version"]]
    assert client.get("/api/knowledge/wodkan/tables/nope").status_code == 404
    assert client.get("/api/clauses").status_code == 200


def test_new_sector_is_just_files(tx, tmp_path, monkeypatch):  # noqa: F811
    from riskminer.core.config import get_config
    from riskminer.knowledge import store

    (tmp_path / "kolej").mkdir()
    (tmp_path / "kolej" / "risks.yaml").write_text("sector: kolej\nname: risks\nrows:\n- {code: K01, name: Tory}\n",
                                                   encoding="utf-8")
    monkeypatch.setattr(get_config(), "knowledge_dir", str(tmp_path))
    assert store.sectors_on_disk() == ["kolej"]
    rep = store.load_sector(tx, "kolej")
    assert rep["written"] == ["risks"] and store.rows("risks", "kolej", tx) == [{"code": "K01", "name": "Tory"}]
