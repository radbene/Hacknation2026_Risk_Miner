"""Path B – new-investment analysis (owner: S3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import Response

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
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


@router.post("/analyses/extract-features", response_model=FeatureExtractOut)
def extract_features(body: FeatureExtractIn, db: Session = DB):
    raise not_implemented(OWNER)


@router.post("/analyses", response_model=AnalysisOut)
def create_analysis(body: AnalysisCreateIn, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.get("/analyses", response_model=Page[AnalysisListItem])
def list_analyses(q: str | None = None, status: str | None = None, subsector: str | None = None,
                  offset: int = 0, limit: int = 50, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: uuid.UUID, db: Session = DB):
    raise not_implemented(OWNER)


@router.put("/analyses/{analysis_id}/features", response_model=AnalysisOut)
def update_features(analysis_id: uuid.UUID, body: Features, db: Session = DB, user: CurrentUser = USER):
    """Confirm/edit features → recompute."""
    raise not_implemented(OWNER)


@router.post("/analyses/{analysis_id}/recompute", response_model=AnalysisOut)
def recompute(analysis_id: uuid.UUID, db: Session = DB, user: CurrentUser = USER):
    raise not_implemented(OWNER)


@router.patch("/analyses/{analysis_id}/items/{item_id}", response_model=AnalysisItemOut)
def patch_item(analysis_id: uuid.UUID, item_id: uuid.UUID, body: AnalysisItemPatch, db: Session = DB,
               user: CurrentUser = USER):
    """Accept/reject an item; `excluded=true` on a neighbour triggers a recompute."""
    raise not_implemented(OWNER)


@router.get("/analyses/{analysis_id}/export")
def export_analysis(analysis_id: uuid.UUID, format: str = "json", db: Session = DB) -> Response:
    """format = json | csv | docx ("Karta analizy inwestycji")."""
    raise not_implemented(OWNER)
