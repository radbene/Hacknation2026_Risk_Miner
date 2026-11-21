"""S1: import → store notices → link → gold-set precision/recall; idempotent rerun; expert decisions survive."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from riskminer.connectors.bzp_store import build_procedure, ensure_sources, store_notice
from riskminer.connectors.xlsx_import import import_path
from riskminer.ids import make_id
from riskminer.link.matcher import link_all
from riskminer.link.quality import evaluate
from riskminer.models import Notice, Project, ProjectProcedure, Rule


@pytest.fixture(scope="module")
def loaded(db_available, notices22, fixtures_dir):
    if not db_available:
        pytest.skip("no database")
    from riskminer.core.db import session_scope

    with session_scope() as s:
        import_path(s, fixtures_dir / "organizer" / "Risk_Miner_dane_projekty.xlsx")
        ensure_sources(s)
        for r in notices22:
            store_notice(s, r, source_code="bzp_zip", retrieved_from="zip:notices_by_nip", tier="deep", keep_html=False)
        s.flush()
        for oc in {r["tenderId"] for r in notices22 if r.get("tenderId")}:
            build_procedure(s, oc, tier="deep")
        link_all(s)
    return True


def test_gold_precision_recall(loaded, db):
    q = evaluate(db)
    assert q["precision"] >= 0.95 and q["recall"] >= 0.95, q
    assert q["projects_fully_correct"] >= 21
    assert not q["decoys_linked"]


def test_rerun_idempotent(loaded, db):
    from riskminer.core.db import session_scope

    n_links = db.scalar(select(func.count()).select_from(ProjectProcedure))
    n_notices = db.scalar(select(func.count()).select_from(Notice))
    with session_scope() as s:
        res = link_all(s)
    assert all(r["status"] in ("linked", "uncertain") for r in res)
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(ProjectProcedure)) == n_links
    assert db.scalar(select(func.count()).select_from(Notice)) == n_notices


def test_expert_reject_and_override_survive(loaded):
    from riskminer.core.db import session_scope

    with session_scope() as s:
        p = s.execute(select(Project).where(Project.code == "RM-2026-022")).scalar_one()
        link = s.execute(select(ProjectProcedure).where(ProjectProcedure.project_id == p.id)).scalars().first()
        lid, before = link.id, link.status
        link.status, link.reviewed_by = "rejected", "test"
    try:
        with session_scope() as s:
            link_all(s, [p.id])
        with session_scope() as s:
            assert s.get(ProjectProcedure, lid).status == "rejected"
        # override → expert link to the same procedure is kept and marked
        with session_scope() as s:
            proc_id = s.get(ProjectProcedure, lid).procedure_id
            s.add(Rule(id=make_id("rule", "link_override", "RM-2026-022", 999), kind="link_override",
                       key="RM-2026-022", version=999, body={"procedure_id": str(proc_id), "comment": "test"}))
        with session_scope() as s:
            r = link_all(s, [p.id])[0]
            assert r["method"] == "expert"
    finally:
        with session_scope() as s:
            s.query(Rule).filter(Rule.key == "RM-2026-022", Rule.version == 999).delete()
            row = s.get(ProjectProcedure, lid)
            row.status, row.reviewed_by, row.method, row.is_override = before, None, "xref", False
        with session_scope() as s:
            link_all(s, [p.id])
