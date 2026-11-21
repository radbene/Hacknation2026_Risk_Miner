"""Rule events on real notices (notices22) – Nowogard showcase RM-2026-020."""

from __future__ import annotations

import datetime as dt

import pytest
from bzp_rows import by_ocid, load
from sqlalchemy import select

from riskminer.models import Event, Evidence

NOWOGARD = "ocds-148610-740158c8-9281-4fe9-9f58-59edc56af25c"


@pytest.fixture
def nowogard(db, notices22):
    ids = load(db, by_ocid(notices22, NOWOGARD), project_code="RM-TEST-020")
    return ids


def _events(db, pid):
    return db.execute(select(Event).where(Event.procedure_id == pid)).scalars().all()


def test_nowogard_showcase(db, nowogard):
    from riskminer.extract.rules import extract_procedure

    rep = extract_procedure(db, nowogard["procedure_id"])
    assert not rep.errors, rep.errors
    evs = _events(db, nowogard["procedure_id"])
    changes = sorted([e for e in evs if e.change_id], key=lambda e: e.effect_days or 0)
    assert len(changes) == 2, [(e.event_type, e.cause) for e in evs]  # AU + CP 5.4.x deduplicated
    by_cause = {("służebno" in (e.cause or "").lower()): e for e in changes}
    serv, ground = by_cause[True], by_cause[False]
    assert serv.risk_codes[0] == "R03" and serv.event_type == "change_deadline"
    assert "R02" in ground.risk_codes
    assert "30 listopada 2025" in serv.effect or "2025-11-30" in serv.effect
    assert "2025-12-31" in ground.effect
    assert serv.mitigation_effect == "nieskuteczne"  # finished 2026-04-27 after the amended 2025-12-31
    late = next(e for e in evs if e.event_type == "late")
    assert late.effect_days == (dt.date(2026, 4, 27) - dt.date(2025, 10, 24)).days
    assert late.project_id == nowogard["project_id"]
    assert any(e.event_type == "improper" for e in evs)  # "pomniejszona o kary umowne"
    # every event cites evidence with a permanent URL; notice quotes verified
    for e in evs:
        assert e.evidence_ids, e.event_type
        rows = [db.get(Evidence, __import__("uuid").UUID(i)) for i in e.evidence_ids]
        assert any(r.url and r.url.startswith("https://ezamowienia.gov.pl/") for r in rows if r.kind == "notice_section")
        for r in rows:
            if r.kind == "notice_section" and r.locator.get("section") not in ("V/VI", "VI"):
                assert r.quote_verified is not False, (r.locator, r.quote)
    # rerun is idempotent
    rep2 = extract_procedure(db, nowogard["procedure_id"])
    assert set(rep2.results.values()) <= {"unchanged", "updated"}


def test_rerun_keeps_expert_decision(db, nowogard):
    from riskminer.extract.rules import extract_procedure

    extract_procedure(db, nowogard["procedure_id"])
    late = next(e for e in _events(db, nowogard["procedure_id"]) if e.event_type == "late")
    late.status, late.title = "edited", "Opóźnienie – zweryfikowane"
    db.flush()
    extract_procedure(db, nowogard["procedure_id"])
    db.refresh(late)
    assert late.title == "Opóźnienie – zweryfikowane"
