"""Project ↔ procedure links (owner: S1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select

from riskminer.api.deps import DB, EXPERT, CurrentUser, Session
from riskminer.models import Entity, Procedure, Project, ProjectProcedure
from riskminer.schemas.cases import LinkCandidate, LinkComponent, LinkOut, ProjectRelinkIn
from riskminer.schemas.common import Page

router = APIRouter(tags=["links"])
OWNER = "S1"


def _comps(raw) -> list[LinkComponent]:
    out = []
    for c in raw or []:
        try:
            out.append(LinkComponent(name=str(c.get("name")), score=float(c.get("score") or 0), weight=c.get("weight"),
                                     detail=c.get("detail"), evidence_id=c.get("evidence_id") or None))
        except (ValueError, TypeError):
            continue
    return out


def _alts(raw) -> list[LinkCandidate]:
    out = []
    for a in raw or []:
        try:
            out.append(LinkCandidate(procedure_id=a.get("procedure_id"), ocid=a.get("ocid"), bzp_number=a.get("bzp_number"),
                                     title=a.get("title"), score=float(a.get("score") or 0),
                                     components=_comps(a.get("components")), why_not=a.get("why_not")))
        except (ValueError, TypeError):
            continue
    return out


def link_out(lk: ProjectProcedure, p: Project, proc: Procedure) -> LinkOut:
    return LinkOut(id=lk.id, project_id=p.id, project_code=p.code, procedure_id=proc.id, ocid=proc.ocid,
                   bzp_number=proc.bzp_number, procedure_title=proc.title, part_no=lk.part_no,
                   components=_comps(lk.components), alternatives=_alts(lk.alternatives), is_override=lk.is_override,
                   rank=lk.rank, status=lk.status, method=lk.method, confidence=lk.confidence,
                   evidence_ids=lk.evidence_ids or [], proposal=lk.proposal, reviewed_by=lk.reviewed_by,
                   reviewed_at=lk.reviewed_at)


def _base():
    return (select(ProjectProcedure, Project, Procedure).join(Project, Project.id == ProjectProcedure.project_id)
            .join(Procedure, Procedure.id == ProjectProcedure.procedure_id))


@router.get("/links", response_model=Page[LinkOut])
def list_links(project_id: uuid.UUID | None = None, status: str | None = None, max_confidence: float | None = None,
               offset: int = 0, limit: int = 100, db: Session = DB):
    q = _base()
    if project_id:
        q = q.where(ProjectProcedure.project_id == project_id)
    else:
        q = q.where(Project.tier == "deep")
    if status:
        q = q.where(ProjectProcedure.status == status)
    if max_confidence is not None:
        q = q.where(func.coalesce(ProjectProcedure.confidence, 0) <= max_confidence)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.execute(q.order_by(Project.code, ProjectProcedure.rank).offset(offset).limit(limit)).all()
    return Page[LinkOut](items=[link_out(*r) for r in rows], total=total, offset=offset, limit=limit)


@router.get("/links/export.csv", response_class=PlainTextResponse)
def export_links_csv(db: Session = DB):
    """links.csv: project, procedure/notice, part, method, confidence, components with evidence, status."""
    from riskminer.connectors.pipeline import links_csv

    return PlainTextResponse(links_csv(db), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=links.csv"})


@router.get("/projects/{project_id}/candidates", response_model=list[LinkCandidate])
def link_candidates(project_id: uuid.UUID, db: Session = DB):
    """All scored candidates (buyer's procedures) with components – fresh scoring, nothing written."""
    from riskminer.link.matcher import key_candidates, score_candidate
    from riskminer.models import Notice

    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Nie znaleziono projektu")
    ent = db.get(Entity, p.beneficiary_id) if p.beneficiary_id else None
    nip = ent.nip if ent else None
    procs = db.execute(select(Procedure).where(Procedure.buyer_nip == nip)).scalars().all() if nip else []
    by_proc: dict[uuid.UUID, LinkCandidate] = {}
    for c in key_candidates(db, p, nip, list(procs)):
        by_proc[c.procedure.id] = _cand(c)
    for proc in procs:
        if proc.id in by_proc:
            continue
        notices = db.execute(select(Notice).where(Notice.procedure_id == proc.id)).scalars().all()
        by_proc[proc.id] = _cand(score_candidate(db, p, proc, list(notices)))
    db.rollback()  # scoring must not persist anything
    return sorted(by_proc.values(), key=lambda c: -c.score)[:25]


def _cand(c) -> LinkCandidate:
    proc = c.procedure
    return LinkCandidate(procedure_id=proc.id, ocid=proc.ocid, bzp_number=proc.bzp_number, title=proc.title,
                         score=round(float(c.score), 3), components=_comps(c.components),
                         why_not=getattr(c, "why_not", None))


@router.post("/projects/{project_id}/relink", response_model=LinkOut)
def relink(project_id: uuid.UUID, body: ProjectRelinkIn, db: Session = DB, user: CurrentUser = EXPERT):
    """Expert relink: pick a candidate, or give an OCID / notice number (fetches it). Stored as override."""
    from riskminer.link.matcher import link_project
    from riskminer.review.audit import ReviewError
    from riskminer.review.audit import relink as do_relink

    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Nie znaleziono projektu")
    if not (body.procedure_id or body.ocid or body.notice_number):
        raise HTTPException(400, "Podaj postępowanie, OCID albo numer ogłoszenia")
    # target not in the DB yet → fetch it from BZP first
    if body.notice_number and not body.procedure_id:
        _fetch_notice(db, body.notice_number)
    current = db.execute(select(ProjectProcedure).where(ProjectProcedure.project_id == p.id,
                                                        ProjectProcedure.status != "rejected")
                         .order_by(ProjectProcedure.rank)).scalars().first()
    try:
        if current:
            do_relink(db, current.id, user.username, procedure_id=body.procedure_id, ocid=body.ocid,
                      notice_number=body.notice_number, part_no=body.part_no, comment=body.comment)
        else:
            from riskminer.ids import make_id
            from riskminer.models import Rule

            ver = (db.scalar(select(func.max(Rule.version)).where(Rule.kind == "link_override", Rule.key == p.code)) or 0) + 1
            db.add(Rule(id=make_id("rule", "link_override", p.code, ver), sector=p.sector, kind="link_override",
                        key=p.code, version=ver, active=True, created_by=user.username,
                        body={"procedure_id": str(body.procedure_id) if body.procedure_id else None, "ocid": body.ocid,
                              "notice_number": body.notice_number, "part_no": body.part_no, "comment": body.comment}))
            db.flush()
        link_project(db, p, actor=user.username)
    except ReviewError as e:
        db.rollback()
        raise HTTPException(400, str(e)) from e
    db.commit()
    row = db.execute(_base().where(ProjectProcedure.project_id == p.id, ProjectProcedure.status != "rejected")
                     .order_by(ProjectProcedure.is_override.desc(), ProjectProcedure.rank)).first()
    if not row:
        raise HTTPException(409, "Zapisano regułę powiązania, ale postępowania nie ma jeszcze w bazie – uruchom „Wzbogać”")
    return link_out(*row)


def _fetch_notice(db: Session, number: str) -> None:
    from riskminer.connectors.bzp import BzpClient
    from riskminer.connectors.bzp_store import build_procedure, store_notice

    try:
        client = BzpClient()
        recs = client.by_notice_number(number.strip())
    except Exception:  # noqa: BLE001 – offline: the override rule is still stored
        return
    ocids = set()
    for r in recs:
        store_notice(db, r, source_code="bzp", retrieved_from=f"{client.base_url}?NoticeNumber={number}", tier="deep")
        if r.get("tenderId"):
            ocids.add(r["tenderId"])
    db.flush()
    for oc in ocids:
        build_procedure(db, oc, tier="deep")
