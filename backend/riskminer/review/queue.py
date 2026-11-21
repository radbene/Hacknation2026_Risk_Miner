"""Expert queue: union across all reviewable tables, proposed first, uncertain on top.

Ordering: rows with a pending rerun `proposal` first, then by uncertainty (1 - confidence, missing = 0.5),
then newest. Each item carries a readable title/summary, project code and evidence ids.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from riskminer import models
from riskminer.models import Procedure, Project, ProjectProcedure, ReviewStatus

_LABEL = {
    "project": "Projekt", "project_procedure": "Powiązanie", "contract": "Umowa", "contract_change": "Zmiana umowy",
    "fact": "Fakt", "document": "Dokument", "risk_category": "Kategoria ryzyka", "lesson": "Wniosek (lekcja)",
    "clause": "Klauzula", "event": "Zdarzenie", "data_issue": "Brak/sprzeczność danych", "analysis": "Analiza",
    "analysis_item": "Element analizy",
}


def _cut(s: Any, n: int = 240) -> str | None:
    if s is None:
        return None
    s = str(s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _title_summary(t: str, o: Any, procs: dict[uuid.UUID, Procedure]) -> tuple[str, str | None]:
    if t == "project":
        return f"{o.code}: {o.title}", _cut(o.description)
    if t == "project_procedure":
        p = procs.get(o.procedure_id)
        ref = (p.bzp_number or p.ocid) if p else str(o.procedure_id)
        part = f", część {o.part_no}" if o.part_no else ""
        comps = ", ".join(f"{c.get('name')}={c.get('score')}" for c in (o.components or [])[:4] if isinstance(c, dict))
        return f"Powiązanie z postępowaniem {ref}{part}", _cut((p.title if p else "") + (f" · {comps}" if comps else ""))
    if t == "contract":
        p = procs.get(o.procedure_id)
        return (f"Umowa{f' część {o.part_no}' if o.part_no else ''} – {p.bzp_number if p else ''}".strip(" –"),
                _cut(f"wartość {o.value_gross} zł brutto, termin {o.planned_end}, wykonano {o.actual_end}"))
    if t == "contract_change":
        return (f"Zmiana umowy nr {o.change_no}" + (f" ({o.legal_basis_code})" if o.legal_basis_code else ""),
                _cut(o.reason or o.description))
    if t == "fact":
        val = o.value_num if o.value_num is not None else (o.value_text or o.value_date)
        return f"{o.fact_type} = {val}{' ' + o.unit if o.unit else ''}", None
    if t == "document":
        return o.title or o.file_name or "Dokument", _cut(f"{o.doc_type or ''} {o.phase or ''}".strip() or None)
    if t == "risk_category":
        return f"{o.code} {o.name}", _cut(o.effects or o.description)
    if t == "lesson":
        return o.title or "Wniosek", _cut(o.cause or o.recommendation)
    if t == "clause":
        return f"{o.code or ''} {o.title or ''}".strip() or "Klauzula", _cut(o.text)
    if t == "event":
        codes = ",".join(o.risk_codes or [])
        return (o.title or o.event_type) + (f" [{codes}]" if codes else ""), _cut(o.cause or o.quote or o.signal)
    if t == "data_issue":
        return f"{o.kind}: {o.field or ''}".strip(": "), _cut(o.message)
    if t == "analysis":
        return o.title, None
    if t == "analysis_item":
        return o.title or o.kind, _cut((o.payload or {}).get("summary") if isinstance(o.payload, dict) else None)
    return _LABEL.get(t, t), None


def _project_filter(t: str, model: type, project_id: uuid.UUID):
    if t == "project":
        return model.id == project_id
    cols = model.__table__.columns
    if "project_id" in cols:
        return model.project_id == project_id
    if "procedure_id" in cols:
        sub = select(ProjectProcedure.procedure_id).where(ProjectProcedure.project_id == project_id)
        return model.procedure_id.in_(sub)
    return None


def queue(session: Session, *, object_type: str | None = None, project_id: uuid.UUID | None = None,
          status: str = "proposed", offset: int = 0, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
    types = [object_type] if object_type else list(models.REVIEWABLE)
    rows: list[tuple[str, Any]] = []
    total = 0
    for t in types:
        model = getattr(models, models.REVIEWABLE[t])
        q = select(model)
        if status == "proposed":
            q = q.where(or_(model.status == ReviewStatus.proposed.value, model.proposal.is_not(None)))
        elif status != "all":
            q = q.where(model.status == status)
        if project_id is not None:
            f = _project_filter(t, model, project_id)
            if f is None:
                continue
            q = q.where(f)
        total += session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        q = q.order_by(model.proposal.is_(None), func.coalesce(model.confidence, 0.5), model.created_at.desc())
        rows += [(t, o) for o in session.execute(q.limit(offset + limit)).scalars()]

    def key(r: tuple[str, Any]):
        o = r[1]
        conf = o.confidence if o.confidence is not None else 0.5
        return (o.proposal is None, conf, -(o.created_at.timestamp() if o.created_at else 0))

    rows.sort(key=key)
    rows = rows[offset: offset + limit]

    proc_ids = {o.procedure_id for t, o in rows if hasattr(o, "procedure_id") and o.procedure_id}
    procs = {p.id: p for p in session.execute(select(Procedure).where(Procedure.id.in_(proc_ids))).scalars()} \
        if proc_ids else {}
    pids: dict[int, uuid.UUID | None] = {}
    for i, (t, o) in enumerate(rows):
        pids[i] = o.id if t == "project" else getattr(o, "project_id", None)
    missing = [o.procedure_id for i, (t, o) in enumerate(rows) if pids[i] is None and getattr(o, "procedure_id", None)]
    via_proc: dict[uuid.UUID, uuid.UUID] = {}
    if missing:
        for pp in session.execute(select(ProjectProcedure).where(ProjectProcedure.procedure_id.in_(missing))).scalars():
            via_proc.setdefault(pp.procedure_id, pp.project_id)
    for i, (_t, o) in enumerate(rows):
        if pids[i] is None and getattr(o, "procedure_id", None):
            pids[i] = via_proc.get(o.procedure_id)
    codes = {p.id: p.code for p in session.execute(
        select(Project).where(Project.id.in_({v for v in pids.values() if v}))).scalars()} if any(pids.values()) else {}

    items = []
    for i, (t, o) in enumerate(rows):
        title, summary = _title_summary(t, o, procs)
        conf = o.confidence
        items.append({
            "object_type": t, "object_id": o.id, "title": f"{_LABEL[t]}: {title}", "summary": summary,
            "status": o.status, "method": o.method, "confidence": conf,
            "uncertainty": None if conf is None else round(1 - conf, 4),
            "project_id": pids[i], "project_code": codes.get(pids[i]) if pids[i] else None,
            "evidence_ids": [e for e in (o.evidence_ids or []) if _is_uuid(e)],
            "has_proposal": bool(o.proposal), "created_at": o.created_at,
        })
    return items, total


def _is_uuid(v: Any) -> bool:
    try:
        uuid.UUID(str(v))
        return True
    except ValueError:
        return False


def counts(session: Session) -> dict[str, int]:
    """Pending (proposed or with proposal) per object type – for the dashboard badge."""
    out = {}
    for t, name in models.REVIEWABLE.items():
        m = getattr(models, name)
        out[t] = session.execute(select(func.count()).select_from(m).where(
            or_(m.status == ReviewStatus.proposed.value, m.proposal.is_not(None)))).scalar_one()
    return out
