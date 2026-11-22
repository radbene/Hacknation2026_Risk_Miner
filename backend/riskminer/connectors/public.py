"""Shared plumbing for the public sources beyond BZP (KPOŚK, TED, Biała lista VAT, KRS).

Every request goes through `logged_op` (op_log), every response is kept in the raw store (raw_record, binary bodies
on disk under `raw_store_dir`), every fact cites evidence with a permanent URL. Rows are written with
`upsert_reviewable`, so re-running never overwrites what the expert reviewed.
`run()` is the entry point used by the CLI (`riskminer sources`) and the `sources` job.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import re
import time
import uuid
from collections.abc import Callable
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config, repo_path
from riskminer.core.oplog import logged_op
from riskminer.core.upsert import upsert, upsert_reviewable
from riskminer.ids import make_id
from riskminer.models import Entity, Fact, Project, RawRecord, Source

log = logging.getLogger("riskminer.public")

SOURCES = {
    # code: (name, base_url, licence)
    "kposk": ("KPOŚK – sprawozdanie z realizacji Krajowego Programu Oczyszczania Ścieków Komunalnych (dane.gov.pl)",
              "https://dane.gov.pl/pl/dataset/3213", "dane publiczne, dane.gov.pl (informacja publiczna)"),
    "ted": ("TED – Tenders Electronic Daily (ogłoszenia UE)", "https://api.ted.europa.eu/v3",
            "dane otwarte UE (Commission Decision 2011/833/EU)"),
    "vat_whitelist": ("Biała lista podatników VAT (Ministerstwo Finansów)", "https://wl-api.mf.gov.pl",
                      "rejestr publiczny (art. 96b ustawy o VAT)"),
    "krs": ("KRS – Krajowy Rejestr Sądowy, API odpisów", "https://api-krs.ms.gov.pl/api/krs",
            "rejestr publiczny (ustawa o KRS)"),
}


class PublicClient:
    """httpx client with our User-Agent, a minimum interval between requests and op_log for every call."""

    def __init__(self, connector: str, job_id: uuid.UUID | None = None, min_interval: float = 0.3, timeout: float = 60):
        cfg = get_config()
        cc = cfg.connectors.get(connector)
        self.connector = connector
        self.min_interval = cc.min_interval_s if cc and cc.min_interval_s else min_interval
        self.job_id = job_id
        self._last = 0.0
        self.n_requests = 0
        self.client = httpx.Client(headers={"User-Agent": cfg.user_agent}, timeout=timeout, follow_redirects=True)

    def request(self, method: str, url: str, *, operation: str, params: dict[str, Any] | None = None,
                json_body: dict[str, Any] | None = None, n_results: Callable[[httpx.Response], int] | None = None,
                ok_status: tuple[int, ...] = (200,)) -> httpx.Response:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        for attempt in range(5):
            with logged_op(self.connector, operation, url, params or json_body or {}, job_id=self.job_id) as op:
                self.n_requests += 1
                r = self.client.request(method, url, params=params, json=json_body)
                op["status_code"], op["bytes"] = r.status_code, len(r.content)
                retry = r.status_code in (429, 503) and attempt < 4
                if r.status_code not in ok_status and not retry:
                    r.raise_for_status()
                if n_results is not None and not retry:
                    op["n_results"] = n_results(r)
            if not retry:
                return r
            delay = float(r.headers.get("Retry-After") or 0) or 3.0 * (attempt + 1)
            time.sleep(min(delay, 30.0))
            self._last = time.monotonic()
        return r


def ensure_source(session: Session, code: str) -> None:
    name, base, licence = SOURCES[code]
    upsert(session, Source, dict(id=make_id("source", code), code=code, name=name, base_url=base, licence=licence,
                                 data_location="public"), index_elements=["code"])


def save_raw(session: Session, source_code: str, key: str, *, url: str | None, retrieved_from: str,
             payload: Any = None, blob: bytes | None = None, content_type: str | None = None, ext: str = "") -> uuid.UUID:
    body = blob if blob is not None else json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()
    sha = hashlib.sha256(body).hexdigest()
    blob_path = None
    if blob is not None:
        p = repo_path(get_config().raw_store_dir) / source_code / f"{sha}{ext}"
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(blob)
        blob_path = str(p)
    raw_id = make_id("raw_record", source_code, key, sha)
    upsert(session, RawRecord, dict(id=raw_id, source_code=source_code, key=key, url=url, retrieved_from=retrieved_from,
                                    retrieved_at=dt.datetime.now(dt.UTC), sha256=sha, content_type=content_type,
                                    payload=payload if blob is None else None, blob_path=blob_path),
           index_elements=["source_code", "key", "sha256"])
    return raw_id


def put_fact(session: Session, *, subject_type: str, subject_id: uuid.UUID, fact_type: str, key: tuple,
             evidence_ids: list[uuid.UUID], value_text: str | None = None, value_num: float | None = None,
             value_date: dt.date | None = None, unit: str | None = None, method: str = "key",
             confidence: float = 1.0) -> str:
    fid = make_id("fact", fact_type, subject_type, subject_id, *key)
    return upsert_reviewable(session, Fact, dict(
        id=fid, subject_type=subject_type, subject_id=subject_id, fact_type=fact_type, value_text=value_text,
        value_num=value_num, value_date=value_date, unit=unit, method=method, confidence=confidence,
        evidence_ids=[str(e) for e in evidence_ids]))


# ---------------------------------------------------------------- who to look up

def deep_projects(session: Session, project_ids: list[uuid.UUID] | None = None) -> list[Project]:
    q = select(Project).where(Project.tier == "deep")
    if project_ids:
        q = q.where(Project.id.in_(project_ids))
    return list(session.execute(q.order_by(Project.code)).scalars())


_GMINA = re.compile(r"^(gmina\s+miejska|gmina\s+miasto|miasto\s+i\s+gmina|gmina\s+i\s+miasto|miasto|gmina)\s+", re.I)


def gmina_of(session: Session, p: Project) -> str | None:
    """'Gmina Nowogard' → 'Nowogard' (beneficiary name), else the project's city."""
    ent = session.get(Entity, p.beneficiary_id) if p.beneficiary_id else None
    name = (ent.name if ent else None) or ""
    name = re.split(r"\s+[–-]\s+", name.strip())[0]  # "Kartuzy – Urząd Miejski w Kartuzach" → "Kartuzy"
    name = _GMINA.sub("", name).strip(" ,.")
    if name and not re.search(r"\b(sp\.|spółka|przedsiębiorstwo|zakład|wodociąg|zarząd|urząd)", name, re.I):
        return name
    return (p.city or None)


