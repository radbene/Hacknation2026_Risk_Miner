"""Path A orchestration (S1 modules, wired by the main session): enrich deep-tier projects and export links.

enrich = for every deep-tier beneficiary NIP fetch all 4 notice types (live BZP API via the mirror → official
fallback; offline: the organizer snapshot) → store notices → build procedures → link every project.
Idempotent: notices/procedures are upserted by natural key, links via upsert_reviewable (expert decisions survive).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import logging
import lzma
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.connectors.bzp_store import build_procedure, ensure_sources, store_notice
from riskminer.models import Entity, Notice, Procedure, Project, ProjectProcedure

log = logging.getLogger("riskminer.enrich")
FIXTURE_NIPS = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "projects22" / "notices_by_nip.jsonl.xz"
DATE_FROM = dt.date(2021, 1, 1)
Progress = Callable[[float, str], None] | None


def deep_buyers(session: Session, project_ids: list[uuid.UUID] | None = None) -> dict[str, dict[str, Any]]:
    """{nip: {name, city, projects:[code]}} for deep-tier projects."""
    q = select(Project, Entity).join(Entity, Entity.id == Project.beneficiary_id).where(Project.tier == "deep")
    if project_ids:
        q = q.where(Project.id.in_(project_ids))
    out: dict[str, dict[str, Any]] = {}
    for p, e in session.execute(q).all():
        if not e.nip:
            continue
        b = out.setdefault(e.nip, {"name": e.name, "city": e.city or p.city, "projects": []})
        b["projects"].append(p.code)
    return out


def _offline_records(nips: set[str]) -> tuple[list[dict[str, Any]], str]:
    """Notices of the given NIPs from the 988-notice extract of the organizer snapshot, else from the full zip."""
    recs: list[dict[str, Any]] = []
    if FIXTURE_NIPS.exists():
        with lzma.open(FIXTURE_NIPS, "rt", encoding="utf-8") as f:
            recs = [r for r in (json.loads(x) for x in f if x.strip())
                    if (r.get("organizationNationalId") or "").strip() in nips]
        have = {(r.get("organizationNationalId") or "").strip() for r in recs}
        if nips <= have:
            return recs, f"zip:{FIXTURE_NIPS.name}"
    from riskminer.connectors.bzp_zip import iter_zip, zip_path

    recs = [r for _, r in iter_zip() if (r.get("organizationNationalId") or "").strip() in nips]
    return recs, f"zip:{zip_path()}"


def enrich(session: Session, *, project_ids: list[uuid.UUID] | None = None, source: str = "auto",
           date_to: dt.date | None = None, progress: Progress = None, job_id: uuid.UUID | None = None,
           actor: str = "system") -> dict[str, Any]:
    """source: live (BZP API only) | offline (snapshot only) | auto (live, snapshot for NIPs the API failed on)."""
    t0 = time.monotonic()
    ensure_sources(session)
    buyers = deep_buyers(session, project_ids)
    date_to = date_to or dt.date.today()
    rep: dict[str, Any] = {"source": source, "buyers": len(buyers), "per_nip": [], "notices": 0, "inserted": 0,
                           "updated": 0, "unchanged": 0, "requests": 0, "api_errors": [], "offline_nips": []}
    ocids: set[str] = set()
    failed: set[str] = set()
    if source in ("live", "auto"):
        from riskminer.connectors.bzp import BzpClient, fetch_for_nip

        client = BzpClient(job_id=job_id)
        for i, (nip, b) in enumerate(sorted(buyers.items())):
            try:
                recs, info = fetch_for_nip(client, nip, b["name"], b["city"], DATE_FROM, date_to)
            except Exception as e:  # noqa: BLE001 – one buyer failing must not stop the run
                recs, info = [], {"error": f"{type(e).__name__}: {e}"[:300]}
            if not recs:
                failed.add(nip)
            now = dt.datetime.now(dt.UTC)
            for r in recs:
                _, res = store_notice(session, r, source_code="bzp",
                                      retrieved_from=f"{client.base_url}?NoticeNumber={r.get('noticeNumber')}",
                                      retrieved_at=now, tier="deep", keep_html=True)
                rep[res] += 1
                if r.get("tenderId"):
                    ocids.add(r["tenderId"])
            rep["notices"] += len(recs)
            rep["per_nip"].append({"nip": nip, "name": b["name"], "projects": b["projects"], "notices": len(recs),
                                   "source": "bzp", **info})
            session.commit()
            if progress:
                progress(0.6 * (i + 1) / max(1, len(buyers)), f"BZP: {b['name']} – {len(recs)} ogłoszeń")
        rep["requests"] = client.n_requests
        rep["api_errors"] = client.errors[-20:]
    if source == "offline":
        failed = set(buyers)
    if failed and source in ("offline", "auto"):
        recs, origin = _offline_records(failed)
        for r in recs:
            _, res = store_notice(session, r, source_code="bzp_zip", retrieved_from=origin, tier="deep", keep_html=False)
            rep[res] += 1
            if r.get("tenderId"):
                ocids.add(r["tenderId"])
        rep["notices"] += len(recs)
        rep["offline_nips"] = sorted(failed)
        rep["offline_origin"] = origin
        session.commit()
    # rebuild every deep procedure of these buyers (also ones stored by earlier runs)
    nips = set(buyers)
    ocids |= set(session.execute(select(Notice.ocid).where(Notice.org_nip.in_(nips), Notice.ocid.is_not(None)))
                 .scalars().all())
    for i, oc in enumerate(sorted(ocids)):
        build_procedure(session, oc, tier="deep", actor=actor)
        if i % 50 == 0:
            session.commit()
            if progress:
                progress(0.6 + 0.25 * i / max(1, len(ocids)), f"postępowania {i}/{len(ocids)}")
    session.commit()
    rep["procedures"] = len(ocids)
    from riskminer.link.matcher import link_all

    if progress:
        progress(0.9, "dopasowanie projektów do postępowań")
    ids = project_ids or None
    links = link_all(session, ids, actor=actor)
    session.commit()
    rep["links"] = links
    rep["link_summary"] = {k: sum(1 for x in links if x["status"] == k) for k in ("linked", "uncertain", "unlinked", "override")}
    rep["seconds"] = round(time.monotonic() - t0, 1)
    return rep


LINKS_CSV_COLUMNS = ["project_code", "project_title", "ocid", "bzp_number", "procedure_title", "part_no", "method",
                     "confidence", "status", "is_override", "rank", "components", "alternatives", "evidence_ids",
                     "reviewed_by"]


def links_csv(session: Session) -> str:
    rows = session.execute(select(ProjectProcedure, Project, Procedure)
                           .join(Project, Project.id == ProjectProcedure.project_id)
                           .join(Procedure, Procedure.id == ProjectProcedure.procedure_id)
                           .order_by(Project.code, ProjectProcedure.rank)).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(LINKS_CSV_COLUMNS)
    for link, p, proc in rows:
        comps = "; ".join(f"{c.get('name')}={c.get('score')}" + (f" ({c.get('detail')})" if c.get("detail") else "")
                          for c in link.components or [])
        alts = "; ".join(f"{a.get('ocid') or a.get('bzp_number')}:{a.get('score')}" for a in link.alternatives or [])
        w.writerow([p.code, p.title, proc.ocid, proc.bzp_number, proc.title, link.part_no, link.method,
                    link.confidence, link.status, link.is_override, link.rank, comps, alts,
                    " ".join(str(x) for x in link.evidence_ids or []), link.reviewed_by])
    # projects without any link are rows too (status unlinked)
    linked = {r[1].id for r in rows}
    for p in session.execute(select(Project).where(Project.tier == "deep").order_by(Project.code)).scalars():
        if p.id not in linked:
            w.writerow([p.code, p.title, "", "", "", p.part_no, "", "", "unlinked", False, "", "", "", "", ""])
    return buf.getvalue()
