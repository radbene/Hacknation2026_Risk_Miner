"""Expert knowledge: versioned tables, docx import, sectors, clauses (owner: S5)."""

from __future__ import annotations

from fastapi import APIRouter

from riskminer.api.deps import DB, USER, CurrentUser, Session, not_implemented
from riskminer.schemas.events import ClauseOut
from riskminer.schemas.knowledge import (
    KnowledgeImportReport,
    KnowledgeTableIn,
    KnowledgeTableOut,
    KnowledgeTableSummary,
    SectorOut,
)

router = APIRouter(tags=["knowledge"])
OWNER = "S5"


@router.get("/knowledge/sectors", response_model=list[SectorOut])
def sectors(db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/knowledge/{sector}/tables", response_model=list[KnowledgeTableSummary])
def list_tables(sector: str, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/knowledge/{sector}/tables/{name}", response_model=KnowledgeTableOut)
def get_table(sector: str, name: str, version: int | None = None, db: Session = DB):
    raise not_implemented(OWNER)


@router.get("/knowledge/{sector}/tables/{name}/versions", response_model=list[KnowledgeTableSummary])
def table_versions(sector: str, name: str, db: Session = DB):
    raise not_implemented(OWNER)


@router.put("/knowledge/{sector}/tables/{name}", response_model=KnowledgeTableOut)
def save_table(sector: str, name: str, body: KnowledgeTableIn, db: Session = DB, user: CurrentUser = USER):
    """Creates a new version; old ones are kept."""
    raise not_implemented(OWNER)


@router.post("/knowledge/{sector}/import", response_model=KnowledgeImportReport)
def import_knowledge(sector: str, db: Session = DB, user: CurrentUser = USER):
    """Re-import knowledge/<sector>/*.yaml into the DB (YAML itself is generated from the expert docx)."""
    raise not_implemented(OWNER)


@router.get("/clauses", response_model=list[ClauseOut])
def list_clauses(risk_code: str | None = None, status: str | None = None, db: Session = DB):
    raise not_implemented(OWNER)
