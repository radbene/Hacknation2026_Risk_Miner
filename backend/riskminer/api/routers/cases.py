"""Case base (owner: S1 acquisition & linking). Projects, procedures, notices, contracts, timeline, graph."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, or_, select

from riskminer.api.deps import DB, EXPERT, CurrentUser, Session
from riskminer.models import (
    Contract,
    ContractChange,
    DataIssue,
    Document,
    Entity,
    Event,
    Notice,
    Procedure,
    Project,
    ProjectProcedure,
)
from riskminer.schemas.cases import (
    ContractChangeOut,
    ContractOut,
    EntityOut,
    GraphEdge,
    GraphNode,
    GraphOut,
    NoticeDetail,
    NoticeOut,
    ProcedureOut,
    ProjectDetail,
    ProjectListItem,
    ProjectPatch,
    SectionOut,
    TimelineItem,
    TimelineOut,
)
from riskminer.schemas.common import Page

router = APIRouter(tags=["cases"])
OWNER = "S1"
KEY_METHODS = {"kpo_ref", "notice_no", "xref", "expert", "ocid", "override"}
NOT_REJECTED = ProjectProcedure.status != "rejected"


def _404(what: str) -> HTTPException:
    return HTTPException(404, f"Nie znaleziono: {what}")


def link_status(links: list[ProjectProcedure]) -> str:
    if not links:
        return "unlinked"
    live = [lk for lk in links if lk.status != "rejected"]
    if not live:
        return "rejected"
    for lk in live:
        if lk.status in ("approved", "edited") or lk.method in KEY_METHODS or (lk.confidence or 0) >= 0.8:
            return "linked"
    return "uncertain"


def _counts(db: Session, ids: list[uuid.UUID]) -> dict[str, dict[uuid.UUID, int]]:
    def grp(col, *where):
        return dict(db.execute(select(col, func.count()).where(col.in_(ids), *where).group_by(col)).all())

    return {
        "procedures": grp(ProjectProcedure.project_id, NOT_REJECTED),
        "events": grp(Event.project_id, Event.status != "rejected"),
        "issues": grp(DataIssue.project_id, DataIssue.status != "rejected"),
        "pending_events": grp(Event.project_id, Event.status == "proposed"),
        "pending_links": grp(ProjectProcedure.project_id, ProjectProcedure.status == "proposed"),
    }


def _list_item(p: Project, ent: Entity | None, links: list[ProjectProcedure], counts: dict) -> dict[str, Any]:
    d = {c: getattr(p, c) for c in ProjectListItem.model_fields if hasattr(p, c)}
    d.update(beneficiary_name=ent.name if ent else None, beneficiary_nip=ent.nip if ent else None,
             subsector_extra=p.subsector_extra or [], tier=p.tier if p.tier in ("deep", "auto") else "deep",
             link_status=link_status(links),
             n_procedures=counts["procedures"].get(p.id, 0), n_events=counts["events"].get(p.id, 0),
             n_issues=counts["issues"].get(p.id, 0),
             n_pending_review=counts["pending_events"].get(p.id, 0) + counts["pending_links"].get(p.id, 0),
             completeness=(p.features or {}).get("completeness"))
    return d


def _project_or_404(db: Session, project_id: uuid.UUID) -> Project:
    p = db.get(Project, project_id)
    if not p:
        raise _404("projekt")
    return p


def _detail(db: Session, p: Project) -> ProjectDetail:
    ent = db.get(Entity, p.beneficiary_id) if p.beneficiary_id else None
    links = db.execute(select(ProjectProcedure).where(ProjectProcedure.project_id == p.id)).scalars().all()
    d = _list_item(p, ent, list(links), _counts(db, [p.id]))
    d.update(description=p.description, city=p.city, work_type=p.work_type, formula=p.formula, funding=p.funding,
             project_value=float(p.project_value) if p.project_value is not None else None,
             grant_value=float(p.grant_value) if p.grant_value is not None else None,
             annotation=p.annotation, features=p.features or {}, import_row=p.import_row, exemplary=p.exemplary,
             beneficiary=EntityOut.model_validate(ent) if ent else None)
    return ProjectDetail(**d)


@router.get("/projects", response_model=Page[ProjectListItem])
def list_projects(q: str | None = None, tier: str | None = "deep", status: str | None = None,
                  subsector: str | None = None, link_status: str | None = None,
                  offset: int = 0, limit: int = 50, db: Session = DB):
    query = select(Project, Entity).outerjoin(Entity, Entity.id == Project.beneficiary_id)
    if tier and tier != "all":
        query = query.where(Project.tier == tier)
    if status:
        query = query.where(Project.project_status == status)
    if subsector:
        query = query.where(or_(Project.subsector_main == subsector, Project.subsector_extra.contains([subsector])))
    if q:
        like = f"%{q}%"
        query = query.where(or_(Project.title.ilike(like), Project.code.ilike(like), Entity.name.ilike(like),
                                Entity.nip.ilike(like), Project.city.ilike(like), Project.public_id_value.ilike(like)))
    query = query.order_by(Project.code)
    if link_status:  # derived → filter in python (deep tier is small; auto tier is always "linked" by OCID)
        rows = db.execute(query).all()
        ids = [p.id for p, _ in rows]
    else:
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        rows = db.execute(query.offset(offset).limit(limit)).all()
        ids = [p.id for p, _ in rows]
    links: dict[uuid.UUID, list[ProjectProcedure]] = {}
    for lk in db.execute(select(ProjectProcedure).where(ProjectProcedure.project_id.in_(ids))).scalars():
        links.setdefault(lk.project_id, []).append(lk)
    counts = _counts(db, ids)
    items = [ProjectListItem(**_list_item(p, e, links.get(p.id, []), counts)) for p, e in rows]
    if link_status:
        items = [i for i in items if i.link_status == link_status]
        total = len(items)
        items = items[offset:offset + limit]
    return Page[ProjectListItem](items=items, total=total, offset=offset, limit=limit)


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: uuid.UUID, db: Session = DB):
    return _detail(db, _project_or_404(db, project_id))


@router.patch("/projects/{project_id}", response_model=ProjectDetail)
def patch_project(project_id: uuid.UUID, body: ProjectPatch, db: Session = DB, user: CurrentUser = EXPERT):
    from riskminer.review.audit import ReviewError, apply_action

    p = _project_or_404(db, project_id)
    try:
        apply_action(db, "project", p.id, "edit", user.username, changes=body.changes, comment=body.comment)
    except ReviewError as e:
        raise HTTPException(400, str(e)) from e
    db.commit()
    db.refresh(p)
    return _detail(db, p)


def _project_procedures(db: Session, project_id: uuid.UUID) -> list[tuple[ProjectProcedure, Procedure]]:
    return list(db.execute(select(ProjectProcedure, Procedure).join(Procedure, Procedure.id == ProjectProcedure.procedure_id)
                           .where(ProjectProcedure.project_id == project_id, NOT_REJECTED)
                           .order_by(ProjectProcedure.rank)).all())


def _contracts(db: Session, project_id: uuid.UUID) -> list[Contract]:
    out: list[Contract] = []
    for lk, proc in _project_procedures(db, project_id):
        q = select(Contract).where(Contract.procedure_id == proc.id)
        if lk.part_no:
            q = q.where(Contract.part_no == lk.part_no)
        out += db.execute(q.order_by(Contract.part_no)).scalars().all()
    return out


def _f(v):
    return float(v) if v is not None else None


def contract_out(db: Session, c: Contract) -> ContractOut:
    ent = db.get(Entity, c.contractor_id) if c.contractor_id else None
    changes = db.execute(select(ContractChange).where(ContractChange.contract_id == c.id)
                         .order_by(ContractChange.change_no)).scalars().all()
    d = {k: getattr(c, k) for k in ContractOut.model_fields if hasattr(c, k) and k not in ("contractor", "changes")}
    for k in ("value_gross", "value_net", "paid_gross"):
        d[k] = _f(d.get(k))
    d["contractor"] = EntityOut.model_validate(ent) if ent else None
    d["changes"] = [ContractChangeOut.model_validate(ch).model_copy(update={"value_delta": _f(ch.value_delta),
                                                                            "new_value": _f(ch.new_value)})
                    for ch in changes]
    return ContractOut(**d)


def procedure_out(p: Procedure) -> ProcedureOut:
    o = ProcedureOut.model_validate(p)
    return o.model_copy(update={"est_value_net": _f(p.est_value_net), "budget_gross": _f(p.budget_gross)})


@router.get("/projects/{project_id}/procedures", response_model=list[ProcedureOut])
def project_procedures(project_id: uuid.UUID, db: Session = DB):
    _project_or_404(db, project_id)
    return [procedure_out(p) for _, p in _project_procedures(db, project_id)]


@router.get("/projects/{project_id}/contracts", response_model=list[ContractOut])
def project_contracts(project_id: uuid.UUID, db: Session = DB):
    _project_or_404(db, project_id)
    return [contract_out(db, c) for c in _contracts(db, project_id)]


@router.get("/projects/{project_id}/notices", response_model=list[NoticeOut])
def project_notices(project_id: uuid.UUID, db: Session = DB):
    _project_or_404(db, project_id)
    ids = [p.id for _, p in _project_procedures(db, project_id)]
    if not ids:
        return []
    return db.execute(select(Notice).where(Notice.procedure_id.in_(ids)).order_by(Notice.published_at)).scalars().all()


@router.get("/projects/{project_id}/timeline", response_model=TimelineOut)
def project_timeline(project_id: uuid.UUID, db: Session = DB):
    p = _project_or_404(db, project_id)
    items: list[TimelineItem] = []
    procs = _project_procedures(db, project_id)
    for _, proc in procs:
        ev = [uuid.UUID(str(x)) for x in (proc.evidence_ids or [])[:3]]
        if proc.est_value_net is not None:
            items.append(TimelineItem(date=proc.first_published_at.date() if proc.first_published_at else None,
                                      kind="estimate", label="Wartość szacunkowa (netto)", value=_f(proc.est_value_net),
                                      evidence_ids=ev))
        if proc.budget_gross is not None:
            items.append(TimelineItem(date=proc.first_published_at.date() if proc.first_published_at else None,
                                      kind="budget", label="Kwota na sfinansowanie (brutto)", value=_f(proc.budget_gross),
                                      evidence_ids=ev))
        if proc.cancelled:
            items.append(TimelineItem(kind="cancelled", label=f"Unieważnienie ({proc.cancel_basis or 'podstawa ?'})",
                                      evidence_ids=ev))
        for n in db.execute(select(Notice).where(Notice.procedure_id == proc.id).order_by(Notice.published_at)).scalars():
            kind = "published" if n.notice_type == "ContractNotice" else "notice"
            items.append(TimelineItem(date=n.published_at.date() if n.published_at else None, kind=kind,
                                      label=f"{_NOTICE_PL.get(n.notice_type, n.notice_type)} {n.notice_number}",
                                      notice_id=n.id))
    pva: dict[str, Any] = {}
    for c in _contracts(db, project_id):
        if c.signed_at:
            items.append(TimelineItem(date=c.signed_at, kind="contract", label=f"Umowa (część {c.part_no or 1})",
                                      value=_f(c.value_gross), notice_id=c.result_notice_id))
        if c.planned_end:
            items.append(TimelineItem(date=c.planned_end, kind="planned_end", label="Planowany termin wykonania",
                                      planned=True))
        for ch in db.execute(select(ContractChange).where(ContractChange.contract_id == c.id)).scalars():
            items.append(TimelineItem(date=ch.change_date or ch.new_end, kind="change",
                                      label=f"Zmiana umowy nr {ch.change_no}" + (f" → termin {ch.new_end}" if ch.new_end else ""),
                                      value=_f(ch.new_value), notice_id=ch.notice_id,
                                      evidence_ids=[uuid.UUID(str(x)) for x in (ch.evidence_ids or [])[:3]]))
        if c.actual_end:
            items.append(TimelineItem(date=c.actual_end, kind="actual_end", label="Faktyczne wykonanie",
                                      notice_id=c.performing_notice_id))
        if c.paid_gross is not None:
            items.append(TimelineItem(date=c.actual_end, kind="paid", label="Wypłacone wynagrodzenie (brutto)",
                                      value=_f(c.paid_gross), notice_id=c.performing_notice_id))
        if not pva or (c.value_gross and _f(c.value_gross) > (pva.get("value") or 0)):
            delay = (c.actual_end - c.planned_end).days if c.actual_end and c.planned_end else None
            pva = {"planned_end": c.planned_end, "actual_end": c.actual_end, "delay_days": delay,
                   "value": _f(c.value_gross), "paid": _f(c.paid_gross), "n_changes": c.n_changes,
                   "on_time": c.on_time, "part_no": c.part_no}
    for e in db.execute(select(Event).where(Event.project_id == p.id, Event.status != "rejected")).scalars():
        items.append(TimelineItem(date=e.event_date, kind="event", label=e.title or e.event_type, notice_id=e.notice_id,
                                  evidence_ids=[uuid.UUID(str(x)) for x in (e.evidence_ids or [])[:3]]))
    items.sort(key=lambda i: (i.date is None, i.date or 0))
    return TimelineOut(project_id=p.id, items=items, planned_vs_actual=pva)


_NOTICE_PL = {"ContractNotice": "Ogłoszenie o zamówieniu", "TenderResultNotice": "Ogłoszenie o wyniku",
              "AgreementUpdateNotice": "Ogłoszenie o zmianie umowy",
              "ContractPerformingNotice": "Ogłoszenie o wykonaniu umowy"}


@router.get("/projects/{project_id}/graph", response_model=GraphOut)
def project_graph(project_id: uuid.UUID, db: Session = DB):
    p = _project_or_404(db, project_id)
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    def node(i, t, label, **data):
        nodes.setdefault(str(i), GraphNode(id=str(i), type=t, label=label, data=data))
        return str(i)

    pn = node(p.id, "project", p.code, title=p.title)
    if p.beneficiary_id:
        ent = db.get(Entity, p.beneficiary_id)
        if ent:
            edges.append(GraphEdge(source=node(ent.id, "entity", ent.name, nip=ent.nip, role="beneficjent"), target=pn,
                                   label="beneficjent"))
    links = db.execute(select(ProjectProcedure, Procedure).join(Procedure, Procedure.id == ProjectProcedure.procedure_id)
                       .where(ProjectProcedure.project_id == p.id)).all()
    for lk, proc in links:
        prn = node(proc.id, "procedure", proc.bzp_number or proc.ocid or "postępowanie", title=proc.title, ocid=proc.ocid)
        edges.append(GraphEdge(source=pn, target=prn, label=f"część {lk.part_no}" if lk.part_no else "postępowanie",
                               method=lk.method, confidence=lk.confidence, status=lk.status))
        for n in db.execute(select(Notice).where(Notice.procedure_id == proc.id)).scalars():
            edges.append(GraphEdge(source=prn, target=node(n.id, "notice", n.notice_number, type=n.notice_type),
                                   label=_NOTICE_PL.get(n.notice_type, n.notice_type)))
        for c in db.execute(select(Contract).where(Contract.procedure_id == proc.id)).scalars():
            cn = node(c.id, "contract", f"Umowa cz. {c.part_no or 1}", value=_f(c.value_gross))
            edges.append(GraphEdge(source=prn, target=cn, label="umowa"))
            if c.contractor_id:
                ent = db.get(Entity, c.contractor_id)
                if ent:
                    label = "osoba fizyczna" if ent.natural_person_flag else ent.name
                    edges.append(GraphEdge(source=cn, target=node(ent.id, "entity", label, nip=None if ent.natural_person_flag else ent.nip,
                                                                  role="wykonawca"), label="wykonawca"))
            for ch in db.execute(select(ContractChange).where(ContractChange.contract_id == c.id)).scalars():
                edges.append(GraphEdge(source=cn, target=node(ch.id, "change", f"Zmiana {ch.change_no}",
                                                              basis=ch.legal_basis_code), label="zmiana"))
    for e in db.execute(select(Event).where(Event.project_id == p.id, Event.status != "rejected")).scalars():
        en = node(e.id, "event", e.title or e.event_type, risk_codes=e.risk_codes)
        target = str(e.change_id or e.contract_id or e.procedure_id or p.id)
        edges.append(GraphEdge(source=target if target in nodes else pn, target=en, label="zdarzenie"))
    for d in db.execute(select(Document).where(Document.project_id == p.id)).scalars():
        edges.append(GraphEdge(source=pn, target=node(d.id, "document", d.title or d.file_name or "dokument",
                                                      doc_type=d.doc_type), label="dokument"))
    return GraphOut(nodes=list(nodes.values()), edges=edges)


@router.get("/procedures", response_model=Page[ProcedureOut])
def list_procedures(q: str | None = None, nip: str | None = None, tier: str | None = None,
                    offset: int = 0, limit: int = 50, db: Session = DB):
    query = select(Procedure)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Procedure.title.ilike(like), Procedure.ocid.ilike(like), Procedure.bzp_number.ilike(like)))
    if nip:
        query = query.where(Procedure.buyer_nip == nip)
    if tier:
        query = query.where(Procedure.tier == tier)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(Procedure.first_published_at.desc().nullslast()).offset(offset).limit(limit)).scalars()
    return Page[ProcedureOut](items=[procedure_out(p) for p in rows], total=total, offset=offset, limit=limit)


@router.get("/procedures/{procedure_id}", response_model=ProcedureOut)
def get_procedure(procedure_id: uuid.UUID, db: Session = DB):
    p = db.get(Procedure, procedure_id)
    if not p:
        raise _404("postępowanie")
    return procedure_out(p)


@router.get("/notices/{notice_id}", response_model=NoticeDetail)
def get_notice(notice_id: uuid.UUID, db: Session = DB):
    n = db.get(Notice, notice_id)
    if not n:
        n = db.execute(select(Notice).where(or_(Notice.object_id == str(notice_id)))).scalars().first()
    if not n:
        raise _404("ogłoszenie")
    d = NoticeOut.model_validate(n).model_dump()
    sections = []
    for s in n.sections or []:
        if isinstance(s, dict):
            sections.append(SectionOut(section=str(s.get("section") or s.get("no") or ""), label=s.get("label") or "",
                                       value=s.get("value") or s.get("text") or "", offset=s.get("offset") or s.get("start"),
                                       part_no=s.get("part_no")))
    return NoticeDetail(**d, canonical_text=n.canonical_text, sections=sections)


@router.get("/entities/{entity_id}", response_model=EntityOut)
def get_entity(entity_id: uuid.UUID, db: Session = DB):
    e = db.get(Entity, entity_id)
    if not e:
        raise _404("podmiot")
    return e
