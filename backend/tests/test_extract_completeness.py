"""Completeness: 4 expert states + contradictions (Bobrowniki: 'Zakończone' but no ContractPerforming notice)."""

from __future__ import annotations

import datetime as dt
import uuid

from bzp_rows import by_ocid, load

from riskminer.models import Project


def _ocid_of(notices22, number):
    return next(n["tenderId"] for n in notices22 if n["noticeNumber"] == number)


def _isolated(ns: list[dict], tag: str) -> list[dict]:
    """Test-only copy of a procedure's notices (own OCID / objectIds) so an as-of replay is not affected by the
    later notices of the real procedure already stored in a shared DB."""
    out = []
    for n in ns:
        c = dict(n)
        c["tenderId"] = f"{n['tenderId']}-{tag}"
        c["objectId"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{tag}:{n['objectId']}"))
        c["noticeNumber"] = f"{n['noticeNumber']}-{tag}"
        out.append(c)
    return out


def test_bobrowniki_contradiction(db, notices22):
    from riskminer.extract.completeness import compute

    # as-of replay before the ContractPerforming notice 2026/BZP 00331672/01 (published 2026-07-09)
    ns = [n for n in by_ocid(notices22, _ocid_of(notices22, "2026/BZP 00130634/01")) if n["publicationDate"] < "2026-07-01"]
    assert "ContractPerformingNotice" not in {n["noticeType"] for n in ns}
    ids = load(db, _isolated(ns, "asof"), project_code="RM-TEST-014")
    db.get(Project, ids["project_id"]).project_status = "Zakończone"
    score, items = compute(db, ids["project_id"], today=dt.date(2026, 11, 21))
    contra = [i for i in items if i.kind == "contradiction"]
    assert contra and contra[0].state == "sprzeczne" and "Zakończone" in contra[0].message and contra[0].what_to_add
    states = {i.state for i in items}
    assert "nie_ma_w_paczce" in states and "potwierdzone" in states
    assert all(i.impact for i in items if i.state != "potwierdzone")
    assert 0 < score < 1
    # idempotent
    score2, items2 = compute(db, ids["project_id"], today=dt.date(2026, 11, 21))
    assert score2 == score and {i.id for i in items2} == {i.id for i in items}


def test_nowogard_vague_reason_and_performed(db, notices22):
    from riskminer.extract.completeness import compute

    ids = load(db, by_ocid(notices22, "ocds-148610-740158c8-9281-4fe9-9f58-59edc56af25c"), project_code="RM-TEST-020")
    _, items = compute(db, ids["project_id"])
    perf = [i for i in items if i.field.startswith("wykonanie umowy")]
    assert perf and perf[0].state == "potwierdzone"
