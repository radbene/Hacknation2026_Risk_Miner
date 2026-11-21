"""Import & enrichment (owner: S1). Long work → job queue."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.cases import EnrichIn, HarvestIn, ImportReport
from riskminer.schemas.common import JobOut

router = APIRouter(tags=["imports"])
OWNER = "S1"


@router.post("/imports/xlsx", response_model=ImportReport)
async def import_xlsx(file: UploadFile = File(...), profile: str = "organizer", db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.post("/enrich", response_model=JobOut)
def enrich(body: EnrichIn, db: Session = DB, user: CurrentUser = USER):
    """Same as `riskminer enrich --all`: idempotent, returns a job whose result is the run report."""
    raise not_implemented(OWNER)


@router.post("/harvest", response_model=JobOut)
def harvest(body: HarvestIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)
