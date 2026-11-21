#!/usr/bin/env python3
"""DEV-ONLY (S3): seed project/procedure/contract/contract_change from the extracted zip records.

Not production code – S1 owns acquisition/linking. Ids follow the shared conventions (make_id), so S1's real
rows replace these on merge. Run after bzp_auto_extract.py:

    uv run python scripts/dev/load_dev_cases.py [--in ../data/dev/bzp_auto.jsonl.gz] [--wipe]
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))

from riskminer.analysis.features import TERYT_VOIV, extract_rules, find_funding  # noqa: E402
from riskminer.analysis.knowledge import rows as krows  # noqa: E402
from riskminer.core.db import SessionLocal  # noqa: E402
from riskminer.core.evidence import NOTICE_PAGE, evidence_id  # noqa: E402
from riskminer.ids import make_id  # noqa: E402
from riskminer.models import Contract, ContractChange, Evidence, Procedure, Project, ProjectProcedure  # noqa: E402

ZIP_PATH = "data/raw/zip/risk_miner_bzp_kopia/bzp_kopia/notices.jsonl.xz"
XLSX = HERE.parents[2] / "tests/fixtures/organizer/Risk_Miner_dane_projekty.xlsx"


def d(s):
    try:
        return dt.date.fromisoformat(s) if s else None
    except ValueError:
        return None


def nip10(v):
    v = re.sub(r"\D", "", v or "")
    return v if len(v) == 10 else None


def batch_upsert(s, model, rows: list[dict], chunk: int = 2000) -> None:
    if not rows:
        return
    cols = {c.key for c in model.__table__.columns}
    for i in range(0, len(rows), chunk):
        part = [{k: v for k, v in r.items() if k in cols} for r in rows[i:i + chunk]]
        keys = sorted(set().union(*part))
        part = [{k: r.get(k) for k in keys} for r in part]
        stmt = insert(model).values(part)
        upd = {k: stmt.excluded[k] for k in keys if k not in ("id", "created_at")}
        s.execute(stmt.on_conflict_do_update(index_elements=["id"], set_=upd))
    s.commit()


def ev(object_id: str, notice_no: str, section: str, quote: str, rows: list[dict]) -> str:
    eid = evidence_id("bzp_zip", "notice_section", object_id, section)
    rows.append(dict(id=eid, source_code="bzp_zip", kind="notice_section", url=NOTICE_PAGE.format(object_id=object_id),
                     retrieved_from=f"{ZIP_PATH}#objectId={object_id}", locator={"notice_number": notice_no, "section": section},
                     quote=quote, created_by="dev_loader"))
    return str(eid)


def change_kind(c: dict) -> list[str]:
    t = f"{c.get('reason') or ''} {c.get('desc') or ''}".lower()
    k = []
    if re.search(r"termin|wydłuż|przedłuż|\d{1,2}\.\d{2}\.\d{4}|do dnia", t):
        k.append("termin")
    if c.get("price_up") or re.search(r"wynagrodzen|kwot|wartoś|cen[ay]", t):
        k.append("wynagrodzenie")
    if re.search(r"zakres|roboty dodatkowe|zamienn|rezygnac|ogranicz", t):
        k.append("zakres")
    return k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(HERE.parents[3] / "data/dev/bzp_auto.jsonl.gz"))
    ap.add_argument("--wipe", action="store_true", help="delete existing dev_loader rows first")
    ap.add_argument("--only", default="", help="comma list of tables to write (evidence,procedure,project,project_procedure,contract,contract_change)")
    a = ap.parse_args()

    by_ocid: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    cn_by_no: dict[str, str] = {}
    with gzip.open(a.inp, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("order_type") not in (None, "Works") or not r.get("ocid"):
                continue
            by_ocid[r["ocid"]][r["type"]].append(r)
            if r["type"] == "ContractNotice" and r.get("notice_no"):
                cn_by_no[r["notice_no"]] = r["ocid"]
    print("procedures in zip:", len(by_ocid))
    sub_rules = krows("subsector_rules")
    cpv_map = {}
    for rule in sub_rules:
        for c in rule.get("cpv") or []:
            cpv_map.setdefault(c, rule["subsector"])

    s = SessionLocal()
    if a.wipe:
        s.execute(text("DELETE FROM contract_change WHERE method='dev_loader'"))
        s.execute(text("DELETE FROM contract WHERE method='dev_loader'"))
        s.execute(text("DELETE FROM project_procedure WHERE method='dev_loader'"))
        s.execute(text("DELETE FROM project WHERE method='dev_loader'"))
        s.execute(text("DELETE FROM procedure WHERE meta->>'dev_loader'='true'"))
        s.execute(text("DELETE FROM evidence WHERE created_by='dev_loader'"))
        s.commit()

    P, PR, PP, C, CC, E = [], [], [], [], [], []
    n_proj = 0
    for ocid, g in by_ocid.items():
        cps, trs, cns, aus = g["ContractPerformingNotice"], g["TenderResultNotice"], g["ContractNotice"], g["AgreementUpdateNotice"]
        if not (cps or trs):
            continue
        first = (cns or trs or cps)[0]
        title = first["title"] or ""
        cpv = first.get("cpv") or ""
        proc_id = make_id("procedure", ocid)
        results = ";".join(t.get("result") or "" for t in trs)
        cancelled = bool(trs) and not cps and "zawarcieUmowy" not in results and "uniewaznienie" in results
        cancel = next((t for t in trs if t.get("cancel_basis")), None)
        est = next((t["est"] for t in trs if t.get("est")), None) or next((c["est"] for c in cns if c.get("est")), None)
        tr1 = trs[0] if len(trs) == 1 and (trs[0].get("n_parts") or 1) == 1 else None
        feats = extract_rules(title)
        sub = feats.subsector_main.value if feats.subsector_main else cpv_map.get(cpv)
        voiv = TERYT_VOIV.get((first.get("province") or "")[2:4])
        dnb = any(c.get("dnb") for c in cns) or bool(feats.formula and feats.formula.value == "zaprojektuj i wybuduj")
        pev = []
        for t in trs:
            if t.get("cancel_basis"):
                pev.append(ev(t["object_id"], t["notice_no"], "5.2", f"5.2.) Podstawa prawna unieważnienia postępowania: {t['cancel_basis']}", E))
            if t.get("n_offers") is not None:
                pev.append(ev(t["object_id"], t["notice_no"], "6.1", f"6.1.) Liczba otrzymanych ofert lub wniosków: {int(t['n_offers'])}", E))
            if t.get("est"):
                pev.append(ev(t["object_id"], t["notice_no"], "4.3", f"4.3.) Wartość zamówienia: {t['est']:.2f}", E))
        PR.append(dict(
            id=proc_id, ocid=ocid, bzp_number=(cns[0]["bzp"] if cns else None), title=title, cpv_main=cpv,
            mode=next((c.get("mode") for c in cps if c.get("mode")), None), order_type="Works", buyer_nip=nip10(first.get("buyer_nip")),
            est_value_net=est, budget_gross=next((t["budget"] for t in trs if t.get("budget")), None),
            planned_period_text=next((c.get("period_raw") for c in cps), None),
            planned_days=next((c.get("period_days") for c in cps if c.get("period_days")), None),
            parts=int(cns[0]["parts"]) if cns and cns[0].get("parts") else None,
            eu_funded=next((bool(c["eu"]) for c in cps if c.get("eu") is not None), None),
            eu_project_ref=next((c.get("eu_name") for c in cps if c.get("eu_name")), None),
            first_published_at=(cns or trs or cps)[0]["pub"] + "T00:00:00Z",
            offers_count=int(tr1["n_offers"]) if tr1 and tr1.get("n_offers") is not None else None,
            cancelled=cancelled, cancel_basis=cancel["cancel_basis"] if cancel else None, sector="wodkan",
            subsector_main=sub, tier="auto", evidence_ids=pev,
            meta={"dev_loader": "true", "cancel_reason": cancel["cancel_reason"] if cancel else None,
                  "tender_results": [{"notice_no": t["notice_no"], "result": t.get("result"), "n_offers": t.get("n_offers"),
                                      "price_min": t.get("price_min"), "price_max": t.get("price_max"),
                                      "price_won": t.get("price_won"), "est": t.get("est"), "budget": t.get("budget"),
                                      "object_id": t["object_id"]} for t in trs],
                  "design_and_build": dnb, "buyer": first.get("buyer"), "city": first.get("city")},
        ))
        if not cps and not cancelled:
            continue  # ongoing / no outcome: procedure only
        code = "AUTO-" + ocid.removeprefix("ocds-148610-")[:18]
        pid = make_id("project", code)
        n_proj += 1
        f_json = {k: v for k, v in feats.model_dump(exclude_none=True).items() if k not in ("cues", "extra", "vat_basis")}
        P.append(dict(
            id=pid, code=code, title=title, description=None, country="Polska", voivodeship=voiv,
            city=first.get("city"), sector="wodkan", subsector_main=sub,
            subsector_extra=(feats.subsector_extra.value if feats.subsector_extra else []),
            work_type=feats.work_type.value if feats.work_type else None,
            formula="zaprojektuj i wybuduj" if dnb else None, order_type="Roboty budowlane", currency="PLN",
            project_status="Unieważnione" if cancelled else "Zakończone",
            funding=next((c.get("eu_name") for c in cps if c.get("eu_name")), None),
            public_id_type="Ogłoszenie BZP", public_id_value=cns[0]["notice_no"] if cns else None,
            tier="auto", features=f_json, method="dev_loader", status="proposed", confidence=1.0,
            evidence_ids=pev[:3],
        ))
        PP.append(dict(id=make_id("project_procedure", pid, proc_id, None), project_id=pid, procedure_id=proc_id,
                       method="dev_loader", confidence=1.0, status="proposed",
                       components=[{"name": "ocid", "score": 1.0, "detail": "projekt auto = postępowanie (ten sam OCID)"}]))
        for c in cps:
            part = int(c["part_title"]) if c.get("part_title") else None
            cid = make_id("contract", proc_id, part, c.get("contractor_nip") or c["object_id"])
            oid, no = c["object_id"], c["notice_no"]
            cev = [ev(oid, no, "4.4", f"4.4.) Wartość umowy: {c['value']}" if c.get("value") else "4.4.) Wartość umowy: brak", E)]
            if c.get("on_time") is not None:
                cev.append(ev(oid, no, "5.3", "5.3.) Czy umowę wykonano w pierwotnie określonym terminie: "
                              + ("Tak" if c["on_time"] else "Nie"), E))
            if c.get("paid") is not None:
                cev.append(ev(oid, no, "5.5", f"5.5.) Łączna wartość wynagrodzenia wypłacona z tytułu zrealizowanej umowy: {c['paid']}", E))
            if c.get("period_raw"):
                cev.append(ev(oid, no, "4.2", f"4.2.) Okres realizacji zamówienia: {c['period_raw']}", E))
            if c.get("done_date"):
                cev.append(ev(oid, no, "5.2", f"5.2.) Termin wykonania umowy: {c['done_date']}", E))
            signed = d(c.get("signed"))
            pdays = c.get("period_days")
            C.append(dict(
                id=cid, procedure_id=proc_id, part_no=part, signed_at=signed, value_gross=c.get("value"),
                offers_count=int(tr1["n_offers"]) if tr1 and tr1.get("n_offers") is not None else None,
                lowest_offer=tr1.get("price_min") if tr1 else None, highest_offer=tr1.get("price_max") if tr1 else None,
                planned_days=pdays, planned_end=(signed + dt.timedelta(days=pdays)) if signed and pdays else None,
                actual_end=d(c.get("done_date")), paid_gross=c.get("paid"), on_time=None if c.get("on_time") is None else bool(c["on_time"]),
                performed=None if c.get("done") is None else bool(c["done"]),
                proper=None if c.get("proper") is None else bool(c["proper"]), n_changes=c.get("n_changes"),
                terms_source="ogłoszenie", method="dev_loader", status="proposed", confidence=1.0, evidence_ids=cev,
                meta={"object_id": oid, "notice_no": no, "result_notice": c.get("result_notice"), "extra": c.get("extra"),
                      "contractor": c.get("contractor"), "contractor_nip": c.get("contractor_nip"),
                      "est_value_net": est, "currency": c.get("currency"), "dev_loader": True},
            ))
            for ch in c.get("changes") or []:
                e1 = ev(oid, no, f"5.4.3#{ch['no']}", f"5.4.3.) Podstawa prawna zmiany: {ch.get('basis') or ''}", E)
                e2 = ev(oid, no, f"5.4.4#{ch['no']}", f"5.4.4.) Przyczyny dokonania zmian: {ch.get('reason') or ''}", E)
                CC.append(dict(
                    id=make_id("contract_change", cid, oid, ch["no"]), contract_id=cid, procedure_id=proc_id, change_no=ch["no"],
                    legal_basis=ch.get("basis"), legal_basis_code=ch.get("code"), reason=ch.get("reason"),
                    description=ch.get("desc"), change_kind=change_kind(ch), value_delta=ch.get("delta"),
                    method="dev_loader", status="proposed", confidence=1.0, evidence_ids=[e1, e2]))
        if not cps:
            continue
        has_cp_changes = any(c.get("changes") for c in cps)
        if not has_cp_changes and aus:
            cid0 = C[-1]["id"]
            for u in aus:
                e1 = ev(u["object_id"], u["notice_no"], "5.2", f"5.2.) Podstawa prawna zmiany umowy/umowy ramowej: {u.get('basis') or ''}", E)
                CC.append(dict(
                    id=make_id("contract_change", cid0, u["object_id"], 1), contract_id=cid0, procedure_id=proc_id,
                    change_no=1, change_date=d(u.get("change_date")), legal_basis=u.get("basis"), legal_basis_code=u.get("code"),
                    reason=u.get("reason"), description=u.get("desc"), change_kind=change_kind(u), method="dev_loader",
                    status="proposed", confidence=1.0, evidence_ids=[e1]))

    # deep tier: the 22 organizer rows (S1 builds the real ones with the same ids)
    ws = openpyxl.load_workbook(XLSX)["Projekty"]
    hdr = None
    for r in ws.iter_rows(values_only=True):
        if hdr is None:
            hdr = r
            continue
        if not r[1]:
            continue
        row = dict(zip(hdr, r, strict=False))
        code, ann = row["Identyfikator rekordu"], row["Adnotacja instytucji"] or ""
        desc_m = re.search(r"Opis: „(.*)”", ann, re.S)
        text_all = f"{row['Nazwa przedsięwzięcia']}. {desc_m.group(1) if desc_m else ''}"
        feats = extract_rules(text_all)
        val = re.search(r"Wartość przedsięwzięcia: ([\d  ]+,\d{2}) zł", ann)
        grant = re.search(r"dofinansowanie: ([\d  ]+,\d{2}) zł", ann)
        num = (lambda m: float(m.group(1).replace(" ", "").replace(" ", "").replace(",", ".")) if m else None)
        pid = make_id("project", code)
        fund = find_funding(ann)
        P.append(dict(
            id=pid, code=code, title=row["Nazwa przedsięwzięcia"], description=desc_m.group(1) if desc_m else None,
            country="Polska", teryt=row["Kod województwa (TERYT)"], voivodeship=row["Województwo"], city=row["Siedziba odbiorcy"],
            sector="wodkan", subsector_main=feats.subsector_main.value if feats.subsector_main else None,
            subsector_extra=feats.subsector_extra.value if feats.subsector_extra else [],
            work_type=feats.work_type.value if feats.work_type else None,
            formula=feats.formula.value if feats.formula else None, order_type=row["Rodzaj zamówienia"],
            legal_regime=row["Reżim prawny"], currency=row["Waluta rozliczeń"], project_status=row["Status przedsięwzięcia"],
            funding=fund.value if fund else None, project_value=num(val), grant_value=num(grant),
            public_id_type=row["Rodzaj identyfikatora publicznego"], public_id_value=row["Identyfikator publiczny"],
            record_scope=row["Zakres rekordu"], annotation=ann or None, tier="deep",
            features={k: v for k, v in feats.model_dump(exclude_none=True).items() if k not in ("cues", "extra", "vat_basis")},
            method="dev_loader", status="proposed", confidence=1.0, evidence_ids=[],
        ))
        ocid = cn_by_no.get(row["Identyfikator publiczny"])
        if ocid:
            proc_id = make_id("procedure", ocid)
            PP.append(dict(id=make_id("project_procedure", pid, proc_id, None), project_id=pid, procedure_id=proc_id,
                           method="dev_loader", confidence=1.0, status="proposed",
                           components=[{"name": "notice_no", "score": 1.0, "detail": row["Identyfikator publiczny"]}]))
    seen = set()
    E = [e for e in E if not (e["id"] in seen or seen.add(e["id"]))]
    print(f"projects={len(P)} (auto {n_proj}) procedures={len(PR)} contracts={len(C)} changes={len(CC)} evidence={len(E)}")
    only = set(filter(None, a.only.split(",")))

    def want(m) -> bool:
        return not only or m.__tablename__ in only

    if want(Evidence):
        batch_upsert(s, Evidence, E)
    if want(Procedure):
        batch_upsert(s, Procedure, PR)
    if want(Project):
        batch_upsert(s, Project, P)
    # a deep project may now point at an auto procedure that also has an auto project – fine for dev
    pp_seen = set()
    PP = [x for x in PP if not (x["id"] in pp_seen or pp_seen.add(x["id"]))]
    if want(ProjectProcedure):
        batch_upsert(s, ProjectProcedure, PP)
    cs = set()
    C = [x for x in C if not (x["id"] in cs or cs.add(x["id"]))]
    if want(Contract):
        batch_upsert(s, Contract, C)
    ccs = set()
    CC = [x for x in CC if not (x["id"] in ccs or ccs.add(x["id"]))]
    if want(ContractChange):
        batch_upsert(s, ContractChange, CC)
    s.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
