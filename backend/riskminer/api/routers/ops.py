"""Dashboard, op log, connector health, LLM usage, licences, quality, monitoring (owner: S6)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import uuid
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select, text

from riskminer.api.deps import DB, EXPERT, USER, CurrentUser, Session
from riskminer.core.config import get_config
from riskminer.models import Alert, Job, LLMCall, OpLog
from riskminer.schemas.common import Message, Page
from riskminer.schemas.ops import (
    AlertOut,
    ConnectorHealth,
    DashboardOut,
    LicenceOut,
    LLMUsageRow,
    MonitorRunIn,
    OpLogOut,
    QualityMetrics,
    WatchIn,
)

router = APIRouter(tags=["ops"])
OWNER = "S6"

COUNTED = {
    "projects": "project", "procedures": "procedure", "links": "project_procedure", "notices": "notice",
    "contracts": "contract", "contract_changes": "contract_change", "events": "event", "documents": "document",
    "evidence": "evidence", "data_issues": "data_issue", "analyses": "analysis", "lessons": "lesson",
    "knowledge_tables": "knowledge_table", "reviews": "review", "op_log": "op_log", "llm_calls": "llm_call",
}
TIERED = ("project", "procedure", "notice", "event")
REVIEW_TABLES = ("project_procedure", "event", "contract_change", "data_issue", "fact", "lesson", "risk_category",
                 "clause", "analysis_item", "document")

# connector registry: code → (tier, name) ; status "działa" when its module exists or it has op_log entries
REGISTRY = {
    "bzp": ("P0", "BZP / e-Zamówienia API (lustro + oficjalne)"),
    "bzp_zip": ("P0", "Paczka ogłoszeń BZP 2021–2026"),
    "xlsx": ("P0", "Import listy projektów (xlsx/csv)"),
    "vat_whitelist": ("P0", "Biała lista podatników VAT"),
    "nik": ("P0", "Raporty NIK"),
    "web_doc": ("P1", "Dokumenty z BIP / stron zamawiających"),
    "files": ("P0", "Wgrane dokumenty (PDF/DOCX)"),
    "ted": ("P1", "TED – ogłoszenia UE"),
    "krs": ("P1", "KRS – rejestr podmiotów"),
    "kio": ("P2", "Orzeczenia KIO"),
    "bk2021": ("P2", "Baza Konkurencyjności 2021"),
    "kposk": ("P2", "KPOŚK – krajowy program oczyszczania ścieków"),
}
MODULE_FOR = {"bzp_zip": "bzp_zip", "xlsx": "xlsx_import", "files": "files", "vat_whitelist": "vat_whitelist"}


def _count(db: Session, table: str, where: str = "") -> int:
    try:
        return db.execute(text(f'SELECT count(*) FROM "{table}" {where}')).scalar() or 0
    except Exception:  # noqa: BLE001
        db.rollback()
        return 0


def _data_locations() -> list[str]:
    cfg = get_config().llm
    used = {n for chain in cfg.tasks.values() for n in chain[:1]} | set(cfg.default[:1])
    return sorted({cfg.profiles[n].data_location for n in used if n in cfg.profiles})


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = DB):
    counts = {k: _count(db, t) for k, t in COUNTED.items()}
    counts["pending_review"] = sum(_count(db, t, "WHERE status = 'proposed'") for t in REVIEW_TABLES)
    counts["alerts_unread"] = _count(db, "alert", "WHERE NOT read")
    counts["watched"] = _count(db, "procedure", "WHERE watched")
    counts["jobs_running"] = _count(db, "job", "WHERE state IN ('queued','running')")
    tiers: dict[str, int] = {}
    for t in TIERED:
        try:
            for tier, n in db.execute(text(f'SELECT tier, count(*) FROM "{t}" GROUP BY tier')).all():
                tiers[f"{t}.{tier}"] = n
        except Exception:  # noqa: BLE001
            db.rollback()
    jobs = db.execute(select(Job).order_by(Job.created_at.desc()).limit(10)).scalars().all()
    last_jobs = [{"id": str(j.id), "kind": j.kind, "state": j.state, "progress": j.progress, "message": j.message,
                  "created_at": j.created_at.isoformat() if j.created_at else None,
                  "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                  "error": (j.error or "").splitlines()[0][:300] if j.error else None} for j in jobs]
    alerts = db.execute(select(Alert).where(Alert.read.is_(False)).order_by(Alert.created_at.desc()).limit(10)).scalars()
    alert_list = [{"id": str(a.id), "kind": a.kind, "severity": a.severity, "message": a.message,
                   "project_id": str(a.project_id) if a.project_id else None,
                   "created_at": a.created_at.isoformat() if a.created_at else None} for a in alerts]
    locs = ["db:eu"] + [f"llm:{x}" for x in _data_locations()]
    return DashboardOut(counts=counts, tiers=tiers, last_jobs=last_jobs, alerts=alert_list, data_locations=locs)


@router.get("/ops/log", response_model=Page[OpLogOut])
def op_log(connector: str | None = None, job_id: uuid.UUID | None = None, operation: str | None = None,
           errors_only: bool = False, since: dt.datetime | None = None, offset: int = 0, limit: int = 100,
           db: Session = DB):
    q = select(OpLog)
    if connector:
        q = q.where(OpLog.connector == connector)
    if job_id:
        q = q.where(OpLog.job_id == job_id)
    if operation:
        q = q.where(OpLog.operation == operation)
    if errors_only:
        q = q.where(OpLog.error.is_not(None) | (OpLog.status_code >= 400))
    if since:
        q = q.where(OpLog.at >= since)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    limit = max(1, min(limit, 1000))
    items = db.execute(q.order_by(OpLog.at.desc()).offset(offset).limit(limit)).scalars().all()
    return Page[OpLogOut](items=items, total=total, offset=offset, limit=limit)


def _module_exists(code: str) -> bool:
    name = f"riskminer.connectors.{MODULE_FOR.get(code, code)}"
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


@router.get("/ops/connectors", response_model=list[ConnectorHealth])
def connectors(db: Session = DB):
    from riskminer.monitor.licences import DATA_SOURCES

    cfg = get_config()
    lic = {code: licence for code, _, licence, _ in DATA_SOURCES}
    stats = {r.connector: r for r in db.execute(
        select(OpLog.connector, func.count().label("n"), func.max(OpLog.at).label("last_at"),
               func.max(OpLog.at).filter(OpLog.error.is_(None) & ((OpLog.status_code.is_(None)) | (OpLog.status_code < 400)))
               .label("last_ok_at"))
        .group_by(OpLog.connector)).all()}
    out = []
    for code in list(REGISTRY) + [c for c in cfg.connectors if c not in REGISTRY]:
        tier, name = REGISTRY.get(code, ("P2", code))
        cc = cfg.connectors.get(code)
        st = stats.get(code)
        last_err = None
        if st:
            last_err = db.execute(select(OpLog.error).where(OpLog.connector == code, OpLog.error.is_not(None))
                                  .order_by(OpLog.at.desc()).limit(1)).scalar()
        ok = None
        if st:
            ok = st.last_ok_at is not None and st.last_ok_at >= st.last_at
        works = bool(st) or _module_exists(code)
        out.append(ConnectorHealth(code=code, name=name, enabled=cc.enabled if cc else works,
                                   base_url=cc.base_url if cc else None, ok=ok,
                                   last_ok_at=st.last_ok_at if st else None,
                                   last_error=(last_err or None) and last_err[:500], licence=lic.get(code),
                                   tier=tier, status="działa" if works else "zaprojektowane"))
    return out


@router.get("/ops/llm-usage", response_model=list[LLMUsageRow])
def llm_usage(since: dt.datetime | None = None, db: Session = DB):
    q = select(LLMCall.task, LLMCall.provider, LLMCall.model, LLMCall.data_location,
               func.count().label("calls"),
               func.count().filter(LLMCall.cached.is_(True)).label("cached"),
               func.count().filter(LLMCall.ok.is_(False)).label("errors"),
               func.coalesce(func.sum(LLMCall.tokens_in), 0).label("tokens_in"),
               func.coalesce(func.sum(LLMCall.tokens_out), 0).label("tokens_out"),
               func.coalesce(func.sum(LLMCall.cost_usd), 0.0).label("cost_usd"))
    if since:
        q = q.where(LLMCall.at >= since)
    rows = db.execute(q.group_by(LLMCall.task, LLMCall.provider, LLMCall.model, LLMCall.data_location)
                      .order_by(LLMCall.task)).all()
    return [LLMUsageRow(task=r.task, provider=r.provider, model=r.model, data_location=r.data_location,
                        calls=r.calls, cached=r.cached, errors=r.errors, tokens_in=int(r.tokens_in),
                        tokens_out=int(r.tokens_out), cost_usd=round(float(r.cost_usd), 4)) for r in rows]


@lru_cache(maxsize=1)
def _licences() -> list[LicenceOut]:
    from riskminer.monitor.licences import inventory

    return [LicenceOut(name=f"{i.name}{(' ' + i.version) if i.version else ''}", kind=i.kind, licence=i.licence,
                       url=i.url, notes="; ".join(x for x in (i.ecosystem, i.notes, None if i.verdict == "ok" else i.verdict) if x) or None)
            for i in inventory() if i.verdict != "optional"]


@router.get("/ops/licences", response_model=list[LicenceOut])
def licences(kind: str | None = None):
    items = _licences()
    return [i for i in items if i.kind == kind] if kind else items


@router.get("/quality", response_model=QualityMetrics)
def quality(db: Session = DB):
    """Gold-set metrics (precision/recall of linking etc.). Computation lives in S1's link module."""
    try:
        from riskminer.link import quality as q  # type: ignore
    except ImportError:
        raise HTTPException(501, "Not implemented yet (owner: S1 – riskminer.link.quality)") from None
    for name in ("compute", "compute_quality", "quality_metrics", "evaluate"):
        fn = getattr(q, name, None)
        if callable(fn):
            return to_quality_metrics(fn(db))
    raise HTTPException(501, "riskminer.link.quality has no compute() function")


