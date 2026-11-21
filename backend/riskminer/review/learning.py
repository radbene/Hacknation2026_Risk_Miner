"""Learning loop: expert decisions become rules/examples that the pipeline reads on the next run.

Interface for other sessions (all read-only helpers take an open SQLAlchemy session):

    from riskminer.review import learning

    learning.get_few_shot(session, "causes", k=3)
        -> [{"object_type", "object_id", "input": str, "output": dict}]   # S2/S3 prompts (few-shot)
        Exemplary items (expert clicked "wzorcowy") first, then recently approved/edited ones.
        Tasks: causes | doc_fragments | lessons | clauses | recommendations | category_proposal | features.

    learning.blacklist(session, "event")          -> set[str]  ids rejected by an expert
    learning.is_blacklisted(session, "project_procedure", id) -> bool
        Rejections are stored as `rule(kind="blacklist", key="<object_type>:<id>")`; ids are uuid5 from natural
        keys, so the same candidate produced by a rebuild has the same id and must be skipped / kept rejected.

    learning.link_overrides(session)              -> [{"project_id", "procedure_id", "part_no", "ocid",
                                                       "notice_number", "mode": "force" | "forbid", ...}]
        S1's linker applies these after every rebuild: `force` = expert relink (always link, confidence 1.0,
        method "expert", is_override=True); `forbid` = rejected link (never propose this pair again).
        Stored as `rule(kind="link_override")`, so they survive truncating/rebuilding project_procedure.

    learning.recommendation_sources(session, risk_codes=None)
        -> {"clauses": [...], "lessons": [...]}   approved/edited clauses and lessons for S3's recommendations.

Writers (called by review/audit.py; other sessions don't need them): on_reject, on_reopen, on_exemplary,
add_link_override, put_rule (versioned: a changed body = new version, the previous one is deactivated).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config
from riskminer.core.upsert import jsonable
from riskminer.ids import make_id
from riskminer.models import Clause, Event, Lesson, ReviewStatus, RiskCategory, Rule

APPROVED = (ReviewStatus.approved.value, ReviewStatus.edited.value)

# task -> (object_type, filter) used for few-shot examples
TASK_SOURCES: dict[str, tuple[str, dict[str, Any]]] = {
    "causes": ("event", {"not_event_type": "doc_fragment"}),
    "doc_fragments": ("event", {"event_type": "doc_fragment"}),
    "lessons": ("lesson", {}),
    "clauses": ("clause", {}),
    "recommendations": ("lesson", {}),
    "category_proposal": ("risk_category", {}),
}


def _sector(sector: str | None) -> str:
    return sector or get_config().sector


# ---------------------------------------------------------------- rules (versioned)


def latest_rule(session: Session, kind: str, key: str, sector: str | None = None) -> Rule | None:
    return session.execute(
        select(Rule).where(Rule.sector == _sector(sector), Rule.kind == kind, Rule.key == key)
        .order_by(Rule.version.desc()).limit(1)
    ).scalars().first()


def put_rule(session: Session, kind: str, key: str, body: dict[str, Any], actor: str | None,
             sector: str | None = None, active: bool = True) -> Rule:
    sector = _sector(sector)
    body = jsonable(body)
    cur = latest_rule(session, kind, key, sector)
    if cur is not None and cur.body == body and cur.active == active:
        return cur
    version = (cur.version + 1) if cur else 1
    if cur is not None:
        cur.active = False
    rule = Rule(id=make_id("rule", sector, kind, key, version), sector=sector, kind=kind, key=key,
                version=version, body=body, active=active, created_by=actor)
    session.add(rule)
    session.flush()
    return rule


def deactivate_rule(session: Session, kind: str, key: str, actor: str | None, sector: str | None = None) -> None:
    cur = latest_rule(session, kind, key, sector)
    if cur is not None and cur.active:
        put_rule(session, kind, key, cur.body, actor, sector, active=False)


def active_rules(session: Session, kind: str, sector: str | None = None) -> list[Rule]:
    """Latest version per key, active only."""
    sector = _sector(sector)
    sub = (select(Rule.key, func.max(Rule.version).label("v"))
           .where(Rule.sector == sector, Rule.kind == kind).group_by(Rule.key).subquery())
    q = (select(Rule).join(sub, (Rule.key == sub.c.key) & (Rule.version == sub.c.v))
         .where(Rule.sector == sector, Rule.kind == kind, Rule.active.is_(True)))
    return list(session.execute(q).scalars())


# ---------------------------------------------------------------- hooks from audit


def _key(object_type: str, object_id: Any) -> str:
    return f"{object_type}:{object_id}"


def _natural(object_type: str, obj: Any) -> dict[str, Any]:
    fields = {
        "project_procedure": ("project_id", "procedure_id", "part_no", "method", "confidence"),
        "event": ("event_type", "project_id", "notice_id", "document_id", "change_id", "quote", "risk_codes"),
        "risk_category": ("code", "name"),
        "clause": ("code", "risk_code", "title"),
        "lesson": ("title", "project_id"),
    }.get(object_type, ())
    return {f: jsonable(getattr(obj, f, None)) for f in fields}


def on_reject(session: Session, object_type: str, obj: Any, reviewer: str, comment: str | None) -> None:
    sector = getattr(obj, "sector", None)
    put_rule(session, "blacklist", _key(object_type, obj.id),
             {"object_type": object_type, "object_id": str(obj.id), "comment": comment, **_natural(object_type, obj)},
             reviewer, sector)
    if object_type == "project_procedure":
        add_link_override(session, mode="forbid", project_id=obj.project_id, procedure_id=obj.procedure_id,
                          part_no=obj.part_no, actor=reviewer, comment=comment)


def on_reopen(session: Session, object_type: str, obj: Any, reviewer: str) -> None:
    sector = getattr(obj, "sector", None)
    deactivate_rule(session, "blacklist", _key(object_type, obj.id), reviewer, sector)
    if object_type == "project_procedure":
        deactivate_rule(session, "link_override", _link_key(obj.project_id, obj.procedure_id, obj.part_no), reviewer)


def on_exemplary(session: Session, object_type: str, obj: Any, reviewer: str, on: bool) -> None:
    sector = getattr(obj, "sector", None)
    key = _key(object_type, obj.id)
    if on:
        put_rule(session, "few_shot", key, {"object_type": object_type, "object_id": str(obj.id)}, reviewer, sector)
    else:
        deactivate_rule(session, "few_shot", key, reviewer, sector)


def _link_key(project_id: Any, procedure_id: Any = None, part_no: Any = None, ref: str | None = None) -> str:
    return f"{project_id}:{procedure_id or ref}:{part_no or 0}"


def add_link_override(session: Session, *, mode: str, project_id: Any, actor: str | None,
                      procedure_id: Any = None, part_no: int | None = None, ocid: str | None = None,
                      notice_number: str | None = None, replaces: Any = None, comment: str | None = None) -> Rule:
    """mode=force (expert relink) | forbid (rejected pair). Survives rebuilds of project_procedure."""
    if mode not in ("force", "forbid"):
        raise ValueError(mode)
    key = _link_key(project_id, procedure_id, part_no, ocid or notice_number)
    body = {"mode": mode, "project_id": project_id, "procedure_id": procedure_id, "part_no": part_no,
            "ocid": ocid, "notice_number": notice_number, "replaces": replaces, "comment": comment}
    return put_rule(session, "link_override", key, body, actor)


# ---------------------------------------------------------------- readers for S1/S2/S3


def blacklist(session: Session, object_type: str, sector: str | None = None) -> set[str]:
    return {r.body.get("object_id") for r in active_rules(session, "blacklist", sector)
            if r.body.get("object_type") == object_type}


def is_blacklisted(session: Session, object_type: str, object_id: Any, sector: str | None = None) -> bool:
    r = latest_rule(session, "blacklist", _key(object_type, object_id), sector)
    return bool(r and r.active)


def link_overrides(session: Session, sector: str | None = None) -> list[dict[str, Any]]:
    return [{**r.body, "rule_id": str(r.id), "version": r.version, "created_by": r.created_by}
            for r in active_rules(session, "link_override", sector)]


def _example(object_type: str, obj: Any) -> dict[str, Any]:
    if object_type == "event":
        inp = obj.quote or obj.signal or obj.title or ""
        out = {k: jsonable(getattr(obj, k)) for k in ("event_type", "risk_codes", "cause", "signal", "effect",
                                                      "effect_days", "mitigation", "mitigation_effect", "quote")}
    elif object_type == "lesson":
        inp = obj.title or obj.cause or ""
        out = {k: jsonable(getattr(obj, k)) for k in ("cause", "signal", "effect", "recommendation", "risk_codes")}
    elif object_type == "clause":
        inp = obj.trigger or obj.title or ""
        out = {k: jsonable(getattr(obj, k)) for k in ("risk_code", "title", "trigger", "legal_basis", "text")}
    else:  # risk_category
        inp = obj.description or obj.name
        out = {k: jsonable(getattr(obj, k)) for k in ("code", "name", "effects", "keywords")}
    return {"object_type": object_type, "object_id": str(obj.id), "input": inp, "output": out}


def get_few_shot(session: Session, task: str, k: int = 3, sector: str | None = None) -> list[dict[str, Any]]:
    """Exemplary approved items for prompts; [] when none (callers just skip the examples block)."""
    if task not in TASK_SOURCES:
        return []
    object_type, flt = TASK_SOURCES[task]
    model = {"event": Event, "lesson": Lesson, "clause": Clause, "risk_category": RiskCategory}[object_type]
    marked = [uuid.UUID(r.body["object_id"]) for r in active_rules(session, "few_shot", sector)
              if r.body.get("object_type") == object_type]
    q = select(model).where(model.status.in_(APPROVED))
    if flt.get("event_type"):
        q = q.where(model.event_type == flt["event_type"])
    if flt.get("not_event_type"):
        q = q.where(model.event_type != flt["not_event_type"])
    rows: list[Any] = []
    if marked:
        rows = list(session.execute(q.where(model.id.in_(marked)).order_by(model.reviewed_at.desc()).limit(k)).scalars())
    if len(rows) < k and object_type == "event":
        more = q.where(Event.exemplary.is_(True), model.id.notin_([r.id for r in rows] or [uuid.uuid4()]))
        rows += list(session.execute(more.order_by(model.reviewed_at.desc()).limit(k - len(rows))).scalars())
    return [_example(object_type, r) for r in rows[:k]]


def recommendation_sources(session: Session, risk_codes: list[str] | None = None,
                           sector: str | None = None) -> dict[str, list[dict[str, Any]]]:
    sector = _sector(sector)
    cq = select(Clause).where(Clause.sector == sector, Clause.status.in_(APPROVED))
    lq = select(Lesson).where(Lesson.sector == sector, Lesson.status.in_(APPROVED))
    if risk_codes:
        cq = cq.where(Clause.risk_code.in_(risk_codes))
    clauses = [{"id": str(c.id), "code": c.code, "risk_code": c.risk_code, "title": c.title, "trigger": c.trigger,
                "legal_basis": c.legal_basis, "text": c.text, "evidence_ids": c.evidence_ids} for c in
               session.execute(cq).scalars()]
    lessons = []
    for le in session.execute(lq).scalars():
        if risk_codes and not set(le.risk_codes or []) & set(risk_codes):
            continue
        lessons.append({"id": str(le.id), "title": le.title, "cause": le.cause, "signal": le.signal,
                        "effect": le.effect, "recommendation": le.recommendation, "risk_codes": le.risk_codes,
                        "project_id": str(le.project_id) if le.project_id else None, "evidence_ids": le.evidence_ids})
    return {"clauses": clauses, "lessons": lessons}
