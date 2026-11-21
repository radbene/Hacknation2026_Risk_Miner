"""Evidence, jobs, health – implemented in Phase 0 (shared by everyone)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, text

from riskminer.api.deps import DB, Session
from riskminer.models import Evidence, Job
from riskminer.schemas.common import EvidenceOut, JobOut

router = APIRouter(tags=["common"])


@router.get("/health")
def health(db: Session = DB) -> dict:
    db.execute(text("SELECT 1"))
    return {"ok": True}


@router.get("/evidence/{evidence_id}", response_model=EvidenceOut)
def get_evidence(evidence_id: uuid.UUID, db: Session = DB):
    ev = db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(404, "Brak dowodu")
    return ev


@router.get("/evidence/{evidence_id}/context")
def evidence_context(evidence_id: uuid.UUID, db: Session = DB) -> dict:
    """What the source preview needs beyond the evidence row. xlsx cell → the whole spreadsheet row (headers in file
    order) with the cited column, so the UI can show the row and mark the cell."""
    from riskminer.models import Project, RawRecord

    ev = db.get(Evidence, evidence_id)
    if not ev:
        raise HTTPException(404, "Brak dowodu")
    loc = ev.locator or {}
    if ev.kind == "xlsx_cell":
        row, file = loc.get("row"), loc.get("file")
        p = db.execute(select(Project).where(Project.import_row["row"].astext == str(row),
                                             Project.import_row["file"].astext == str(file))).scalars().first()
        cells = ((p.import_row or {}).get("cells") or {}) if p else {}
        headers = []
        if ev.raw_record_id and (rr := db.get(RawRecord, ev.raw_record_id)) is not None:
            headers = list((rr.payload or {}).get("headers") or [])
        headers = [h for h in headers if h in cells] + [h for h in cells if h not in headers]
        return {"type": "sheet", "file": file, "sheet": loc.get("sheet"), "row": row, "column": loc.get("column"),
                "header": loc.get("header"), "cells": [{"header": h, "value": cells.get(h)} for h in headers],
                "project_id": str(p.id) if p else None, "project_code": p.code if p else None}
    if ev.notice_id:
        return {"type": "notice", "notice_id": str(ev.notice_id), "section": loc.get("section"), "quote": ev.quote,
                "field": loc.get("field")}
    if ev.document_id:
        return {"type": "document", "document_id": str(ev.document_id), "page": loc.get("page"), "quote": ev.quote}
    if ev.derivation:
        return {"type": "calculation"}
    return {"type": "other"}


@router.get("/evidence", response_model=list[EvidenceOut])
def get_evidence_batch(ids: list[uuid.UUID] = Query(default=[]), db: Session = DB):
    if not ids:
        return []
    return db.execute(select(Evidence).where(Evidence.id.in_(ids))).scalars().all()


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(kind: str | None = None, limit: int = 50, db: Session = DB):
    q = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if kind:
        q = q.where(Job.kind == kind)
    return db.execute(q).scalars().all()


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, db: Session = DB):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Brak zadania")
    return job
