"""Exports of any record set to JSON/CSV (owner: S3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from riskminer.api.deps import DB, Session

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
    from riskminer.export.records import bundle

    return Response(bundle(db), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=riskminer_eksport.zip"})


@router.get("/exports/{entity}")
def export_entity(entity: str, format: str = "json", project_id: str | None = None, status: str | None = None,
                  tier: str | None = "deep", db: Session = DB) -> Response:
    from riskminer.export.records import rows, to_csv, to_json

    if entity not in EXPORTABLE:
        raise HTTPException(404, f"Nieznany zbiór: {entity}")
    data = rows(db, entity, project_id=project_id, status=status, tier=tier if tier != "all" else None)
    if format == "csv":
        return Response(to_csv(data), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f"attachment; filename={entity}.csv"})
    return Response(to_json(data), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={entity}.json"})
