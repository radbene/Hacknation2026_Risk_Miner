"""Fill subsector / work type / formula / scale features of case-base projects (rules only, deterministic).

Auto-tier projects come from BZP with only a title; the deep tier has the organizer's description. Each value
keeps its source and quote (FeatureValue), so the similarity breakdown can cite it. Expert-reviewed projects are
left untouched. Idempotent.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from riskminer.analysis.features import extract_rules
from riskminer.analysis.knowledge import rows as krows
from riskminer.models import Project

ROAD = re.compile(r"\b(ul\.|ulic\w*|drog\w*|dróg|jezdni\w*|chodnik\w*|ścieżk\w*|ronda|skrzyżowani\w*|nawierzchni\w*)", re.I)
SKIP = {"cues", "extra", "vat_basis", "value", "duration_months", "start_date", "funding"}


def cpv_map(session: Session | None = None) -> dict[str, str]:
    out: dict[str, str] = {}
    for rule in krows("subsector_rules", session):
        for c in rule.get("cpv") or []:
            out.setdefault(str(c), rule["subsector"])
    return out


def classify(session: Session, *, tier: str | None = None, only_missing: bool = True, batch: int = 2000,
             progress: Callable[[float, str], None] | None = None) -> dict[str, Any]:
    cmap = cpv_map(session)
    q = select(Project).where(Project.status.notin_(("approved", "edited")))
    if tier:
        q = q.where(Project.tier == tier)
    if only_missing:
        q = q.where(Project.subsector_main.is_(None))
    ids = list(session.execute(q.with_only_columns(Project.id)).scalars())
    cpv_by_project = dict(session.execute(text(
        "SELECT pp.project_id, max(pr.cpv_main) FROM project_procedure pp JOIN procedure pr ON pr.id = pp.procedure_id "
        "GROUP BY pp.project_id")).all())
    n_sub = 0
    for i in range(0, len(ids), batch):
        for p in session.execute(select(Project).where(Project.id.in_(ids[i:i + batch]))).scalars():
            src = "\n".join(x for x in (p.title, p.description) if x)
            f = extract_rules(src, session)
            ft = extract_rules(p.title or "", session)
            sub = ft.subsector_main.value if ft.subsector_main else None
            road = bool(ROAD.search(p.title or ""))
            if not sub and not road:
                sub = f.subsector_main.value if f.subsector_main else None
            elif not sub and road:  # road works with a water/sewer component: keep it as an extra subsector only
                extra = [f.subsector_main.value] if f.subsector_main else []
                p.subsector_extra = sorted(set((p.subsector_extra or []) + extra))
                p.features = {**(p.features or {}), "primary_object": "droga"}
            cpv = (cpv_by_project.get(p.id) or "")
            if not sub and not road and cpv:
                sub = cmap.get(cpv) or cmap.get(cpv[:8]) or next((v for k, v in cmap.items() if cpv.startswith(k.rstrip("0"))), None)
            if sub:
                n_sub += 1
            p.subsector_main = sub if not only_missing else (p.subsector_main or sub)
            if not p.subsector_extra and f.subsector_extra:
                p.subsector_extra = list(f.subsector_extra.value or [])
            p.work_type = p.work_type or (f.work_type.value if f.work_type else None)
            p.formula = p.formula or (f.formula.value if f.formula else None)
            feats = dict(p.features or {})
            for k, v in f.model_dump(exclude_none=True, mode="json").items():
                if k not in SKIP and k not in feats:
                    feats[k] = v
            p.features = feats
        session.commit()
        if progress:
            progress(min(1.0, (i + batch) / max(1, len(ids))), f"klasyfikacja {min(i + batch, len(ids))}/{len(ids)}")
    return {"projects": len(ids), "with_subsector": n_sub}