def norm(s: str | None) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    s = re.sub(r"\s*\((gm\.|gmina|m\.)[^)]*\)$", "", s)
    prev = None
    while prev != s:  # "gmina miasto elbląg" → "elbląg"
        prev, s = s, re.sub(r"^(m\.|gm\.|miasto|miasta|gmina)\s+", "", s)
    return s.strip()


# ---------------------------------------------------------------- entry point

def run(session: Session, sources: list[str] | None = None, project_ids: list[uuid.UUID] | None = None,
        job_id: uuid.UUID | None = None, progress: Callable[[float, str | None], None] | None = None) -> dict[str, Any]:
    from riskminer.connectors import kposk, krs, ted, vat_whitelist

    order = [("kposk", kposk.run), ("ted", ted.run), ("vat_whitelist", vat_whitelist.run), ("krs", krs.run)]
    wanted = [o for o in order if not sources or o[0] in sources]
    report: dict[str, Any] = {}
    for i, (code, fn) in enumerate(wanted):
        if progress:
            progress(i / max(1, len(wanted)), f"{code}…")
        ensure_source(session, code)
        try:
            report[code] = fn(session, project_ids=project_ids, job_id=job_id)
            session.commit()
        except Exception as e:  # noqa: BLE001 – one source failing must not stop the others
            session.rollback()
            log.exception("source %s failed", code)
            report[code] = {"error": f"{type(e).__name__}: {e}"[:500]}
    if progress:
        progress(1.0, "gotowe")
    return report
