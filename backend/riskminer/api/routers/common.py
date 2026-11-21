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
