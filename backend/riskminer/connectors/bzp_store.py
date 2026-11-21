"""Store BZP API records: raw_record → notice (DOM sections, xrefs, parsed) → procedure / contract / change.

`store_notice()` is called by every BZP source (live API, mirror, zip). `build_procedure(ocid)` derives the
procedure, its contracts (one per lot × contractor) and contract changes from *all* notices of that OCID, so
the result does not depend on the order notices arrive in. Everything is idempotent (uuid5 ids, upserts) and
reviewed rows are never overwritten (upsert_reviewable). Every value written cites a notice-section evidence
(permanent ezamowienia URL; the mirror/zip goes to `retrieved_from`).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.evidence import NOTICE_PAGE, NOTICE_PDF, add_evidence
from riskminer.core.upsert import jsonable, upsert, upsert_reviewable
from riskminer.ids import make_id, nip_valid
from riskminer.models import Contract, ContractChange, Entity, Notice, Procedure, RawRecord, Source
from riskminer.parse.bzp_dom import PARSER_VERSION
from riskminer.parse.bzp_notices import contractor_id, norm_notice_no, parse_notice

WODKAN_CPV = ("45231300", "45232400", "45232410", "45232420", "45232421", "45232430", "45232440", "45232150",
              "45232130", "45252100", "45252126", "45252127", "45232411", "45232423", "45231100", "45231110",
              "45232100", "45232120", "45232000", "45252000", "45247000", "45240000")
WODKAN_KW = re.compile(r"wodoci|kanaliz|oczyszczal|\bSUW\b|uzdatn|przepompown|deszczow|retencj|tłoczn|ścieków|sciek",
                       re.I)
LEGAL_FORM_RE = re.compile(r"sp\.|spółk|s\.a\.|z\s*o\.\s*o|\bS\.?A\b|zakład|przedsiębiorstwo gospodarki|gmin|"
                           r"spółdzielni|konsorcj|\bPGK\b|\bZGK\b|instytut|uniwersytet", re.I)

SOURCES = {
    "bzp": ("BZP – API e-Zamówienia (mirror HackNation / oficjalne)", "https://ezamowienia.gov.pl/mo-board/api/v1/notice"),
    "bzp_zip": ("BZP – kopia ogłoszeń wod-kan (paczka organizatora)", "https://bzp.cytr.us/paczka/risk_miner_bzp_kopia.zip"),
}
LICENCE = "Informacja publiczna (ustawa o dostępie do informacji publicznej); Biuletyn Zamówień Publicznych, UZP"


def ensure_sources(session: Session) -> None:
    for code, (name, url) in SOURCES.items():
        upsert(session, Source, dict(id=make_id("source", code), code=code, name=name, base_url=url, licence=LICENCE,
                                     data_location="local"))


def is_wodkan(rec: dict[str, Any]) -> bool:
    cpv = rec.get("cpvCode") or ""
    return any(c in cpv for c in WODKAN_CPV) or bool(WODKAN_KW.search(rec.get("orderObject") or ""))


def _pub(rec: dict[str, Any]) -> dt.datetime | None:
    s = rec.get("publicationDate")
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def natural_person(name: str | None) -> bool:
    """Sole traders (natural persons) – masked in the UI. Heuristic: no legal-form marker in the name."""
    return bool(name) and not LEGAL_FORM_RE.search(name or "")


def entity_for(session: Session, raw_id: str | None, name: str | None, role: str, city: str | None = None,
               province: str | None = None, evidence: list[str] | None = None) -> uuid.UUID | None:
    cid, kind = contractor_id(raw_id)
    if not cid and not name:
        return None
    if kind == "NIP":
        eid = make_id("entity", cid)
    elif kind == "REGON":
        eid = make_id("entity", "REGON", cid)
    else:
        eid = make_id("entity", "name", name)
    ent = session.get(Entity, eid)
    if ent is None:
        upsert(session, Entity, dict(
            id=eid, name=(name or cid or "?").strip(), nip=cid if kind == "NIP" else None,
            regon=cid if kind == "REGON" else None, role=role, city=city, province=province, country="PL",
            verified_by=["BZP"] if kind == "NIP" and nip_valid(cid) else [],
            natural_person_flag=role == "contractor" and natural_person(name),
            aliases=[name] if name else [], evidence_ids=evidence or []))
    else:
        if name and name not in (ent.aliases or []):
            ent.aliases = [*(ent.aliases or []), name]
        if evidence:
            ent.evidence_ids = sorted({*(ent.evidence_ids or []), *evidence})
        if "BZP" not in (ent.verified_by or []) and kind == "NIP" and nip_valid(cid):
            ent.verified_by = [*(ent.verified_by or []), "BZP"]
    return eid


def store_notice(session: Session, rec: dict[str, Any], *, source_code: str = "bzp", retrieved_from: str | None = None,
                 retrieved_at: dt.datetime | None = None, tier: str = "auto", keep_html: bool = True,
                 op_log_id: uuid.UUID | None = None) -> tuple[uuid.UUID, str]:
    """Insert/update one notice. Returns (notice_id, 'inserted'|'updated'|'unchanged')."""
    oid = rec["objectId"]
    retrieved_at = retrieved_at or dt.datetime.now(dt.UTC)
    body = json.dumps(rec, sort_keys=True, ensure_ascii=False)
    sha = hashlib.sha256(body.encode()).hexdigest()
    raw_id = make_id("raw_record", source_code, oid, sha)
    payload = rec if keep_html else {k: v for k, v in rec.items() if k != "htmlBody"}
    upsert(session, RawRecord, dict(id=raw_id, source_code=source_code, key=oid, url=NOTICE_PAGE.format(object_id=oid),
                                    retrieved_from=retrieved_from, retrieved_at=retrieved_at, sha256=sha,
                                    content_type="application/json", payload=payload, op_log_id=op_log_id,
                                    blob_path=None if keep_html else retrieved_from),
           index_elements=["source_code", "key", "sha256"])
    nid = make_id("notice", oid)
    existing = session.get(Notice, nid)
    if existing is not None and existing.raw_record_id == raw_id and existing.parser_version == PARSER_VERSION:
        if tier == "deep" and existing.tier != "deep":
            existing.tier = "deep"
            return nid, "updated"
        return nid, "unchanged"
    dom, parsed, xr = parse_notice(rec)
    upsert(session, Notice, dict(
        id=nid, object_id=oid, notice_number=rec.get("noticeNumber") or "", bzp_number=rec.get("bzpNumber"),
        notice_type=rec.get("noticeType") or "", ocid=rec.get("tenderId"), published_at=_pub(rec),
        title=rec.get("orderObject"), org_name=rec.get("organizationName"),
        org_nip=re.sub(r"\D", "", rec.get("organizationNationalId") or "")[:10] or None,
        org_city=rec.get("organizationCity"), org_province=rec.get("organizationProvince"), cpv=rec.get("cpvCode"),
        order_type=rec.get("orderType"), below_eu=rec.get("isTenderAmountBelowEU"),
        contractors=rec.get("contractors") or [], url=NOTICE_PAGE.format(object_id=oid),
        pdf_url=NOTICE_PDF.format(object_id=oid), retrieved_from=retrieved_from, retrieved_at=retrieved_at,
        raw_record_id=raw_id, canonical_text=dom.canonical_text, sections=dom.sections(), xrefs=jsonable(xr),
        parsed=jsonable(parsed), parser_version=PARSER_VERSION,
        tier="deep" if tier == "deep" or (existing is not None and existing.tier == "deep") else tier))
    return nid, ("inserted" if existing is None else "updated")


# ---------------------------------------------------------------- evidence for parsed values

def field_evidence(session: Session, n: Notice, path: str) -> str | None:
    """Evidence for the DOM field that produced parsed value `path` (e.g. 'parts.1.value')."""
    idx = (n.parsed or {}).get("refs", {}).get(path)
    if idx is None or idx >= len(n.sections or []):
        return None
    f = n.sections[idx]
    return str(add_evidence(
        session, source_code="bzp", kind="notice_section", key=(n.object_id, idx), url=n.url,
        retrieved_from=n.retrieved_from, retrieved_at=n.retrieved_at, quote=(f.get("value") or "")[:4000],
        notice_id=n.id, raw_record_id=n.raw_record_id,
        locator={"notice_number": n.notice_number, "notice_type": n.notice_type, "section": f.get("section"),
                 "label": f.get("label"), "part_no": f.get("part_no"), "field_index": idx,
                 "start": f.get("offset"), "end": (f.get("offset") or 0) + len(f.get("value") or "")}))


def api_evidence(session: Session, n: Notice, field: str, value: Any) -> str:
    return str(add_evidence(session, source_code="bzp", kind="api_field", key=(n.object_id, field), url=n.url,
                            retrieved_from=n.retrieved_from, retrieved_at=n.retrieved_at, quote=str(value)[:2000],
                            notice_id=n.id, raw_record_id=n.raw_record_id,
                            locator={"notice_number": n.notice_number, "notice_type": n.notice_type, "field": field}))


def _d(v: Any) -> dt.date | None:
    if not v:
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _dec(v: Any) -> Decimal | None:
    return None if v is None else Decimal(str(v))


# ---------------------------------------------------------------- procedure / contracts / changes

def build_procedure(session: Session, ocid: str, tier: str | None = None, actor: str = "system") -> uuid.UUID | None:
    notices = session.execute(select(Notice).where(Notice.ocid == ocid).order_by(Notice.published_at)).scalars().all()
    if not notices:
        return None
    pid = make_id("procedure", ocid)
    by_type: dict[str, list[Notice]] = {}
    for n in notices:
        by_type.setdefault(n.notice_type, []).append(n)
    cn = (by_type.get("ContractNotice") or [None])[-1]
    trs = by_type.get("TenderResultNotice") or []
    tr = trs[-1] if trs else None
    first = notices[0]
    ev: list[str] = []

    def take(n: Notice | None, path: str, value: Any) -> Any:
        if n is not None and value not in (None, "", []):
            e = field_evidence(session, n, path)
            if e:
                ev.append(e)
        return value

    bzp_number = None
    if cn:
        bzp_number = norm_notice_no(cn.notice_number)
        ev.append(api_evidence(session, cn, "noticeNumber", cn.notice_number))
    else:  # procedure number from cross-references (prior notice 2.14 / 3.1.1 / 3.2.1), never a result notice
        results = {x["notice_number"] for n in notices for x in n.xrefs or [] if x.get("kind") == "result_notice"}
        results |= {norm_notice_no(n.notice_number) for n in notices}
        for n in notices:
            for x in n.xrefs or []:
                if x.get("kind") == "prior_notice" and x.get("source") == "bzp" and x["notice_number"] not in results:
                    bzp_number = x["notice_number"]
                    ev.append(field_evidence(session, n, "prior_notice") or api_evidence(session, n, "xref", bzp_number))
                    break
            if bzp_number:
                break
    cnp = (cn.parsed if cn else {}) or {}
    trp = (tr.parsed if tr else {}) or {}
    cn_part0 = (cnp.get("parts") or {}).get("0") or (cnp.get("parts") or {}).get("1") or {}
    titles = [cnp.get("title"), trp.get("title"), *[(n.parsed or {}).get("title") for n in notices], first.title]
    title = next((t for t in titles if t), None)
    kpo = sorted({k for n in notices for k in ((n.parsed or {}).get("eu") or {}).get("kpo_numbers", [])})
    eu_funded = next((((n.parsed or {}).get("eu") or {}).get("funded") for n in notices
                      if ((n.parsed or {}).get("eu") or {}).get("funded") is not None), None)
    tr_parts = trp.get("parts") or {}
    cancelled = bool(tr_parts) and all(p.get("cancelled") for p in tr_parts.values())
    cancel_basis = next((p.get("cancel_basis") for p in tr_parts.values() if p.get("cancel_basis")), None)
    offers = sum(p.get("n_offers") or 0 for p in tr_parts.values()) if tr_parts else None
    buyer = entity_for(session, first.org_nip, first.org_name, "buyer", first.org_city, first.org_province,
                       [api_evidence(session, first, "organizationNationalId", first.org_nip)])
    cpv_main = cn_part0.get("cpv_main") or (re.match(r"\d{8}", first.cpv or "") or [None])[0]
    existing = session.get(Procedure, pid)
    vals = dict(
        id=pid, ocid=ocid, bzp_number=bzp_number, title=title,
        cpv_main=take(cn, "parts.0.cpv_main" if "0" in (cnp.get("parts") or {}) else "parts.1.cpv_main", cpv_main),
        cpv_extra=cn_part0.get("cpv_extra") or [], mode=take(cn or tr, "mode", (cnp or trp).get("mode")),
        order_type=first.order_type, buyer_id=buyer, buyer_nip=first.org_nip,
        est_value_net=_dec(take(tr, "est_value", trp.get("est_value"))),
        planned_period_text=take(cn, "parts.0.period" if "0" in (cnp.get("parts") or {}) else "parts.1.period",
                                 cn_part0.get("period")),
        planned_days=cn_part0.get("planned_days"),
        parts=take(cn, "n_parts", cnp.get("n_parts")) or (trp.get("n_parts") or None),
        eu_funded=eu_funded, eu_project_ref=";".join(kpo) or None,
        platform_url=take(cn, "platform_url", cnp.get("platform_url")),
        ted_refs=sorted({x["notice_number"] for n in notices for x in n.xrefs or [] if x.get("source") == "ted"}),
        first_published_at=first.published_at, offers_count=offers or None, cancelled=cancelled if tr_parts else None,
        cancel_basis=cancel_basis, sector="wodkan" if any(is_wodkan({"cpvCode": n.cpv, "orderObject": n.title})
                                                          for n in notices) else None,
        tier="deep" if (tier == "deep" or any(n.tier == "deep" for n in notices)
                        or (existing is not None and existing.tier == "deep")) else (tier or "auto"),
        meta={"notice_ids": [str(n.id) for n in notices], "kpo_numbers": kpo,
              "notice_types": {k: len(v) for k, v in by_type.items()}, "has_contract_notice": cn is not None},
        evidence_ids=sorted(set(ev)),
    )
    if existing is not None:  # keep fields enriched elsewhere (siblings, watched)
        vals["related_procedure_ids"] = existing.related_procedure_ids or []
    upsert(session, Procedure, vals)
    for n in notices:
        if n.procedure_id != pid:
            n.procedure_id = pid
    _build_contracts(session, pid, ocid, notices, tr, actor)
    return pid


def _match_part(n: Notice, tr_parts: dict[str, Any]) -> str | None:
    """Assign a performing/change notice to a lot: explicit 'Umowa dla części nr N', then contractor + value/date."""
    p = n.parsed or {}
    if p.get("lot_no"):
        return str(p["lot_no"])
    if not tr_parts:
        return None
    if len(tr_parts) == 1:
        return next(iter(tr_parts))
    cid = ((p.get("contractor") or {}).get("id"))
    val, signed = p.get("value"), p.get("signed_at")
    best, best_score = None, 0.0
    for key, tp in tr_parts.items():
        s = 0.0
        if cid and (tp.get("contractor") or {}).get("id") == cid:
            s += 1
        if val is not None and tp.get("value") is not None and abs(float(val) - float(tp["value"])) < 1.0:
            s += 2
        if signed and tp.get("signed_at") == signed:
            s += 0.5
        if s > best_score:
            best, best_score = key, s
    return best if best_score >= 1.5 else None


def _build_contracts(session: Session, pid: uuid.UUID, ocid: str, notices: list[Notice], tr: Notice | None,
                     actor: str) -> None:
    trp = (tr.parsed if tr else {}) or {}
    tr_parts = {k: v for k, v in (trp.get("parts") or {}).items() if (v.get("contractor") or {}).get("id")
                or (v.get("contractor") or {}).get("name")}
    contracts: dict[str, dict[str, Any]] = {}

    def cslot(part_key: str | None, contractor: dict[str, Any]) -> dict[str, Any]:
        key = f"{part_key or 0}|{contractor.get('id') or contractor.get('name') or '?'}"
        if key not in contracts:
            contracts[key] = {"part_key": part_key, "contractor": contractor, "ev": [], "vals": {}, "cp": None,
                              "aus": []}
        return contracts[key]

    for key, tp in tr_parts.items():
        c = cslot(key if key != "0" else None, tp.get("contractor") or {})
        v = c["vals"]
        v.update(result_notice_id=tr.id, signed_at=_d(tp.get("signed_at")), value_gross=_dec(tp.get("value")),
                 offers_count=tp.get("n_offers"), lowest_offer=_dec(tp.get("price_min")),
                 highest_offer=_dec(tp.get("price_max")), planned_end=_d(tp.get("planned_end")),
                 planned_days=tp.get("planned_days"))
        for f in ("signed_at", "value", "n_offers", "price_min", "period", "contractor.id"):
            path = f"parts.{key}.{f}"
            if e := field_evidence(session, tr, path):
                c["ev"].append(e)
    for n in notices:
        if n.notice_type not in ("ContractPerformingNotice", "AgreementUpdateNotice"):
            continue
        p = n.parsed or {}
        part_key = _match_part(n, tr_parts)
        contractor = p.get("contractor") or {}
        if part_key and part_key in tr_parts and not contractor.get("id"):
            contractor = tr_parts[part_key].get("contractor") or contractor
        # attach to an existing slot of the same part (contractor ids may differ NIP vs REGON across notices)
        same = [c for c in contracts.values() if c["part_key"] == (part_key if part_key != "0" else None)]
        c = same[0] if len(same) == 1 else cslot(part_key if part_key != "0" else None, contractor)
        v = c["vals"]
        for k, val in (("signed_at", _d(p.get("signed_at"))), ("value_gross", _dec(p.get("value"))),
                       ("planned_end", _d(p.get("planned_end"))), ("planned_days", p.get("planned_days"))):
            if v.get(k) is None and val is not None:
                v[k] = val
        for f in ("signed_at", "value", "period"):
            if e := field_evidence(session, n, f):
                c["ev"].append(e)
        if n.notice_type == "ContractPerformingNotice":
            if c["cp"] is None or (n.published_at and c["cp"].published_at and n.published_at > c["cp"].published_at):
                c["cp"] = n
        else:
            c["aus"].append(n)

    for c in contracts.values():
        part_no = int(c["part_key"]) if c["part_key"] and c["part_key"] != "0" else None
        con = c["contractor"]
        cev = [e for e in [field_evidence(session, tr, f"parts.{c['part_key']}.contractor.id") if tr and c["part_key"]
                           else None] if e]
        ent = entity_for(session, con.get("id_raw") or con.get("id"), con.get("name"), "contractor", con.get("city"),
                         evidence=cev)
        v = dict(c["vals"])
        cp = c["cp"]
        if cp is not None:
            p = cp.parsed or {}
            v.update(performing_notice_id=cp.id, actual_end=_d(p.get("end_date")), paid_gross=_dec(p.get("paid")),
                     on_time=p.get("on_time"), performed=p.get("performed"), proper=p.get("proper"),
                     n_changes=p.get("n_changes"))
            for f in ("end_date", "paid", "on_time", "performed", "proper", "n_changes"):
                if e := field_evidence(session, cp, f):
                    c["ev"].append(e)
        elif c["aus"]:
            v["n_changes"] = len(c["aus"])
        cid = make_id("contract", ocid, part_no or 0, ent or "?")
        upsert_reviewable(session, Contract, dict(
            id=cid, procedure_id=pid, part_no=part_no, contractor_id=ent, terms_source="ogłoszenie",
            method="rule", confidence=1.0, evidence_ids=sorted(set(c["ev"])),
            meta={"contractor_name": con.get("name"), "contractor_id": con.get("id"),
                  "contractor_id_type": con.get("id_type"),
                  "agreement_update_ids": [str(a.id) for a in c["aus"]]}, **v), actor=actor)
        _build_changes(session, cid, pid, c["aus"], cp, v.get("value_gross"), actor)


def _build_changes(session: Session, contract_id: uuid.UUID, pid: uuid.UUID, aus: list[Notice], cp: Notice | None,
                   value: Decimal | None, actor: str) -> None:
    rows = []
    for n in sorted(aus, key=lambda x: ((x.parsed or {}).get("change", {}).get("date") or "", x.published_at or 0)):
        ch = (n.parsed or {}).get("change") or {}
        rows.append((n, ch, "change"))
    if cp is not None:
        for k, ch in enumerate((cp.parsed or {}).get("changes") or []):
            if k >= len(rows):  # changes reported only in the performing notice
                rows.append((cp, ch, f"changes.{k}"))
    for i, (n, ch, pre) in enumerate(rows, start=1):
        ev = [e for f in ("legal_basis", "reason", "description", "value", "date", "change_no")
              if (e := field_evidence(session, n, f"{pre}.{f}"))]
        val = _dec(ch.get("value"))
        new_value = delta = None
        if val is not None:
            if value and val >= value * Decimal("0.5"):
                new_value, delta = val, val - value
            else:
                delta = val
        upsert_reviewable(session, ContractChange, dict(
            id=make_id("contract_change", contract_id, n.id, ch.get("change_no") or i), contract_id=contract_id,
            procedure_id=pid, notice_id=n.id, change_no=i, change_date=_d(ch.get("date")),
            legal_basis=ch.get("legal_basis"), legal_basis_code=ch.get("legal_basis_code"), reason=ch.get("reason"),
            description=ch.get("description"), change_kind=ch.get("kinds") or [], value_delta=delta,
            new_value=new_value, new_end=_d(ch.get("new_end")), method="rule", confidence=1.0,
            evidence_ids=sorted(set(ev))), actor=actor)