def to_quality_metrics(res) -> QualityMetrics:
    """Accept QualityMetrics, a dict in its shape, or S1's flat `evaluate()` dict (precision, recall, per_project …)."""
    if isinstance(res, QualityMetrics):
        return res
    res = dict(res or {})
    if "linking" in res and "gold_set" in res:
        return QualityMetrics.model_validate({"computed_at": dt.datetime.now(dt.UTC), **res})
    details = res.pop("per_project", []) or []
    extra = {k: res.pop(k) for k in ("events", "quotes") if isinstance(res.get(k), dict)}
    return QualityMetrics(gold_set=str(res.pop("gold_file", res.pop("gold_set", "links_gold.csv"))),
                          computed_at=dt.datetime.now(dt.UTC), linking=res, details=details, **extra)


@router.get("/alerts", response_model=list[AlertOut])
def alerts(unread_only: bool = False, kind: str | None = None, project_id: uuid.UUID | None = None,
           limit: int = 200, db: Session = DB):
    q = select(Alert)
    if unread_only:
        q = q.where(Alert.read.is_(False))
    if kind:
        q = q.where(Alert.kind == kind)
    if project_id:
        q = q.where(Alert.project_id == project_id)
    return db.execute(q.order_by(Alert.created_at.desc()).limit(max(1, min(limit, 1000)))).scalars().all()


