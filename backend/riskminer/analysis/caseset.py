"""The experience base as seen by the analysis: one `Case` per project (deep + auto tier) with its outcomes.

Reads only DB tables filled by S1/S2 (project, project_procedure, procedure, contract, contract_change).
Outcomes are aggregated over the project's contracts. Cached in-process; the cache key is the row counts and
the latest update time, so new data (or an expert edit) invalidates it.
"""

from __future__ import annotations

import datetime as dt
import re
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

REVIEW_REJECTED = "rejected"


@dataclass
class Case:
    project_id: uuid.UUID
    code: str
    title: str
    description: str | None
    tier: str
    subsector_main: str | None
    subsector_extra: list[str]
    work_type: str | None
    formula: str | None
    voivodeship: str | None
    features: dict[str, Any]
    project_status: str | None
    # outcomes (aggregated over contracts)
    n_contracts: int = 0
    value_gross: float | None = None
    paid_gross: float | None = None
    planned_days: int | None = None
    actual_days: int | None = None
    delay_days: int | None = None  # actual_end − planned_end (≥ 0), None if dates missing
    late: bool | None = None  # any contract not on time (zamawiający: 5.3 = Nie)
    performed: bool | None = None
    n_changes: int | None = None
    change_codes: list[str] = field(default_factory=list)
    change_reasons: list[dict[str, Any]] = field(default_factory=list)  # [{code, reason, evidence_ids}]
    offers_count: int | None = None
    est_value_net: float | None = None
    budget_gross: float | None = None
    price_won: float | None = None
    cancelled: bool = False
    cancel_basis: str | None = None
    signed_year: int | None = None
    year: int | None = None
    evidence_ids: list[str] = field(default_factory=list)  # contract/procedure evidence (outcome sources)
    procedure_ids: list[uuid.UUID] = field(default_factory=list)

    @property
    def length_km(self) -> float | None:
        v = (self.features or {}).get("length_km")
        v = v.get("value") if isinstance(v, dict) else v
        return float(v) if isinstance(v, int | float) and v > 0 else None

    @property
    def rlm(self) -> float | None:
        v = (self.features or {}).get("rlm")
        v = v.get("value") if isinstance(v, dict) else v
        return float(v) if isinstance(v, int | float) and v > 0 else None

    @property
    def completed(self) -> bool:
        return self.n_contracts > 0 and (self.late is not None or self.paid_gross is not None)

    @property
    def paid_ratio(self) -> float | None:
        if self.performed and self.paid_gross and self.value_gross and self.value_gross > 0 and self.paid_gross > 0:
            return self.paid_gross / self.value_gross
        return None

    @property
    def cancelled_255_3(self) -> bool:
        return bool(self.cancelled and self.cancel_basis and "255 pkt 3" in self.cancel_basis)

    @property
    def text(self) -> str:
        return f"{self.title or ''}. {self.description or ''}"


_SQL_PROJECTS = """
SELECT p.id, p.code, p.title, p.description, p.tier, p.subsector_main, p.subsector_extra, p.work_type,
       p.formula, p.voivodeship, p.features, p.project_status
FROM project p WHERE p.status <> 'rejected'
"""
_SQL_PROCS = """
SELECT pp.project_id, pr.id, pr.est_value_net, pr.budget_gross, pr.offers_count, pr.cancelled, pr.cancel_basis,
       pr.first_published_at, pr.evidence_ids, pr.meta->'tender_results' AS trs
FROM project_procedure pp JOIN procedure pr ON pr.id = pp.procedure_id
WHERE pp.status <> 'rejected'
"""
_SQL_CONTRACTS = """
SELECT c.id, c.procedure_id, c.value_gross, c.paid_gross, c.planned_days, c.planned_end, c.actual_end,
       c.signed_at, c.on_time, c.performed, c.n_changes, c.offers_count, c.evidence_ids
FROM contract c WHERE c.status <> 'rejected'
"""
_SQL_CHANGES = """
SELECT cc.procedure_id, cc.legal_basis_code, cc.reason, cc.evidence_ids
FROM contract_change cc WHERE cc.status <> 'rejected'
"""
_SQL_KEY = """
SELECT (SELECT count(*) FROM project), (SELECT max(updated_at) FROM project),
       (SELECT count(*) FROM contract), (SELECT max(updated_at) FROM contract),
       (SELECT count(*) FROM contract_change), (SELECT count(*) FROM project_procedure)
"""

_lock = threading.Lock()
# Main object named in the title. Auto-tier subsectors come from title + description, so a sports hall whose
# description mentions "kanalizacja sanitarna" got that subsector and showed up as an 81% neighbour of a sewer.
_WODKAN = re.compile(r"kanaliz|wodociąg|wodn\w*-|ściek|oczyszcz|przepomp|pompowni|deszczow|retenc|uzdatn|ujęci\w* wody|"
                     r"studni|przyłącz|przykanalik|sanitarn|kolektor|rurociąg|zbiornik\w* wody|\bSUW\b|\bwody\b", re.I)
_OTHER = re.compile(r"boisk|\bhal[aiężo]\b|sportow|szkoł|szkol|przedszkol|żłob|świetlic|remiz|budynk|budynek|termomoderniz|"
                    r"\bulic|\bdrog|chodnik|ścieżk|parking|oświetl|\bmost|plac\w* zabaw|stadion|basen|kości|cmentarz|"
                    r"rewitaliz|świetlic|domu kultury|urzęd|ratusz", re.I)


