"""Path A step 3 (S2 modules, wired by the main session): rule events + LLM causes + completeness per project."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.models import Project


def extract(session: Session, project_ids: list[uuid.UUID] | None = None, *, use_llm: bool = False,
            tier: str = "deep", progress: Callable[[float, str], None] | None = None) -> dict[str, Any]:
    from riskminer.extract.completeness import compute
    from riskminer.extract.rules import Report, extract_project

    q = select(Project).where(Project.tier == tier)
    if project_ids:
        q = select(Project).where(Project.id.in_(project_ids))
    projects = session.execute(q.order_by(Project.code)).scalars().all()
    rep = Report()
    per_project = []
    for i, p in enumerate(projects):
        n0 = len(rep.results)
        extract_project(session, p.id, rep)
        score, issues = compute(session, p.id)
        p.features = {**(p.features or {}), "completeness": round(score, 3)}
        session.commit()
        per_project.append({"project": p.code, "events": len(rep.results) - n0, "completeness": round(score, 3),
                            "issues": len(issues)})
        if progress:
            progress((i + 1) / max(1, len(projects)) * (0.7 if use_llm else 1.0), f"{p.code}: zdarzenia i kompletność")
    out = rep.as_dict() | {"projects": per_project}
    if use_llm:
        from riskminer.extract.llm_extract import enrich_events

        llm = {}
        for p in projects:
            for k, v in enrich_events(session, project_id=p.id).items():
                llm[k] = llm.get(k, 0) + v
            session.commit()
        out["llm"] = llm
    return out
