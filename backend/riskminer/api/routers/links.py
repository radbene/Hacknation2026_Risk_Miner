"""Project ↔ procedure links (owner: S1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.cases import LinkCandidate, LinkOut, RelinkIn
from riskminer.schemas.common import Page

router = APIRouter(tags=["links"])
OWNER = "S1"


@router.get("/links", response_model=Page[LinkOut])
def list_links(project_id: uuid.UUID | None = None, status: str | None = None, max_confidence: float | None = None,
               offset: int = 0, limit: int = 100, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/links/export.csv", response_class=PlainTextResponse)
def export_links_csv(db: Session = DB):
    """links.csv: project, procedure/notice, part, method, confidence, components with evidence, status."""
    raise not_implemented(OWNER)


@router.get("/projects/{project_id}/candidates", response_model=list[LinkCandidate])
def link_candidates(project_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.post("/projects/{project_id}/relink", response_model=LinkOut)
def relink(project_id: uuid.UUID, body: RelinkIn, db: Session = DB, user: CurrentUser = USER):
    """Expert relink: pick a candidate, or give an OCID / notice number (fetches it). Stored as override."""
    raise not_implemented(OWNER)
