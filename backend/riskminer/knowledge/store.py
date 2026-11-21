"""Expert knowledge in the DB: versioned tables loaded from `knowledge/<sector>/*.yaml` (+ `extra/*.yaml`).

A sector is just a folder of files: `knowledge/<sector>/sector.yaml` (optional: name, cpv_prefixes) plus any
`<table>.yaml` with `{sector, name, rows: [...]}` (optional `title`, `columns`). No code changes.

    load_sector(session, "wodkan", actor="import")  -> report   # riskminer knowledge load [--sector]
    current(session, "wodkan", "thresholds")        -> KnowledgeTable | None  (highest version)
    rows(name, sector=None, session=None)           -> list[dict]  DB current version, falls back to YAML
    save_version(session, sector, name, rows, columns, actor, comment) -> new KnowledgeTable (old kept)

Readers (S1/S2/S3) should use `rows("subsector_rules")` etc. so edits made by the expert in the UI take effect
without code changes. Versioning: every change = new row (sector, name, version+1); the highest version is
current; a re-import of an unchanged file (same sha256 as any stored version) is a no-op, so UI edits are not
clobbered by `knowledge load`.
Derived tables: `risks` → `risk_category`, `clauses` (extra/clauses.yaml, written by S3) → `clause`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config, repo_path
from riskminer.core.upsert import jsonable
from riskminer.ids import make_id
from riskminer.models import Clause, KnowledgeTable, Review, RiskCategory, SectorProfile

SECTOR_NAMES = {"wodkan": "Wodociągi i kanalizacja", "drogi": "Drogi (P2)"}

TITLES = {
    "risks": "Katalog ryzyk R01–R15", "subsectors": "Podsektory", "phases": "Fazy inwestycji",
    "documents": "Typy dokumentów", "event_sources": "Zdarzenie → źródło", "art455": "Podstawy zmian (art. 455 Pzp)",
    "porady": "Porady eksperckie", "checklist": "Lista kontrolna (9 punktów)", "guide_sections": "Rozdziały poradnika",
    "sources": "Źródła informacji", "texts": "Teksty poradnika", "art455_map": "Art. 455 → typ zmiany i R-kody",
    "checklist_rcodes": "Lista kontrolna → R-kody", "completeness_states": "Stany kompletności danych",
    "event_rules": "Reguły zdarzeń", "risk_signals": "Sygnały ryzyka (wzorce)",
    "similarity_weights": "Wagi podobieństwa", "subsector_rules": "Reguły podsektorów (CPV, słowa kluczowe)",
    "thresholds": "Progi", "clauses": "Klauzule umowne", "llm_routing": "Routing modeli językowych",
}

LABELS = {
    "code": "Kod", "name": "Nazwa", "effects": "Skutki", "description": "Opis", "scope": "Zakres",
    "order": "Kolejność", "phase": "Faza", "documents": "Dokumenty", "group": "Grupa", "event": "Zdarzenie",
    "sources": "Źródła", "basis": "Podstawa", "meaning": "Znaczenie", "mechanic": "Mechanizm", "advice": "Porada",
    "no": "Nr", "item": "Punkt", "guide_sections": "Rozdziały", "level": "Poziom", "title": "Tytuł", "id": "Id",
    "text": "Treść", "change_type": "Typ zmiany", "note": "Uwagi", "status": "Status",
    "default_risk_codes": "Domyślne R-kody", "risk_codes": "R-kody", "risk_code": "R-kod", "applies_to": "Dotyczy",
    "state": "Stan", "label": "Etykieta", "event_type": "Typ zdarzenia", "source": "Źródło",
    "condition": "Warunek", "patterns": "Wzorce", "component": "Składnik", "weight": "Waga",
    "subsector": "Podsektor", "cpv": "CPV", "keywords": "Słowa kluczowe", "key": "Klucz", "value": "Wartość",
    "trigger": "Wyzwalacz", "legal_basis": "Podstawa prawna",
}
ENUMS = {"status": ["draft", "approved", "rejected"]}


def sectors_on_disk() -> list[str]:
    root = repo_path(get_config().knowledge_dir)
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def sector_dir(sector: str) -> Path:
    return repo_path(get_config().knowledge_dir) / sector


def infer_columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys: list[str] = []
    for r in rows:
        for k in r:
            if str(k) not in keys:
                keys.append(str(k))
    cols = []
    for k in keys:
        vals = [r.get(k) for r in rows if r.get(k) is not None]
        if k in ("risk_codes", "default_risk_codes") or (k == "risk_code"):
            typ = "rcodes"
        elif vals and all(isinstance(v, bool) for v in vals):
            typ = "bool"
        elif vals and all(isinstance(v, int | float) and not isinstance(v, bool) for v in vals):
            typ = "number"
        elif any(isinstance(v, list) for v in vals):
            typ = "list"
        elif k in ENUMS:
            typ = "enum"
        elif any(isinstance(v, str) and len(v) > 80 for v in vals):
            typ = "longtext"
        else:
            typ = "text"
        col = {"key": k, "label": LABELS.get(k, k.replace("_", " ").capitalize()), "type": typ}
        if typ == "enum":
            col["options"] = ENUMS[k]
        cols.append(col)
    return cols


def _read_yaml(path: Path) -> dict[str, Any] | None:
    raw = path.read_bytes()
    data = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        return None
    data["_sha256"] = hashlib.sha256(raw).hexdigest()
    return data


def table_files(sector: str) -> list[Path]:
    d = sector_dir(sector)
    if not d.exists():
        return []
    return sorted(p for p in [*d.glob("*.yaml"), *(d / "extra").glob("*.yaml")]
                  if p.name not in ("manifest.yaml", "sector.yaml"))


def current(session: Session, sector: str, name: str, version: int | None = None) -> KnowledgeTable | None:
    q = select(KnowledgeTable).where(KnowledgeTable.sector == sector, KnowledgeTable.name == name)
    q = q.where(KnowledgeTable.version == version) if version else q.order_by(KnowledgeTable.version.desc())
    return session.execute(q.limit(1)).scalars().first()


def list_current(session: Session, sector: str) -> list[KnowledgeTable]:
    sub = (select(KnowledgeTable.name, func.max(KnowledgeTable.version).label("v"))
           .where(KnowledgeTable.sector == sector).group_by(KnowledgeTable.name).subquery())
    q = (select(KnowledgeTable).join(sub, (KnowledgeTable.name == sub.c.name) & (KnowledgeTable.version == sub.c.v))
         .where(KnowledgeTable.sector == sector).order_by(KnowledgeTable.name))
    return list(session.execute(q).scalars())


def versions(session: Session, sector: str, name: str) -> list[KnowledgeTable]:
    return list(session.execute(select(KnowledgeTable).where(
        KnowledgeTable.sector == sector, KnowledgeTable.name == name).order_by(KnowledgeTable.version.desc())).scalars())


def save_version(session: Session, sector: str, name: str, rows: list[dict[str, Any]], *,
                 columns: list[dict[str, Any]] | None = None, actor: str | None, comment: str | None = None,
                 title: str | None = None, source_file: str | None = None,
                 source_sha256: str | None = None) -> KnowledgeTable:
    prev = current(session, sector, name)
    version = (prev.version + 1) if prev else 1
    rows = jsonable(rows)
    t = KnowledgeTable(
        id=make_id("knowledge_table", sector, name, version), sector=sector, name=name, version=version,
        title=title or (prev.title if prev else None) or TITLES.get(name, name),
        columns=columns or (prev.columns if prev and not _new_keys(prev.columns, rows) else infer_columns(rows)),
        rows=rows, source_file=source_file, source_sha256=source_sha256, edited_by=actor, comment=comment,
    )
    session.add(t)
    session.flush()
    session.add(Review(object_type="knowledge_table", object_id=t.id, action="create" if not prev else "edit",
                       before={"version": prev.version, "n_rows": len(prev.rows or [])} if prev else None,
                       after={"version": version, "n_rows": len(rows), **_row_diff(prev.rows if prev else [], rows)},
                       reviewer=actor, comment=comment or f"{sector}/{name} v{version}", at=dt.datetime.now(dt.UTC)))
    sync_derived(session, sector, name, rows, actor)
    return t


def _new_keys(columns: list[dict[str, Any]] | None, rows: list[dict[str, Any]]) -> bool:
    known = {c.get("key") for c in columns or []}
    return any(str(k) not in known for r in rows for k in r)


def _row_diff(old: list[dict], new: list[dict]) -> dict[str, int]:
    o = {yaml.safe_dump(r, sort_keys=True, allow_unicode=True) for r in old or []}
    n = {yaml.safe_dump(r, sort_keys=True, allow_unicode=True) for r in new or []}
    return {"rows_added": len(n - o), "rows_removed": len(o - n)}


def sync_derived(session: Session, sector: str, name: str, rows: list[dict[str, Any]], actor: str | None) -> int:
    """Keep the relational copies in step: risks → risk_category, clauses → clause."""
    n = 0
    if name == "risks":
        for r in rows:
            if not r.get("code"):
                continue
            rid = make_id("risk_category", sector, r["code"])
            rc = session.get(RiskCategory, rid)
            vals = {"name": r.get("name") or r["code"], "effects": r.get("effects"),
                    "description": r.get("description"), "keywords": r.get("keywords") or [],
                    "parent_code": r.get("parent_code")}
            if rc is None:
                rc = RiskCategory(id=rid, sector=sector, code=r["code"], method="import", confidence=1.0,
                                  status="approved", reviewed_by=actor or "import", version=1, **vals)
                session.add(rc)
            elif any(getattr(rc, k) != v for k, v in vals.items()):
                for k, v in vals.items():
                    setattr(rc, k, v)
                rc.version = (rc.version or 1) + 1
            n += 1
    elif name == "clauses":
        for i, r in enumerate(rows):
            code = r.get("code") or f"{sector}-K{i + 1:03d}"
            cid = make_id("clause", sector, code)
            c = session.get(Clause, cid)
            vals = {k: r.get(k) for k in ("risk_code", "title", "trigger", "legal_basis")}
            vals["text"] = r.get("text") or ""
            status = {"approved": "approved", "rejected": "rejected"}.get(str(r.get("status")), "proposed")
            if c is None:
                session.add(Clause(id=cid, sector=sector, code=code, method=r.get("method") or "import",
                                   status=status, evidence_ids=r.get("evidence_ids") or [], version=1, **vals))
            elif c.status == "proposed" and any(getattr(c, k) != v for k, v in vals.items()):
                for k, v in vals.items():
                    setattr(c, k, v)
                c.version = (c.version or 1) + 1
            elif c.status != "proposed":  # expert-reviewed clause: keep, store proposal
                diff = {k: v for k, v in vals.items() if getattr(c, k) != v}
                if diff:
                    c.proposal = diff
            n += 1
    session.flush()
    return n


def _sector_profile(session: Session, sector: str) -> SectorProfile:
    meta: dict[str, Any] = {}
    f = sector_dir(sector) / "sector.yaml"
    if f.exists():
        meta = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    sp = session.execute(select(SectorProfile).where(SectorProfile.code == sector)).scalars().first()
    if sp is None:
        sp = SectorProfile(id=make_id("sector_profile", sector), code=sector)
        session.add(sp)
    sp.name = meta.get("name") or SECTOR_NAMES.get(sector, sector)
    sp.knowledge_path = str(Path(get_config().knowledge_dir) / sector)
    sp.cpv_prefixes = meta.get("cpv_prefixes") or sp.cpv_prefixes or []
    sp.active = bool(meta.get("active", True))
    session.flush()
    return sp


def load_sector(session: Session, sector: str | None = None, actor: str = "import") -> dict[str, Any]:
    """Load every YAML table of a sector; unchanged files are skipped. Returns a report."""
    sector = sector or get_config().sector
    _sector_profile(session, sector)
    report: dict[str, Any] = {"sector": sector, "files": [], "tables": {}, "written": [], "unchanged": []}
    for path in table_files(sector):
        data = _read_yaml(path)
        if data is None:
            continue
        name = data.get("name") or path.stem
        rel = str(path.relative_to(repo_path(get_config().knowledge_dir).parent))
        report["files"].append(rel)
        report["tables"][name] = len(data["rows"])
        seen = session.execute(select(KnowledgeTable.id).where(
            KnowledgeTable.sector == sector, KnowledgeTable.name == name,
            KnowledgeTable.source_sha256 == data["_sha256"]).limit(1)).first()
        if seen:
            report["unchanged"].append(name)
            continue
        save_version(session, sector, name, data["rows"], columns=data.get("columns"), actor=actor,
                     title=data.get("title"), source_file=rel, source_sha256=data["_sha256"],
                     comment=f"Import z pliku {rel}")
        report["written"].append(name)
    return report


def rows(name: str, sector: str | None = None, session: Session | None = None) -> list[dict[str, Any]]:
    """Current rows of a knowledge table: DB (expert-edited) first, YAML file as a fallback."""
    sector = sector or get_config().sector
    own = session is None
    try:
        if own:
            from riskminer.core.db import SessionLocal
            session = SessionLocal()
        t = current(session, sector, name)
        if t is not None:
            return list(t.rows or [])
    except Exception:  # noqa: BLE001 – no DB (tests, offline scripts) → files
        pass
    finally:
        if own and session is not None:
            session.close()
    for path in table_files(sector):
        data = _read_yaml(path)
        if data and (data.get("name") or path.stem) == name:
            return list(data["rows"])
    return []
