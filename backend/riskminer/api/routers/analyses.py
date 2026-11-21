"""Path B – new-investment analysis (owner: S3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select

from riskminer.api.deps import DB, USER, CurrentUser, Session
from riskminer.models import Analysis, AnalysisItem
from riskminer.schemas.analysis import (
    AnalysisCreateIn,
    AnalysisItemOut,
    AnalysisItemPatch,
    AnalysisListItem,
    AnalysisOut,
    FeatureExtractIn,
    FeatureExtractOut,
    Features,
)
from riskminer.schemas.common import Page

router = APIRouter(tags=["analyses"])
OWNER = "S3"


def analysis_out(db: Session, a: Analysis) -> AnalysisOut:
    items = db.execute(select(AnalysisItem).where(AnalysisItem.analysis_id == a.id).order_by(AnalysisItem.ord)).scalars()
    o = AnalysisOut.model_validate(a)
    return o.model_copy(update={"items": [AnalysisItemOut.model_validate(i) for i in items]})


def _get(db: Session, analysis_id: uuid.UUID) -> Analysis:
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Nie znaleziono analizy")
    return a


def _text_of(db: Session, text: str | None, document_ids: list[uuid.UUID]) -> str:
    from riskminer.models import Chunk

    parts = [text or ""]
    for did in document_ids:
        parts += [c.text for c in db.execute(select(Chunk).where(Chunk.document_id == did).order_by(Chunk.ord)
                                             .limit(200)).scalars()]
    return "\n".join(p for p in parts if p).strip()


@router.post("/analyses/extract-features", response_model=FeatureExtractOut)
def extract_features(body: FeatureExtractIn, db: Session = DB):
    from riskminer.analysis.features import extract_features as run

    text = _text_of(db, body.text, body.document_ids)
    if not text:
        raise HTTPException(400, "Podaj opis inwestycji albo dokument")
    return run(text, db, use_llm=True)


@router.post("/analyses", response_model=AnalysisOut)
def create_analysis(body: AnalysisCreateIn, db: Session = DB, user: CurrentUser = USER):
    from riskminer.analysis.run import create

    if not (body.text or body.document_ids or body.features):
        raise HTTPException(400, "Podaj opis, dokument albo cechy inwestycji")
    a = create(db, title=body.title, text=body.text,
               features=body.features.model_dump(mode="json", exclude_none=True) if body.features else None,
               params=body.params, document_ids=body.document_ids, project_id=body.project_id, actor=user.username)
    db.commit()
    return analysis_out(db, a)


@router.get("/analyses", response_model=Page[AnalysisListItem])
def list_analyses(q: str | None = None, status: str | None = None, subsector: str | None = None,
                  offset: int = 0, limit: int = 50, db: Session = DB):
    query = select(Analysis)
    if q:
        query = query.where(Analysis.title.ilike(f"%{q}%"))
    if status:
        query = query.where(Analysis.status == status)
    if subsector:
        query = query.where(Analysis.features["subsector_main"]["value"].astext == subsector)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(Analysis.created_at.desc()).offset(offset).limit(limit)).scalars().all()
    items = []
    for a in rows:
        sub = (a.features or {}).get("subsector_main")
        items.append(AnalysisListItem(id=a.id, title=a.title, status=a.status, created_at=a.created_at,
                                      created_by=a.created_by, subsector_main=sub.get("value") if isinstance(sub, dict) else sub,
                                      n_neighbours=(a.summary or {}).get("n_neighbours", 0),
                                      n_flags=(a.summary or {}).get("n_flags", 0)))
    return Page[AnalysisListItem](items=items, total=total, offset=offset, limit=limit)


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: uuid.UUID, db: Session = DB):
    return analysis_out(db, _get(db, analysis_id))


@router.put("/analyses/{analysis_id}/features", response_model=AnalysisOut)
def update_features(analysis_id: uuid.UUID, body: Features, db: Session = DB, user: CurrentUser = USER):
    """Confirm/edit features → recompute."""
    from riskminer.analysis.run import compute
    from riskminer.review.audit import record

    a = _get(db, analysis_id)
    before = {"features": a.features}
    a.features = body.model_dump(mode="json", exclude_none=True)
    record(db, "analysis", a, "edit", before, {"features": a.features}, user.username, "Zmiana cech inwestycji")
    compute(db, a, user.username)
    db.commit()
    return analysis_out(db, a)


@router.post("/analyses/{analysis_id}/recompute", response_model=AnalysisOut)
def recompute(analysis_id: uuid.UUID, db: Session = DB, user: CurrentUser = USER):
    from riskminer.analysis.run import compute

    a = _get(db, analysis_id)
    compute(db, a, user.username)
    db.commit()
    return analysis_out(db, a)


@router.patch("/analyses/{analysis_id}/items/{item_id}", response_model=AnalysisItemOut)
def patch_item(analysis_id: uuid.UUID, item_id: uuid.UUID, body: AnalysisItemPatch, db: Session = DB,
               user: CurrentUser = USER):
    """Accept/reject an item; `excluded=true` on a neighbour triggers a recompute."""
    import datetime as dt

    from riskminer.analysis.run import compute
    from riskminer.core.upsert import row_dict
    from riskminer.review.audit import record

    a = _get(db, analysis_id)
    it = db.get(AnalysisItem, item_id)
    if not it or it.analysis_id != a.id:
        raise HTTPException(404, "Nie znaleziono elementu analizy")
    before = row_dict(it)
    if body.payload is not None:
        it.payload = {**(it.payload or {}), **body.payload}
        it.status = "edited"
    if body.status:
        it.status = body.status
    if body.status or body.payload is not None:
        it.reviewed_by, it.reviewed_at = user.username, dt.datetime.now(dt.UTC)
    recompute_needed = False
    if body.excluded is not None and it.kind == "neighbour" and it.ref_project_id:
        it.excluded = body.excluded
        ids = {str(x) for x in a.excluded_project_ids or []}
        ids = ids | {str(it.ref_project_id)} if body.excluded else ids - {str(it.ref_project_id)}
        a.excluded_project_ids = sorted(ids)
        recompute_needed = True
    record(db, "analysis", a, "item_" + (body.status or ("exclude" if body.excluded else "edit")), before,
           row_dict(it), user.username, body.comment)
    db.flush()
    if recompute_needed:
        compute(db, a, user.username)
    db.commit()
    db.refresh(it)
    return it


@router.get("/analyses/{analysis_id}/export")
def export_analysis(analysis_id: uuid.UUID, format: str = "json", db: Session = DB) -> Response:
    """format = json | csv | docx ("Karta analizy inwestycji")."""
    from riskminer.export.analysis import to_csv, to_docx, to_json

    a = _get(db, analysis_id)
    out = analysis_out(db, a)
    safe = "analiza_" + str(a.id)[:8]
    if format == "csv":
        return Response(to_csv(out), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f"attachment; filename={safe}.csv"})
    if format == "docx":
        return Response(to_docx(out), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": f"attachment; filename={safe}.docx"})
    return Response(to_json(out), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={safe}.json"})