@router.post("/alerts/{alert_id}/read", response_model=Message)
def mark_alert_read(alert_id: uuid.UUID, read: bool = True, db: Session = DB, user: CurrentUser = USER):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(404, "Brak alertu")
    a.read = read
    db.commit()
    return Message(message="Oznaczono jako przeczytany" if read else "Oznaczono jako nieprzeczytany")


@router.post("/monitor/watch", response_model=Message)
def watch(body: WatchIn, db: Session = DB, user: CurrentUser = EXPERT):
    from riskminer.monitor.watch import set_watch

    if not body.procedure_ids and not body.project_ids:
        raise HTTPException(422, "Podaj procedure_ids lub project_ids")
    n = set_watch(db, procedure_ids=body.procedure_ids, project_ids=body.project_ids, watched=body.watched)
    db.commit()
    total = _count(db, "procedure", "WHERE watched")
    return Message(message=f"Zmieniono {n} postępowań; obserwowane razem: {total}")


@router.post("/monitor/run", response_model=Message)
def monitor_run(body: MonitorRunIn, db: Session = DB, user: CurrentUser = EXPERT):
    """Replay (`as_of`) runs inline – it only reads the DB. A live check queries BZP, so it goes to the worker."""
    if body.as_of:
        from riskminer.monitor.watch import run_monitor

        rep = run_monitor(db, as_of=body.as_of, user=user.username)
        new = sum(1 for a in rep["new_notices"] if a.get("created"))
        return Message(message=(f"Stan na {body.as_of.isoformat()}: obserwowane {rep['watched']}, nowe ogłoszenia {new}, "
                                f"przekroczone terminy {len(rep['deadlines'])}, alerty utworzone {rep['alerts_created']}"
                                + (f". {rep['note']}" if rep.get("note") else "")))
    from riskminer.core.jobs import enqueue

    job = enqueue(db, "monitor", {"live": True, "user": user.username}, user=user.username)
    return Message(message=f"Zlecono sprawdzenie BZP (zadanie {job.id})")