def main_object(title: str) -> str:
    """'wodkan' | 'mixed' (another object first, e.g. road works with a sewer part) | 'other' (no wod-kan object)."""
    o, w = _OTHER.search(title or ""), _WODKAN.search(title or "")
    if not o:
        return "wodkan"
    if not w:
        return "other"
    return "mixed" if o.start() < w.start() else "wodkan"


_cache: dict[str, Any] = {"key": None, "cases": None, "wodkan": None}


def _f(x: Any) -> float | None:
    return float(x) if x is not None else None


def load_wodkan_cases(session: Session) -> list[Case]:
    """Cases usable as references for a wod-kan investment (see `main_object`); cached with the full list so the
    TF-IDF index (keyed by list identity) is built once."""
    cases = load_cases(session)
    with _lock:
        hit = _cache.get("wodkan")
        if hit is not None and hit[0] is cases:
            return hit[1]
    out = [c for c in cases if c.tier == "deep" or main_object(c.title) != "other"]
    with _lock:
        _cache["wodkan"] = (cases, out)
    return out


def load_cases(session: Session, use_cache: bool = True) -> list[Case]:
    key = tuple(str(x) for x in session.execute(text(_SQL_KEY)).one())
    with _lock:
        if use_cache and _cache["key"] == key and _cache["cases"] is not None:
            return _cache["cases"]
    cases = _build(session)
    with _lock:
        _cache.update(key=key, cases=cases)
    return cases


def _build(session: Session) -> list[Case]:
    projects = {r.id: Case(
        project_id=r.id, code=r.code, title=r.title or "", description=r.description, tier=r.tier,
        subsector_main=r.subsector_main, subsector_extra=list(r.subsector_extra or []), work_type=r.work_type,
        formula=r.formula, voivodeship=r.voivodeship, features=dict(r.features or {}), project_status=r.project_status,
    ) for r in session.execute(text(_SQL_PROJECTS))}
    proc_to_projects: dict[uuid.UUID, list[uuid.UUID]] = {}
    for r in session.execute(text(_SQL_PROCS)):
        c = projects.get(r.project_id)
        if c is None:
            continue
        proc_to_projects.setdefault(r.id, []).append(r.project_id)
        c.procedure_ids.append(r.id)
        c.est_value_net = c.est_value_net or _f(r.est_value_net)
        c.budget_gross = c.budget_gross or _f(r.budget_gross)
        c.offers_count = c.offers_count if c.offers_count is not None else r.offers_count
        if r.cancelled:
            c.cancelled = True
            c.cancel_basis = r.cancel_basis
        if r.first_published_at:
            c.year = c.year or r.first_published_at.year
        trs = r.trs or []
        won = [t.get("price_won") for t in trs if isinstance(t, dict) and t.get("price_won")]
        if len(trs) == 1 and won:
            c.price_won = float(won[0])
        c.evidence_ids.extend(str(e) for e in (r.evidence_ids or [])[:3])
    agg: dict[uuid.UUID, list[Any]] = {}
    for r in session.execute(text(_SQL_CONTRACTS)):
        for pid in proc_to_projects.get(r.procedure_id, []):
            agg.setdefault(pid, []).append(r)
    for pid, rows in agg.items():
        c = projects[pid]
        c.n_contracts = len(rows)
        vals = [_f(r.value_gross) for r in rows if r.value_gross is not None]
        c.value_gross = sum(vals) if vals else None
        paid = [_f(r.paid_gross) for r in rows if r.paid_gross is not None]
        c.paid_gross = sum(paid) if paid and len(paid) == len(rows) else None
        pd_ = [r.planned_days for r in rows if r.planned_days]
        c.planned_days = max(pd_) if pd_ else None
        ot = [r.on_time for r in rows if r.on_time is not None]
        c.late = (not all(ot)) if ot else None
        perf = [r.performed for r in rows if r.performed is not None]
        c.performed = all(perf) if perf else None
        nch = [r.n_changes for r in rows if r.n_changes is not None]
        c.n_changes = sum(nch) if nch else None
        if c.offers_count is None:
            oc = [r.offers_count for r in rows if r.offers_count is not None]
            c.offers_count = min(oc) if oc else None
        delays, actual = [], []
        for r in rows:
            if r.planned_end and r.actual_end:
                delays.append(max(0, (r.actual_end - r.planned_end).days))
            if r.signed_at and r.actual_end:
                actual.append((r.actual_end - r.signed_at).days)
        c.delay_days = max(delays) if delays else None
        c.actual_days = max(actual) if actual else None
        signed = [r.signed_at for r in rows if isinstance(r.signed_at, dt.date)]
        c.signed_year = min(signed).year if signed else None
        c.year = c.signed_year or c.year
        for r in rows:
            c.evidence_ids.extend(str(e) for e in (r.evidence_ids or []))
    for r in session.execute(text(_SQL_CHANGES)):
        for pid in proc_to_projects.get(r.procedure_id, []):
            c = projects[pid]
            if r.legal_basis_code:
                c.change_codes.append(r.legal_basis_code)
            if len(c.change_reasons) < 6:
                c.change_reasons.append({"code": r.legal_basis_code, "reason": (r.reason or "")[:400],
                                         "evidence_ids": [str(e) for e in (r.evidence_ids or [])]})
    # an auto case that is the same procedure as a deep project is a duplicate – keep the deep one
    deep_procs = {p for c in projects.values() if c.tier == "deep" for p in c.procedure_ids}
    out = [c for c in projects.values() if (c.completed or c.cancelled)
           and not (c.tier != "deep" and deep_procs.intersection(c.procedure_ids))]
    out.sort(key=lambda c: c.code)
    return out


def clear_cache() -> None:
    with _lock:
        _cache.update(key=None, cases=None, wodkan=None)
