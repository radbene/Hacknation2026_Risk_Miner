"""BZP snapshot connector: stream the organizer's notices.jsonl.xz (113k wod-kan notices) into notice/procedure.

The zip *is* the raw store for the auto tier: raw_record.payload keeps only metadata (no htmlBody) and
raw_record.blob_path / notice.retrieved_from = "<zip path>#L<line>". notice.canonical_text + sections are kept
(needed for quotes). Never decompressed to disk – streamed with lzma.

Harvest = load notices → build procedures → one auto-tier project per wod-kan procedure with a contract
outcome (code AUTO-…), linked by OCID (method=ocid, confidence 1.0). Deep-tier procedures are skipped.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import lzma
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from riskminer.connectors.bzp_store import build_procedure, ensure_sources, is_wodkan, store_notice
from riskminer.core.config import get_config, repo_path
from riskminer.core.db import SessionLocal
from riskminer.core.oplog import logged_op
from riskminer.core.upsert import upsert_reviewable
from riskminer.ids import make_id
from riskminer.models import Contract, Entity, Notice, Procedure, Project, ProjectProcedure

log = logging.getLogger("riskminer.bzp_zip")
MAIN_CHECKOUT_ZIP = Path("/home/radek/workspace/hacknation/risk_miner/risk-miner/data/raw/zip/risk_miner_bzp_kopia/bzp_kopia/notices.jsonl.xz")
PL_VOIV = {"PL02": "dolnośląskie", "PL04": "kujawsko-pomorskie", "PL06": "lubelskie", "PL08": "lubuskie",
           "PL10": "łódzkie", "PL12": "małopolskie", "PL14": "mazowieckie", "PL16": "opolskie", "PL18": "podkarpackie",
           "PL20": "podlaskie", "PL22": "pomorskie", "PL24": "śląskie", "PL26": "świętokrzyskie",
           "PL28": "warmińsko-mazurskie", "PL30": "wielkopolskie", "PL32": "zachodniopomorskie"}


def zip_path() -> Path:
    cc = get_config().connectors.get("bzp_zip")
    p = repo_path((cc.extra.get("path") if cc else None) or "data/raw/zip/risk_miner_bzp_kopia/bzp_kopia/notices.jsonl.xz")
    return p if p.exists() else MAIN_CHECKOUT_ZIP


def iter_zip(path: Path | None = None) -> Iterator[tuple[int, dict[str, Any]]]:
    path = path or zip_path()
    with lzma.open(path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if line.strip():
                yield i, json.loads(line)


def load_zip(*, limit: int | None = None, date_from: dt.date | None = None, date_to: dt.date | None = None,
             nips: set[str] | None = None, deep_nips: set[str] | None = None, batch: int = 500,
             progress: Callable[[float, str], None] | None = None, job_id=None) -> dict[str, Any]:
    """Stream notices into the DB (own sessions, commit per batch). Returns counts + touched OCIDs."""
    path = zip_path()
    counts = {"read": 0, "stored": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    ocids: set[str] = set()
    t0 = time.monotonic()
    s = SessionLocal()
    with logged_op("bzp_zip", "load", str(path), {"limit": limit, "date_from": str(date_from), "date_to": str(date_to),
                                                  "nips": len(nips or [])}, job_id=job_id) as op:
        try:
            ensure_sources(s)
            for lineno, rec in iter_zip(path):
                counts["read"] += 1
                day = (rec.get("publicationDate") or "")[:10]
                nip = (rec.get("organizationNationalId") or "").strip()
                if (date_from and day < date_from.isoformat()) or (date_to and day > date_to.isoformat()) \
                        or (nips is not None and nip not in nips):
                    counts["skipped"] += 1
                    continue
                if deep_nips and nip in deep_nips:  # deep tier is owned by `enrich` (live API provenance)
                    counts["skipped"] += 1
                    continue
                tier = "auto"
                try:
                    _, res = store_notice(s, rec, source_code="bzp_zip", retrieved_from=f"{path}#L{lineno}",
                                          tier=tier, keep_html=False)
                    counts[res] += 1
                    counts["stored"] += 1
                    if rec.get("tenderId"):
                        ocids.add(rec["tenderId"])
                except Exception as e:  # noqa: BLE001
                    s.rollback()
                    counts["errors"] += 1
                    log.warning("zip line %s: %s", lineno, e)
                if counts["stored"] % batch == 0:
                    s.commit()
                    if progress:
                        progress(0.0, f"wczytano {counts['stored']} ogłoszeń ({time.monotonic() - t0:.0f}s)")
                if limit and counts["stored"] >= limit:
                    break
            s.commit()
        finally:
            s.close()
        op["n_results"] = counts["stored"]
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return {"counts": counts, "ocids": sorted(ocids)}


def _deep_procedure_ids(s: Session) -> set:
    return set(s.execute(select(ProjectProcedure.procedure_id).join(Project, Project.id == ProjectProcedure.project_id)
                         .where(Project.tier == "deep")).scalars().all())


def auto_project(s: Session, proc: Procedure) -> str | None:
    """One auto-tier project per wod-kan procedure with an outcome (contract or cancellation)."""
    contracts = s.execute(select(Contract).where(Contract.procedure_id == proc.id)).scalars().all()
    if not contracts and not proc.cancelled:
        return None
    if proc.sector != "wodkan":
        return None
    ent = s.get(Entity, proc.buyer_id) if proc.buyer_id else None
    performed = [c for c in contracts if c.performing_notice_id]
    status = ("Unieważnione" if proc.cancelled and not contracts else
              "Zakończone" if contracts and len(performed) == len(contracts) else "W realizacji")
    code = "AUTO-" + make_id("auto", proc.ocid).hex[:12]
    pid = make_id("project", code)
    first_notice = s.execute(select(Notice).where(Notice.procedure_id == proc.id).order_by(Notice.published_at)).scalars().first()
    upsert_reviewable(s, Project, dict(
        id=pid, code=code, title=proc.title or code, beneficiary_id=proc.buyer_id, country="Polska",
        voivodeship=PL_VOIV.get(ent.province if ent else None), teryt=(ent.province or "")[2:] if ent and ent.province else None,
        city=ent.city if ent else None, sector="wodkan", order_type=proc.order_type, project_status=status,
        funding="KPO" if (proc.meta or {}).get("kpo_numbers") else None,
        public_id_type="OCID", public_id_value=proc.ocid, record_scope="całe postępowanie", tier="auto",
        record_source="BZP (kopia organizatora)", method="harvest", confidence=1.0,
        evidence_ids=(proc.evidence_ids or [])[:5],
        description=((first_notice.parsed or {}).get("parts") or {}).get("0", {}).get("description") if first_notice else None))
    upsert_reviewable(s, ProjectProcedure, dict(
        id=make_id("project_procedure", pid, proc.id, 0), project_id=pid, procedure_id=proc.id, part_no=None,
        method="ocid", confidence=1.0, components=[{"name": "ocid", "score": 1.0, "weight": None,
                                                     "detail": f"Projekt automatyczny z postępowania {proc.ocid}",
                                                     "evidence_id": (proc.evidence_ids or [None])[0]}],
        alternatives=[], evidence_ids=(proc.evidence_ids or [])[:3]))
    return code


def build_all(ocids: list[str], *, make_projects: bool = True, batch: int = 200,
              progress: Callable[[float, str], None] | None = None) -> dict[str, Any]:
    s = SessionLocal()
    out = {"procedures": 0, "auto_projects": 0, "errors": 0}
    try:
        deep = _deep_procedure_ids(s)
        for i, oc in enumerate(ocids, start=1):
            try:
                pid = build_procedure(s, oc)
                out["procedures"] += 1
                if make_projects and pid and pid not in deep:
                    proc = s.get(Procedure, pid)
                    if proc.tier != "deep" and auto_project(s, proc):
                        out["auto_projects"] += 1
            except Exception as e:  # noqa: BLE001
                s.rollback()
                out["errors"] += 1
                log.warning("build %s: %s", oc, e)
            if i % batch == 0:
                s.commit()
                if progress:
                    progress(i / max(1, len(ocids)), f"zbudowano {i}/{len(ocids)} postępowań")
        s.commit()
    finally:
        s.close()
    return out


def harvest(*, limit: int | None = None, date_from: dt.date | None = None, date_to: dt.date | None = None,
            progress: Callable[[float, str], None] | None = None, job_id=None) -> dict[str, Any]:
    """Auto tier: every wod-kan procedure 2021–2026 from the zip (tier=auto)."""
    s = SessionLocal()
    try:
        deep_nips = set(s.execute(select(Entity.nip).join(Project, Project.beneficiary_id == Entity.id)
                                  .where(Project.tier == "deep")).scalars().all()) - {None}
    finally:
        s.close()
    loaded = load_zip(limit=limit, date_from=date_from or dt.date(2021, 1, 1), date_to=date_to, deep_nips=deep_nips,
                      progress=progress, job_id=job_id)
    built = build_all(loaded["ocids"], progress=progress)
    return {"source": "bzp_zip", "path": str(zip_path()), **loaded["counts"], **built, "ocids": len(loaded["ocids"])}


def db_size_mb(session: Session) -> float:
    return round(session.execute(text("select pg_database_size(current_database())")).scalar() / 1e6, 1)


__all__ = ["harvest", "load_zip", "build_all", "iter_zip", "zip_path", "is_wodkan", "db_size_mb"]
