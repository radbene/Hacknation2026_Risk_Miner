"""Biała lista podatników VAT (Ministry of Finance) – verifies beneficiaries and contractors by NIP.

Batch endpoint /api/search/nips/{n1,...,n30}?date=. We keep the VAT status, REGON and KRS number (the KRS number
feeds the KRS connector). Bank account numbers are not kept, and for natural persons the name and addresses are
dropped from the stored response as well.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.connectors.public import PublicClient, deep_projects, put_fact, save_raw
from riskminer.core.evidence import add_evidence
from riskminer.ids import nip_valid, norm_nip
from riskminer.models import Contract, Entity, ProjectProcedure

API = "https://wl-api.mf.gov.pl/api/search/nips/{nips}"
PERMANENT = "https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={date}"
BATCH = 30


def entities_to_check(session: Session, project_ids: list[uuid.UUID] | None) -> list[Entity]:
    projects = deep_projects(session, project_ids)
    ids = {p.beneficiary_id for p in projects if p.beneficiary_id}
    procs = session.execute(select(ProjectProcedure.procedure_id).where(
        ProjectProcedure.project_id.in_([p.id for p in projects]), ProjectProcedure.status != "rejected")).scalars().all()
    if procs:
        ids |= set(session.execute(select(Contract.contractor_id).where(
            Contract.procedure_id.in_(procs), Contract.contractor_id.is_not(None))).scalars())
    ents = list(session.execute(select(Entity).where(Entity.id.in_(ids))).scalars()) if ids else []
    return [e for e in ents if nip_valid(norm_nip(e.nip))]


def _clean(subject: dict[str, Any], natural: bool) -> dict[str, Any]:
    s = {k: v for k, v in subject.items() if k not in ("accountNumbers", "representatives", "authorizedClerks", "partners")}
    s["accountNumbers_count"] = len(subject.get("accountNumbers") or [])
    if natural:
        for k in ("name", "residenceAddress", "workingAddress", "pesel"):
            s.pop(k, None)
    return s


def run(session: Session, project_ids: list[uuid.UUID] | None = None, job_id: uuid.UUID | None = None) -> dict[str, Any]:
    client = PublicClient("vat_whitelist", job_id=job_id, min_interval=0.5)
    ents = entities_to_check(session, project_ids)
    by_nip = {norm_nip(e.nip): e for e in ents}
    date = dt.date.today().isoformat()
    out = {"entities": len(by_nip), "found": 0, "not_registered": 0, "statuses": {}}
    nips = sorted(by_nip)
    for i in range(0, len(nips), BATCH):
        chunk = nips[i:i + BATCH]
        url = API.format(nips=",".join(chunk))
        r = client.request("GET", url, operation="search_nips", params={"date": date}, ok_status=(200, 400),
                           n_results=lambda x: len((x.json().get("result") or {}).get("entries") or []))
        entries = (r.json().get("result") or {}).get("entries") or []
        for entry in entries:
            nip = entry.get("identifier")
            ent = by_nip.get(nip)
            subjects = entry.get("subjects") or []
            if not ent:
                continue
            if not subjects:
                out["not_registered"] += 1
                status = "brak w wykazie"
                sub: dict[str, Any] = {}
            else:
                sub = subjects[0]
                status = sub.get("statusVat") or "nieznany"
                out["found"] += 1
            raw_id = save_raw(session, "vat_whitelist", f"nip:{nip}:{date}", url=PERMANENT.format(nip=nip, date=date),
                              retrieved_from=url, payload=_clean(sub, ent.natural_person_flag))
            eid = add_evidence(session, source_code="vat_whitelist", kind="api_field", key=(nip, date),
                               url=PERMANENT.format(nip=nip, date=date), retrieved_from=url,
                               retrieved_at=dt.datetime.now(dt.UTC), locator={"field": "statusVat", "nip": nip},
                               quote=status, raw_record_id=raw_id)
            ent.vat_status = status[:32]
            if sub.get("regon") and not ent.regon:
                ent.regon = str(sub["regon"])[:14]
            if sub.get("krs") and not ent.krs:
                ent.krs = str(sub["krs"])[:10]
            ent.verified_by = sorted(set(ent.verified_by or []) | {"VAT"})
            ent.evidence_ids = sorted(set(ent.evidence_ids or []) | {str(eid)})
            put_fact(session, subject_type="entity", subject_id=ent.id, fact_type="vat_status", key=(date,),
                     evidence_ids=[eid], value_text=status, value_date=dt.date.today())
            out["statuses"][status] = out["statuses"].get(status, 0) + 1
    return out
