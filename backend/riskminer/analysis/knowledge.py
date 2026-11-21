"""Knowledge tables for the analysis: current DB version (`knowledge_table`), YAML fallback.

The DB row with the highest version per (sector, name) wins (experts edit it in "Wiedza ekspercka");
otherwise `knowledge/<sector>/extra/<name>.yaml` or `knowledge/<sector>/<name>.yaml`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config, repo_path
from riskminer.models import KnowledgeTable


def _yaml_path(name: str, sector: str) -> Path | None:
    base = repo_path(get_config().knowledge_dir) / sector
    for p in (base / "extra" / f"{name}.yaml", base / f"{name}.yaml"):
        if p.exists():
            return p
    return None


@lru_cache(maxsize=64)
def _yaml_rows(name: str, sector: str) -> tuple[tuple[dict[str, Any], ...], str | None]:
    p = _yaml_path(name, sector)
    if not p:
        return (), None
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return tuple(data.get("rows") or []), str(p.relative_to(repo_path(".")))


def load_table(name: str, session: Session | None = None, sector: str | None = None) -> dict[str, Any]:
    """Returns {"rows": [...], "source": "db:v3" | "yaml:<path>" | "missing", "version": int | None}."""
    sector = sector or get_config().sector
    if session is not None:
        try:
            row = session.execute(
                select(KnowledgeTable).where(KnowledgeTable.sector == sector, KnowledgeTable.name == name)
                .order_by(KnowledgeTable.version.desc()).limit(1)).scalars().first()
        except Exception:  # noqa: BLE001 – a broken DB must not stop rules-only analysis
            session.rollback()
            row = None
        if row is not None and row.rows:
            return {"rows": list(row.rows), "source": f"db:v{row.version}", "version": row.version}
    rows, path = _yaml_rows(name, sector)
    return {"rows": [dict(r) for r in rows], "source": f"yaml:{path}" if path else "missing", "version": None}


def rows(name: str, session: Session | None = None) -> list[dict[str, Any]]:
    return load_table(name, session)["rows"]


def thresholds(session: Session | None = None) -> dict[str, Any]:
    return {r["key"]: r.get("value") for r in rows("thresholds", session) if "key" in r}
