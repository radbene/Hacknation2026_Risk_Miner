"""JSON/CSV export of any record set + the example bundle (exports/przyklad)."""

from __future__ import annotations

import csv
import io
import json
import uuid
import zipfile
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.upsert import jsonable, row_dict
from riskminer import models as M

ENTITIES: dict[str, tuple[type, str | None]] = {
    "projects": (M.Project, "id"), "procedures": (M.Procedure, None), "notices": (M.Notice, None),
    "contracts": (M.Contract, None), "changes": (M.ContractChange, None), "links": (M.ProjectProcedure, "project_id"),
    "events": (M.Event, "project_id"), "issues": (M.DataIssue, "project_id"), "lessons": (M.Lesson, "project_id"),
    "clauses": (M.Clause, None), "analyses": (M.Analysis, None), "analysis_items": (M.AnalysisItem, None),
    "evidence": (M.Evidence, None), "reviews": (M.Review, None),
}
HEAVY = {"canonical_text", "sections", "tsv", "embedding", "import_row"}
LIMIT = 20000


def rows(session: Session, entity: str, project_id: str | None = None, status: str | None = None,
         tier: str | None = "deep") -> list[dict[str, Any]]:
    model, pcol = ENTITIES[entity]
    q = select(model)
    if project_id and pcol:
        q = q.where(getattr(model, pcol) == uuid.UUID(project_id))
    if status and hasattr(model, "status"):
        q = q.where(model.status == status)
    if tier and hasattr(model, "tier") and entity in ("projects", "procedures", "notices", "events"):
        q = q.where(model.tier == tier)
    out = []
    for obj in session.execute(q.limit(LIMIT)).scalars():
        d = {k: v for k, v in row_dict(obj).items() if k not in HEAVY}
        out.append(jsonable(d))
    return out


def to_json(data: list[dict[str, Any]]) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=1, default=str).encode("utf-8")


def to_csv(data: list[dict[str, Any]]) -> bytes:
    buf = io.StringIO()
    if not data:
        return b""
    cols = list(dict.fromkeys(k for d in data for k in d))
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for d in data:
        w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, dict | list) else v for k, v in d.items()})
    return buf.getvalue().encode("utf-8")


def bundle(session: Session, out_dir: Path | None = None) -> bytes:
    """Deep-tier record sets + links.csv + every analysis (JSON/CSV/DOCX) as one zip; optionally written to out_dir."""
    from riskminer.api.routers.analyses import analysis_out
    from riskminer.connectors.pipeline import links_csv
    from riskminer.export.analysis import to_csv as a_csv
    from riskminer.export.analysis import to_docx, to_json as a_json

    files: dict[str, bytes] = {"links.csv": links_csv(session).encode("utf-8")}
    for ent in ("projects", "links", "events", "issues", "lessons", "clauses", "reviews"):
        data = rows(session, ent)
        files[f"{ent}.json"] = to_json(data)
        files[f"{ent}.csv"] = to_csv(data)
    deep = {r["id"] for r in rows(session, "projects")}
    procs = [r for r in rows(session, "links")]
    pids = {r["procedure_id"] for r in procs if r["project_id"] in deep}
    for ent in ("procedures", "contracts", "changes"):
        data = [r for r in rows(session, ent, tier=None) if (r.get("procedure_id") or r.get("id")) in pids]
        files[f"{ent}.json"], files[f"{ent}.csv"] = to_json(data), to_csv(data)
    for a in session.execute(select(M.Analysis).order_by(M.Analysis.created_at)).scalars():
        out = analysis_out(session, a)
        stem = f"analizy/{(a.title or 'analiza')[:40].replace('/', '-').replace(' ', '_')}_{str(a.id)[:8]}"
        files[f"{stem}.json"], files[f"{stem}.csv"], files[f"{stem}.docx"] = a_json(out), a_csv(out), to_docx(out)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    if out_dir:
        for name, data in files.items():
            p = out_dir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    return buf.getvalue()
