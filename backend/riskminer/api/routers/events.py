"""Events, risks, data issues, lessons, re-analysis (owner: S2)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
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


@router.get("/events", response_model=Page[EventOut])
def list_events(project_id: uuid.UUID | None = None, risk_code: str | None = None, event_type: str | None = None,
                status: str | None = None, tier: str | None = None, offset: int = 0, limit: int = 100, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.patch("/events/{event_id}", response_model=EventOut)
def patch_event(event_id: uuid.UUID, body: EventPatch, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/issues", response_model=list[DataIssueOut])
def project_issues(project_id: uuid.UUID, kind: str | None = None, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/completeness", response_model=CompletenessOut)
def project_completeness(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.post("/projects/{project_id}/extract", response_model=JobOut)
def extract_project(project_id: uuid.UUID, use_llm: bool = True, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/projects/{project_id}/reanalyze", response_model=ReanalysisDiff)
def reanalyze_project(project_id: uuid.UUID, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/risk-categories", response_model=list[RiskCategoryOut])
def list_risk_categories(sector: str = "wodkan", include_proposed: bool = True, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/lessons", response_model=Page[LessonOut])
def list_lessons(risk_code: str | None = None, source_kind: str | None = None, offset: int = 0, limit: int = 100,
                 db: Session = DB):
    raise not_implemented(OWNER)
