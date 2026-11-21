"""S6: ops router, monitoring (as_of replay, deadlines, data quality), licences, ERD, demo helpers."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

from riskminer.monitor.docs_gen import erd_mermaid
from riskminer.monitor.licences import classify


def test_classify_licences():
    assert classify("MIT") == "ok"
    assert classify("Apache-2.0 OR BSD-3-Clause") == "ok"
    assert classify("LGPL-3.0-only") == "note"
    assert classify("GPL-3.0-or-later") == "forbidden"
    assert classify("AGPL-3.0") == "forbidden"
    assert classify("GPL-2.0 OR MIT") == "ok"
    assert classify("") == "unknown"


def test_erd_has_core_tables_and_relations():
    m = erd_mermaid(compact=True)
    assert m.startswith("erDiagram")
    for t in ("project", "procedure", "notice", "evidence", "alert"):
        assert f"    {t} {{" in m
    assert 'procedure ||--o{ project_procedure : "procedure_id"' in m


def test_demo_command_discovery():
    from riskminer.monitor.demo import command_exists, command_path

    assert command_path(["knowledge", "load"]) == ["knowledge", "load"]
    assert command_path(["import-xlsx", "/x/y.xlsx"]) == ["import-xlsx"]
    assert command_path(["harvest", "--sample", "5"]) == ["harvest"]
    assert command_exists(["monitor", "run"])
    assert command_exists(["report"])
    assert not command_exists(["no-such-command"])


@pytest.fixture
def mon_data(db):
    """A finished project with a watched procedure, 2 notices and an overdue contract."""
    from riskminer.ids import make_id
    from riskminer.models import Alert, Contract, Notice, Procedure, Project, ProjectProcedure, Setting
    from riskminer.monitor.watch import CURSOR_KEY

    tag = uuid.uuid4().hex[:8]
    code = f"T6-{tag}"
    prj = Project(id=make_id("project", code), code=code, title="Test kanalizacja", project_status="Zakończone")
    proc = Procedure(id=make_id("procedure", f"ocds-test-{tag}"), ocid=f"ocds-test-{tag}", title="Budowa kanalizacji",
                     watched=True)
    db.add_all([prj, proc])
    db.flush()
    db.add(ProjectProcedure(id=make_id("project_procedure", prj.id, proc.id, None), project_id=prj.id,
                            procedure_id=proc.id, status="approved"))
    n1 = Notice(id=make_id("notice", f"o1-{tag}"), object_id=f"o1-{tag}", notice_number=f"2025/BZP {tag}/01",
                notice_type="ContractNotice", procedure_id=proc.id,
                published_at=dt.datetime(2025, 5, 1, 10, tzinfo=dt.UTC))
    n2 = Notice(id=make_id("notice", f"o2-{tag}"), object_id=f"o2-{tag}", notice_number=f"2025/BZP {tag}/02",
                notice_type="AgreementUpdateNotice", procedure_id=proc.id,
                published_at=dt.datetime(2025, 9, 1, 10, tzinfo=dt.UTC))
    db.add_all([n1, n2])
    db.add(Contract(id=make_id("contract", proc.id, None, None), procedure_id=proc.id, planned_end=dt.date(2025, 8, 1),
                    status="approved"))
    old_cursor = db.get(Setting, CURSOR_KEY)
    old_value = dict(old_cursor.value) if old_cursor else None
    db.commit()
    yield {"project": prj, "procedure": proc, "n2": n2}
    db.rollback()
    db.query(Alert).filter(Alert.procedure_id == proc.id).delete()
    db.query(Alert).filter(Alert.project_id == prj.id).delete()
    db.query(Notice).filter(Notice.procedure_id == proc.id).delete()
    db.delete(db.get(Project, prj.id))
    db.delete(db.get(Procedure, proc.id))
    s = db.get(Setting, CURSOR_KEY)
    if old_value is None and s is not None:
        db.delete(s)
    elif s is not None:
        s.value = old_value
    db.commit()


def test_monitor_replay_alerts_and_idempotency(db, mon_data):
    from riskminer.models import Alert
    from riskminer.monitor.watch import run_monitor

    base = run_monitor(db, as_of=dt.date(2025, 6, 1), reanalyse=False)
    assert base["mode"] == "replay" and "note" in base  # baseline: nothing reported as new
    assert not [a for a in base["new_notices"]]

    rep = run_monitor(db, as_of=dt.date(2025, 12, 31), reanalyse=False)
    numbers = [a["notice"] for a in rep["new_notices"]]
    assert mon_data["n2"].notice_number in numbers  # agreement update published 2025-09-01
    proc_id = mon_data["procedure"].id
    kinds = {a.kind for a in db.query(Alert).filter(
        (Alert.procedure_id == proc_id) | (Alert.project_id == mon_data["project"].id))}
    assert {"new_notice", "deadline_passed", "data_quality"} <= kinds

    n_before = db.query(Alert).count()
    run_monitor(db, as_of=dt.date(2025, 6, 1), reanalyse=False)   # rewind
    again = run_monitor(db, as_of=dt.date(2025, 12, 31), reanalyse=False)
    assert db.query(Alert).count() == n_before  # uuid5 alert ids → no duplicates
    assert again["alerts_created"] == 0


@pytest.fixture
def client(db_available):
    if not db_available:
        pytest.skip("no database")
    from fastapi.testclient import TestClient

    from riskminer.api.main import app

    return TestClient(app)


def test_ops_endpoints(client):
    r = client.get("/api/dashboard")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "projects" in body["counts"] and "pending_review" in body["counts"]
    assert any(x.startswith("llm:") for x in body["data_locations"])
    assert client.get("/api/ops/log", params={"limit": 5}).status_code == 200
    con = client.get("/api/ops/connectors").json()
    assert {c["code"] for c in con} >= {"bzp", "bzp_zip", "vat_whitelist", "ted"}
    assert all(c["status"] in ("działa", "zaprojektowane") for c in con)
    assert client.get("/api/ops/llm-usage").status_code == 200
    lic = client.get("/api/ops/licences").json()
    assert any(x["kind"] == "data" for x in lic) and any(x["kind"] == "library" for x in lic)
    assert client.get("/api/alerts").status_code == 200
    assert client.get("/api/quality").status_code in (200, 501)
    assert client.post("/api/monitor/watch", json={}).status_code == 422
