"""Events, risks, data issues, lessons, re-analysis (owner: S2)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from riskminer.api.deps import DB, USER, CurrentUser, Session
from riskminer.core.jobs import enqueue
from riskminer.models import DataIssue, Event, Lesson, Project
from riskminer.schemas.common import JobOut, Page
from riskminer.schemas.events import (
    CompletenessOut,
    DataIssueOut,
    EventOut,
    EventPatch,
    LessonOut,
    ReanalysisDiff,
    RiskCategoryOut,
)

router = APIRouter(tags=["events"])
OWNER = "S2"


def event_out(e: Event, code: str | None = None) -> EventOut:
    o = EventOut.model_validate(e)
    return o.model_copy(update={"project_code": code, "effect_pln": float(e.effect_pln) if e.effect_pln is not None else None,
                                "risk_codes": [str(x) for x in e.risk_codes or []]})


def _event_or_404(db: Session, event_id: uuid.UUID) -> Event:
    e = db.get(Event, event_id)
    if not e:
        raise HTTPException(404, "Nie znaleziono zdarzenia")
    return e


def _code(db: Session, project_id) -> str | None:
    return db.scalar(select(Project.code).where(Project.id == project_id)) if project_id else None


@router.get("/events", response_model=Page[EventOut])
def list_events(project_id: uuid.UUID | None = None, risk_code: str | None = None, event_type: str | None = None,
                status: str | None = None, tier: str | None = None, offset: int = 0, limit: int = 100, db: Session = DB):
    q = select(Event, Project.code).outerjoin(Project, Project.id == Event.project_id)
    if project_id:
        q = q.where(Event.project_id == project_id)
    if risk_code:
        q = q.where(Event.risk_codes.contains([risk_code]))
    if event_type:
        q = q.where(Event.event_type == event_type)
    if status:
        q = q.where(Event.status == status)
    if tier:
        q = q.where(Event.tier == tier)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.execute(q.order_by(Project.code, Event.event_date.nullslast()).offset(offset).limit(limit)).all()
    return Page[EventOut](items=[event_out(e, c) for e, c in rows], total=total, offset=offset, limit=limit)


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: uuid.UUID, db: Session = DB):
    e = _event_or_404(db, event_id)
    return event_out(e, _code(db, e.project_id))


@router.patch("/events/{event_id}", response_model=EventOut)
def patch_event(event_id: uuid.UUID, body: EventPatch, db: Session = DB, user: CurrentUser = USER):
    from riskminer.review.audit import ReviewError, apply_action

    e = _event_or_404(db, event_id)
    try:
        apply_action(db, "event", e.id, "edit", user.username, changes=body.changes, comment=body.comment)
    except ReviewError as err:
        raise HTTPException(400, str(err)) from err
    db.commit()
    db.refresh(e)
    return event_out(e, _code(db, e.project_id))


@router.get("/projects/{project_id}/issues", response_model=list[DataIssueOut])
def project_issues(project_id: uuid.UUID, kind: str | None = None, db: Session = DB):
    q = select(DataIssue).where(DataIssue.project_id == project_id)
    if kind:
        q = q.where(DataIssue.kind == kind)
    return db.execute(q.order_by(DataIssue.kind, DataIssue.field)).scalars().all()


@router.get("/projects/{project_id}/completeness", response_model=CompletenessOut)
def project_completeness(project_id: uuid.UUID, db: Session = DB):
    from riskminer.extract.completeness import compute

    if not db.get(Project, project_id):
        raise HTTPException(404, "Nie znaleziono projektu")
    score, items = compute(db, project_id)
    p = db.get(Project, project_id)
    p.features = {**(p.features or {}), "completeness": round(score, 3)}
    db.commit()
    return CompletenessOut(project_id=project_id, score=score, items=[DataIssueOut.model_validate(i) for i in items])


@router.post("/projects/{project_id}/extract", response_model=JobOut)
def extract_project(project_id: uuid.UUID, use_llm: bool = True, db: Session = DB, user: CurrentUser = USER):
    if not db.get(Project, project_id):
        raise HTTPException(404, "Nie znaleziono projektu")
    return enqueue(db, "extract", {"project_ids": [str(project_id)], "use_llm": use_llm}, user=user.username)


@router.post("/projects/{project_id}/reanalyze", response_model=ReanalysisDiff)
def reanalyze_project(project_id: uuid.UUID, db: Session = DB, user: CurrentUser = USER):
    """Rerun rules (+ completeness) for one project and diff against the previous events."""
    from riskminer.extract.completeness import compute
    from riskminer.extract.rules import extract_project as run

    if not db.get(Project, project_id):
        raise HTTPException(404, "Nie znaleziono projektu")
    before = {e.id: event_out(e) for e in db.execute(select(Event).where(Event.project_id == project_id)).scalars()}
    rep = run(db, project_id)
    compute(db, project_id)
    db.commit()
    code = _code(db, project_id)
    after = {e.id: e for e in db.execute(select(Event).where(Event.project_id == project_id)).scalars()}
    diff = ReanalysisDiff(project_id=project_id)
    for eid, res in rep.results.items():
        e = after.get(uuid.UUID(str(eid)))
        if e is None:
            continue
        if res == "inserted":
            diff.new.append(event_out(e, code))
        elif res in ("updated", "proposal"):
            diff.changed.append({"event": event_out(e, code).model_dump(mode="json"),
                                 "before": before[e.id].model_dump(mode="json") if e.id in before else None,
                                 "proposal": e.proposal})
        else:
            diff.confirmed.append(event_out(e, code))
    seen = {uuid.UUID(str(i)) for i in rep.results}
    diff.closed = [b.model_copy(update={"project_code": code}) for i, b in before.items() if i not in seen]
    return diff


@router.get("/risk-categories", response_model=list[RiskCategoryOut])
def list_risk_categories(sector: str = "wodkan", include_proposed: bool = True, db: Session = DB):
    from riskminer.extract.catalog import list_categories

    return list_categories(db, sector, include_proposed=include_proposed)


@router.get("/lessons", response_model=Page[LessonOut])
def list_lessons(risk_code: str | None = None, source_kind: str | None = None, offset: int = 0, limit: int = 100,
                 db: Session = DB):
    q = select(Lesson)
    if risk_code:
        q = q.where(Lesson.risk_codes.contains([risk_code]))
    if source_kind:
        q = q.where(Lesson.source_kind == source_kind)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.execute(q.order_by(Lesson.created_at.desc()).offset(offset).limit(limit)).scalars().all()
    return Page[LessonOut](items=rows, total=total, offset=offset, limit=limit)
