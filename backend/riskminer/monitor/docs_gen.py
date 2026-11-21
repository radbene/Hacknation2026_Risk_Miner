"""Generated documentation fragments: ERD (mermaid) from models/tables.py, status table from docs/status.md."""

from __future__ import annotations

import re

from riskminer.core.config import REPO_ROOT
from riskminer.models import Base

_SKIP_COLS = {"created_at", "updated_at"}


def _type(col) -> str:
    t = type(col.type).__name__.lower()
    return {"uuid": "uuid", "string": "string", "text": "text", "integer": "int", "biginteger": "bigint",
            "numeric": "numeric", "float": "float", "boolean": "bool", "date": "date", "datetime": "timestamptz",
            "jsonb": "jsonb", "vector": "vector", "tsvector": "tsvector"}.get(t, t)


def erd_mermaid(compact: bool = False) -> str:
    """Mermaid erDiagram of every table; compact=True lists only keys + FK columns."""
    lines = ["erDiagram"]
    rels = []
    for t in Base.metadata.sorted_tables:
        cols = []
        for c in t.columns:
            if c.name in _SKIP_COLS:
                continue
            is_fk = bool(c.foreign_keys)
            if compact and not (c.primary_key or is_fk or c.unique):
                continue
            key = "PK" if c.primary_key else ("FK" if is_fk else ("UK" if c.unique else ""))
            cols.append(f"        {_type(c)} {c.name}{(' ' + key) if key else ''}")
            for fk in c.foreign_keys:
                rels.append(f'    {fk.column.table.name} ||--o{{ {t.name} : "{c.name}"')
        lines.append(f"    {t.name} {{")
        lines += cols
        lines.append("    }")
    return "\n".join(lines + sorted(set(rels)))


def status_table() -> str:
    """'działa' / 'zaprojektowane' table per session section from docs/status.md."""
    p = REPO_ROOT / "docs" / "status.md"
    if not p.exists():
        return ""
    sections: dict[str, dict[str, list[str]]] = {}
    cur, mode = None, None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur, mode = line[3:].strip(), None
            sections[cur] = {"działa": [], "zaprojektowane": [], "problemy": []}
            continue
        m = re.match(r"\*\*(Działa|Zaprojektowane|Znane problemy|Problemy)\*\*", line.strip(), re.I)
        if m:
            k = m.group(1).lower()
            mode = "działa" if k.startswith("dzia") else ("zaprojektowane" if k.startswith("zapro") else "problemy")
            continue
        if cur and mode and line.strip().startswith("- "):
            sections[cur][mode].append(line.strip()[2:])
    out = ["| Obszar | Działa | Zaprojektowane (nie wdrożone) |", "|---|---|---|"]
    for name, d in sections.items():
        if not (d["działa"] or d["zaprojektowane"]):
            continue
        out.append(f"| {name} | " + "<br>".join(d["działa"]) + " | " + "<br>".join(d["zaprojektowane"]) + " |")
    return "\n".join(out)
