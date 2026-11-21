"""Expert knowledge: versioned tables, YAML import, sectors, clauses (owner: S5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from riskminer.api.deps import DB, CurrentUser, Session, require_role
from riskminer.knowledge import store
from riskminer.models import Clause, SectorProfile
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
EXPERT = require_role("expert")


def _summary(t) -> KnowledgeTableSummary:
    return KnowledgeTableSummary(sector=t.sector, name=t.name, title=t.title, version=t.version,
                                 n_rows=len(t.rows or []), edited_by=t.edited_by, updated_at=t.updated_at)


@router.get("/knowledge/sectors", response_model=list[SectorOut])
def sectors(db: Session = DB):
    """Sectors = folders under knowledge/ (+ their DB profile). A new sector is just new files."""
    profiles = {p.code: p for p in db.execute(select(SectorProfile)).scalars()}
    out = []
    for code in sorted(set(store.sectors_on_disk()) | set(profiles)):
        p = profiles.get(code)
        tables = [t.name for t in store.list_current(db, code)] or [f.stem for f in store.table_files(code)]
        out.append(SectorOut(code=code, name=p.name if p else store.SECTOR_NAMES.get(code, code),
                             knowledge_path=p.knowledge_path if p else f"knowledge/{code}",
                             active=p.active if p else bool(tables), tables=sorted(set(tables))))
    return out


@router.get("/knowledge/{sector}/tables", response_model=list[KnowledgeTableSummary])
def list_tables(sector: str, db: Session = DB):
    return [_summary(t) for t in store.list_current(db, sector)]


@router.get("/knowledge/{sector}/tables/{name}", response_model=KnowledgeTableOut)
def get_table(sector: str, name: str, version: int | None = None, db: Session = DB):
    t = store.current(db, sector, name, version)
    if t is None:
        raise HTTPException(404, "Brak tabeli wiedzy (uruchom import: POST /knowledge/{sector}/import)")
    return t


@router.get("/knowledge/{sector}/tables/{name}/versions", response_model=list[KnowledgeTableSummary])
def table_versions(sector: str, name: str, db: Session = DB):
    return [_summary(t) for t in store.versions(db, sector, name)]


@router.put("/knowledge/{sector}/tables/{name}", response_model=KnowledgeTableOut)
def save_table(sector: str, name: str, body: KnowledgeTableIn, db: Session = DB, user: CurrentUser = EXPERT):
    """Creates a new version (old ones are kept); every save is in the history."""
    cols = [c.model_dump(exclude_none=True) for c in body.columns] if body.columns else None
    t = store.save_version(db, sector, name, body.rows, columns=cols, actor=user.username, comment=body.comment)
    db.commit()
    return t


@router.post("/knowledge/{sector}/tables/{name}/restore/{version}", response_model=KnowledgeTableOut)
def restore_version(sector: str, name: str, version: int, db: Session = DB, user: CurrentUser = EXPERT):
    """Roll back = copy an old version as the new current one (history stays linear)."""
    old = store.current(db, sector, name, version)
    if old is None:
        raise HTTPException(404, "Brak wersji")
    t = store.save_version(db, sector, name, old.rows, columns=old.columns, actor=user.username,
                           comment=f"Przywrócono wersję {version}")
    db.commit()
    return t


@router.post("/knowledge/{sector}/import", response_model=KnowledgeImportReport)
def import_knowledge(sector: str, db: Session = DB, user: CurrentUser = EXPERT):
    """Re-import knowledge/<sector>/*.yaml into the DB (YAML itself is generated from the expert docx)."""
    if sector not in store.sectors_on_disk():
        raise HTTPException(404, f"Brak katalogu knowledge/{sector}")
    rep = store.load_sector(db, sector, actor=user.username)
    db.commit()
    return KnowledgeImportReport(sector=sector, files=rep["files"], tables=rep["tables"], written=rep["written"])


@router.get("/clauses", response_model=list[ClauseOut])
def list_clauses(risk_code: str | None = None, status: str | None = None, sector: str | None = None,
                 db: Session = DB):
    q = select(Clause).order_by(Clause.risk_code, Clause.code)
    if risk_code:
        q = q.where(Clause.risk_code == risk_code)
    if status:
        q = q.where(Clause.status == status)
    if sector:
        q = q.where(Clause.sector == sector)
    return db.execute(q).scalars().all()
