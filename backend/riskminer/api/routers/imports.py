"""Import & enrichment (owner: S1). Long work → job queue."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from riskminer.api.deps import DB, EXPERT, CurrentUser, Session
from riskminer.core.jobs import enqueue
from riskminer.schemas.cases import EnrichIn, HarvestIn, ImportReport
from riskminer.schemas.common import JobOut

router = APIRouter(tags=["imports"])
OWNER = "S1"


@router.post("/imports/xlsx", response_model=ImportReport)
async def import_xlsx(file: UploadFile = File(...), profile: str = "organizer", db: Session = DB, user: CurrentUser = EXPERT):
    from riskminer.connectors.xlsx_import import PROFILES, import_file

    if profile not in PROFILES:
        raise HTTPException(400, f"Nieznany profil importu: {profile}")
    data = await file.read()
    try:
        rep = import_file(db, data, file.filename or "upload.xlsx", profile=profile, actor=user.username)
    except (ValueError, KeyError) as e:
        db.rollback()
        raise HTTPException(400, f"Nie udało się odczytać pliku: {e}") from e
    db.commit()
    return ImportReport(**{k: rep.get(k) for k in ImportReport.model_fields if k in rep})


@router.post("/enrich", response_model=JobOut)
def enrich(body: EnrichIn, db: Session = DB, user: CurrentUser = EXPERT):
    """Same as `riskminer enrich --all`: idempotent, returns a job whose result is the run report."""
    params = body.model_dump(mode="json") | {"actor": user.username}
    return enqueue(db, "enrich", params, user=user.username)


@router.post("/harvest", response_model=JobOut)
def harvest(body: HarvestIn, db: Session = DB, user: CurrentUser = EXPERT):
    return enqueue(db, "harvest", body.model_dump(mode="json"), user=user.username)
