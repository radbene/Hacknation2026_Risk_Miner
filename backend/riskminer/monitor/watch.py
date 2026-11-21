"""Monitoring of unfinished investments (P1).

- `set_watch` marks procedures (or every procedure of a project) as watched.
- `run_monitor(as_of=None)` – live: fetch new BZP notices of watched OCIDs since the last check (feed.py),
  store them, raise `new_notice` alerts and request a re-analysis (S2 job "reanalyze" if registered).
- `run_monitor(as_of=D)` – **replay**: pretend today is D. Only notices already in the DB with
  published_at ≤ D are visible; notices published between the previous replay cursor and D are reported as
  new. This lets the demo walk an investment through time (e.g. Nowogard 2025 → 2026).
- Every run also checks deadlines (planned end passed without a ContractPerforming notice) and data quality
  (organizer rows marked "Zakończone" with no ContractPerforming notice in BZP, e.g. Bobrowniki).

Alert ids are uuid5 of their natural key, so reruns never duplicate alerts.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import Any

from sqlalchemy import false, or_, select
from sqlalchemy.orm import Session

from riskminer.core.evidence import NOTICE_PAGE, NOTICE_PDF
from riskminer.core.upsert import upsert
from riskminer.ids import make_id
from riskminer.models import (
    Alert,
    Contract,
    ContractChange,
    Notice,
    Procedure,
    Project,
    ProjectProcedure,
    Setting,
)

log = logging.getLogger("riskminer.monitor")
CURSOR_KEY = "monitor.cursor"
PERFORMING = "ContractPerformingNotice"
NOTICE_TYPE_PL = {
    "ContractNotice": "ogłoszenie o zamówieniu",
    "TenderResultNotice": "ogłoszenie o wyniku postępowania",
    "AgreementUpdateNotice": "ogłoszenie o zmianie umowy",
    "ContractPerformingNotice": "ogłoszenie o wykonaniu umowy",
}


# ---------------------------------------------------------------- helpers


def _today() -> dt.date:
    return dt.date.today()


def _end_of(day: dt.date) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.max, tzinfo=dt.UTC)


def get_cursor(session: Session) -> dict[str, Any]:
    s = session.get(Setting, CURSOR_KEY)
    return dict(s.value) if s and s.value else {}


def set_cursor(session: Session, value: dict[str, Any], user: str | None = None) -> None:
    # ORM write (not a Core upsert) so an already-loaded Setting in this session is not left stale
    s = session.get(Setting, CURSOR_KEY)
    if s is None:
        session.add(Setting(key=CURSOR_KEY, value=value, updated_by=user or "monitor"))
    else:
        s.value, s.updated_by, s.version = value, user or "monitor", (s.version or 1) + 1
    session.flush()


def alert(session: Session, *, kind: str, key: tuple, message: str, severity: str = "info",
          project_id=None, procedure_id=None, notice_id=None, payload: dict | None = None) -> tuple[uuid.UUID, bool]:
    """Idempotent alert. Returns (id, created). Existing alerts keep their `read` flag."""
    aid = make_id("alert", kind, *key)
    existing = session.get(Alert, aid)
    if existing is not None:
        existing.message, existing.severity, existing.payload = message, severity, payload or {}
        return aid, False
    session.add(Alert(id=aid, kind=kind, severity=severity, message=message, project_id=project_id,
                      procedure_id=procedure_id, notice_id=notice_id, payload=payload or {}))
    session.flush()
    return aid, True


def _project_for(session: Session, procedure_id) -> uuid.UUID | None:
    return session.execute(
        select(ProjectProcedure.project_id).where(ProjectProcedure.procedure_id == procedure_id,
                                                  ProjectProcedure.status != "rejected")
        .order_by(ProjectProcedure.rank)
    ).scalars().first()


def watched_procedures(session: Session) -> list[Procedure]:
    return list(session.execute(select(Procedure).where(Procedure.watched.is_(True))).scalars())


# ---------------------------------------------------------------- watch list


def set_watch(session: Session, procedure_ids=None, project_ids=None, watched: bool = True) -> int:
    ids = set(procedure_ids or [])
    if project_ids:
        ids |= set(session.execute(select(ProjectProcedure.procedure_id)
                                   .where(ProjectProcedure.project_id.in_(list(project_ids)),
                                          ProjectProcedure.status != "rejected")).scalars())
    n = 0
    for pid in ids:
        p = session.get(Procedure, pid)
        if p is not None and p.watched != watched:
            p.watched = watched
            n += 1
    session.flush()
    return n


def auto_watch_unfinished(session: Session) -> int:
    """Watch every linked procedure of projects that are not finished (no performing notice yet)."""
    rows = session.execute(
        select(ProjectProcedure.procedure_id, Project.project_status)
        .join(Project, Project.id == ProjectProcedure.project_id)
        .where(ProjectProcedure.status != "rejected")
    ).all()
    n = 0
    for proc_id, status in rows:
        if status and status.lower().startswith("zakończ"):
            continue
        has_perf = session.execute(select(Notice.id).where(Notice.procedure_id == proc_id,
                                                           Notice.notice_type == PERFORMING).limit(1)).first()
        p = session.get(Procedure, proc_id)
        if p is not None and not has_perf and not p.watched:
            p.watched = True
            n += 1
    session.flush()
    return n


# ---------------------------------------------------------------- live ingestion


def _store_items(session: Session, items: list[dict]) -> list[Notice]:
    """Store API items. Uses S1's ingest if available, else a minimal Notice row (S1's parser fills the rest)."""
    try:
        from riskminer.connectors import bzp as s1  # type: ignore

        fn = getattr(s1, "ingest_items", None)
        if callable(fn):
            fn(session, items, retrieved_from=None)
            oids = [i.get("objectId") for i in items]
            return list(session.execute(select(Notice).where(Notice.object_id.in_(oids))).scalars())
    except ImportError:
        pass
    out = []
    for it in items:
        oid = it.get("objectId")
        if not oid:
            continue
        proc = session.execute(select(Procedure).where(Procedure.ocid == it.get("tenderId"))).scalars().first()
        nid = make_id("notice", oid)
        pub = it.get("publicationDate")
        upsert(session, Notice, {
            "id": nid, "object_id": oid, "notice_number": it.get("noticeNumber") or oid,
            "bzp_number": it.get("bzpNumber"), "notice_type": it.get("noticeType") or "?",
            "procedure_id": proc.id if proc else None, "ocid": it.get("tenderId"),
            "published_at": dt.datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None,
            "title": it.get("orderObject"), "org_name": it.get("organizationName"),
            "org_nip": it.get("organizationNationalId"), "org_city": it.get("organizationCity"),
            "org_province": it.get("organizationProvince"), "order_type": it.get("orderType"),
            "url": NOTICE_PAGE.format(object_id=oid), "pdf_url": NOTICE_PDF.format(object_id=oid),
            "retrieved_from": "bzp-api", "retrieved_at": dt.datetime.now(dt.UTC), "tier": "auto",
        })
        out.append(session.get(Notice, nid))
    session.flush()
    return out


def _request_reanalysis(session: Session, notice: Notice, project_id) -> str | None:
    import riskminer.core.handlers  # noqa: F401  registers every session's handlers
    from riskminer.core.jobs import HANDLERS, enqueue

    if "reanalyze" not in HANDLERS:
        return None
    job = enqueue(session, "reanalyze", {"notice_id": str(notice.id), "procedure_id": str(notice.procedure_id),
                                         "project_id": str(project_id) if project_id else None,
                                         "reason": "monitor:new_notice"}, user="monitor")
    return str(job.id)


def _new_notice_alerts(session: Session, notices: list[Notice], *, as_of: dt.date | None,
                       reanalyse: bool) -> list[dict]:
    out = []
    for n in sorted(notices, key=lambda x: x.published_at or dt.datetime.min.replace(tzinfo=dt.UTC)):
        project_id = _project_for(session, n.procedure_id) if n.procedure_id else None
        sev = "warning" if n.notice_type in ("AgreementUpdateNotice",) else "info"
        msg = (f"Nowe {NOTICE_TYPE_PL.get(n.notice_type, n.notice_type)} {n.notice_number} "
               f"({(n.published_at.date().isoformat() if n.published_at else '?')}): {(n.title or '')[:160]}")
        aid, created = alert(session, kind="new_notice", key=(n.object_id,), message=msg, severity=sev,
                             project_id=project_id, procedure_id=n.procedure_id, notice_id=n.id,
                             payload={"notice_number": n.notice_number, "notice_type": n.notice_type,
                                      "url": n.url, "as_of": as_of.isoformat() if as_of else None})
        job_id = _request_reanalysis(session, n, project_id) if (created and reanalyse) else None
        if job_id:
            alert(session, kind="reanalysis", key=(n.object_id,), severity="info", project_id=project_id,
                  procedure_id=n.procedure_id, notice_id=n.id,
                  message=f"Zlecono ponowną analizę po ogłoszeniu {n.notice_number}",
                  payload={"job_id": job_id})
        out.append({"alert_id": str(aid), "created": created, "notice": n.notice_number, "type": n.notice_type,
                    "reanalysis_job": job_id})
    return out


# ---------------------------------------------------------------- checks


def check_deadlines(session: Session, as_of: dt.date) -> list[dict]:
    """Contracts whose planned end passed before `as_of` with no ContractPerforming notice visible at `as_of`."""
    out = []
    rows = session.execute(select(Contract).where(Contract.planned_end.is_not(None),
                                                  Contract.planned_end < as_of)).scalars()
    for c in rows:
        perf = session.execute(select(Notice.id).where(
            Notice.procedure_id == c.procedure_id, Notice.notice_type == PERFORMING,
            or_(Notice.published_at.is_(None), Notice.published_at <= _end_of(as_of))).limit(1)).first()
        if perf:
            continue
        # latest agreed end date from changes (art. 455) visible at as_of
        new_end = session.execute(select(ContractChange.new_end).where(
            ContractChange.contract_id == c.id, ContractChange.new_end.is_not(None),
            or_(ContractChange.change_date.is_(None), ContractChange.change_date <= as_of))
            .order_by(ContractChange.new_end.desc())).scalars().first()
        end = max(d for d in (c.planned_end, new_end) if d)
        if end >= as_of:
            continue
        days = (as_of - end).days
        aid, created = alert(
            session, kind="deadline_passed", key=(str(c.id),), severity="warning" if days < 90 else "high",
            project_id=_project_for(session, c.procedure_id), procedure_id=c.procedure_id,
            message=f"Termin wykonania umowy minął {end.isoformat()} ({days} dni temu), brak ogłoszenia o wykonaniu umowy",
            payload={"contract_id": str(c.id), "planned_end": c.planned_end.isoformat(),
                     "amended_end": new_end.isoformat() if new_end else None, "as_of": as_of.isoformat(),
                     "days_overdue": days})
        out.append({"alert_id": str(aid), "created": created, "contract": str(c.id), "days": days})
    return out


def check_finished_without_performing(session: Session) -> list[dict]:
    """Organizer rows marked 'Zakończone' without any ContractPerforming notice in BZP → data-quality alert."""
    out = []
    projects = session.execute(select(Project).where(Project.project_status.ilike("zakończ%"))).scalars()
    for p in projects:
        proc_ids = list(session.execute(select(ProjectProcedure.procedure_id).where(
            ProjectProcedure.project_id == p.id, ProjectProcedure.status != "rejected")).scalars())
        has_perf = bool(proc_ids) and session.execute(select(Notice.id).where(
            Notice.procedure_id.in_(proc_ids), Notice.notice_type == PERFORMING).limit(1)).first() is not None
        if has_perf:
            continue
        why = ("brak powiązanego postępowania w BZP" if not proc_ids
               else "w BZP brak ogłoszenia o wykonaniu umowy dla powiązanych postępowań")
        aid, created = alert(
            session, kind="data_quality", key=("finished_without_performing", p.code), severity="warning",
            project_id=p.id,
            message=f"{p.code}: w danych organizatora status „{p.project_status}”, ale {why}",
            payload={"project_code": p.code, "rule": "finished_without_performing", "procedures": len(proc_ids),
                     "source": {"xlsx_row": (p.import_row or {}).get("_row")}})
        out.append({"alert_id": str(aid), "created": created, "project": p.code})
    return out


# ---------------------------------------------------------------- run


def run_monitor(session: Session, as_of: dt.date | None = None, *, reanalyse: bool = True,
                live: bool | None = None, user: str | None = None, job_id=None) -> dict[str, Any]:
    """One monitoring pass. Returns a run report (stored as job.result when run as a job)."""
    cursor = get_cursor(session)
    report: dict[str, Any] = {"mode": "replay" if as_of else "live", "as_of": (as_of or _today()).isoformat(),
                              "previous_cursor": cursor.get("as_of")}
    watched = watched_procedures(session)
    report["watched"] = len(watched)
    ids = [p.id for p in watched]
    new: list[Notice] = []

    if as_of is not None:  # replay from the DB
        prev = dt.date.fromisoformat(cursor["as_of"]) if cursor.get("mode") == "replay" and cursor.get("as_of") else None
        if prev is None or as_of < prev:
            report["note"] = ("pierwszy przebieg / przewinięcie: ustawiono punkt odniesienia, ogłoszenia do tej "
                              "daty traktowane jako znane")
        elif ids:
            new = list(session.execute(select(Notice).where(
                Notice.procedure_id.in_(ids), Notice.published_at > _end_of(prev),
                Notice.published_at <= _end_of(as_of))).scalars())
        report["visible_notices"] = len(session.execute(select(Notice.id).where(
            Notice.procedure_id.in_(ids) if ids else false(), Notice.published_at <= _end_of(as_of))).all())
        set_cursor(session, {"as_of": as_of.isoformat(), "mode": "replay"}, user)
    else:  # live
        today = _today()
        prev = dt.date.fromisoformat(cursor["as_of"]) if cursor.get("mode") == "live" and cursor.get("as_of") else None
        date_from = (prev + dt.timedelta(days=1)) if prev else today - dt.timedelta(days=2)
        if live is not False and watched:
            from riskminer.monitor import feed

            items = feed.fetch_for_ocids([p.ocid for p in watched if p.ocid], date_from, today, job_id=job_id)
            known = set(session.execute(select(Notice.object_id).where(
                Notice.object_id.in_([i.get("objectId") for i in items]))).scalars()) if items else set()
            new = _store_items(session, [i for i in items if i.get("objectId") not in known])
            report["fetched"] = len(items)
            report["window"] = [date_from.isoformat(), today.isoformat()]
        set_cursor(session, {"as_of": today.isoformat(), "mode": "live"}, user)

    report["new_notices"] = _new_notice_alerts(session, new, as_of=as_of, reanalyse=reanalyse)
    report["deadlines"] = check_deadlines(session, as_of or _today())
    report["data_quality"] = check_finished_without_performing(session)
    report["alerts_created"] = sum(1 for k in ("new_notices", "deadlines", "data_quality")
                                   for a in report[k] if a.get("created"))
    session.commit()
    return report
