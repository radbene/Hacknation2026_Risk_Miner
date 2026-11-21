"""Exports of any record set to JSON/CSV (owner: S3)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from riskminer.api.deps import DB, Session, not_implemented

router = APIRouter(tags=["exports"])
OWNER = "S3"

EXPORTABLE = ["projects", "procedures", "notices", "contracts", "changes", "links", "events", "issues",
              "lessons", "clauses", "analyses", "analysis_items", "evidence", "reviews"]


@router.get("/exports")
def list_exports() -> dict:
    return {"entities": EXPORTABLE, "formats": ["json", "csv"]}


@router.get("/exports/bundle.zip")
def export_bundle(db: Session = DB) -> Response:
    """Full example export (exports/przyklad)."""
    raise not_implemented(OWNER)


@router.get("/exports/{entity}")
def export_entity(entity: str, format: str = "json", project_id: str | None = None, status: str | None = None,
                  db: Session = DB) -> Response:
    raise not_implemented(OWNER)
