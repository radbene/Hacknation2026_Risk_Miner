"""TEST-ONLY helper: builds notice/procedure/contract/contract_change rows from raw BZP notices (notices22).

S1 owns the real parser (`riskminer/parse/`). This mimics its documented output shape
(notice.sections = [{section, label, value, offset, part_no}]) just enough for S2 tests. Do not import from
application code.
"""

from __future__ import annotations

import datetime as dt
import html
import re

from riskminer.core.upsert import upsert
from riskminer.ids import make_id
from riskminer.models import Contract, ContractChange, Notice, Procedure, Project, ProjectProcedure

_H = re.compile(r"<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>", re.S | re.I)
_SEC = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\)\s*(.*)$", re.S)


def _text(fragment: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\s*\n\s*", "\n", s).strip()


def sections(body: str) -> tuple[list[dict], str]:
    body = body[body.find("<main>"):] if "<main>" in body else body
    body = re.sub(r"<footer.*", "", body, flags=re.S)
    heads = list(_H.finditer(body))
    out, canon, part = [], [], None
    for i, m in enumerate(heads):
        inner = m.group(1) or m.group(2) or ""
        nxt = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        if m.group(2) is not None:
            t = _text(inner)
            pm = re.search(r"Część\s+(\d+)", t)
            if pm:
                part = int(pm.group(1))
            tail = _text(body[m.end():nxt])
            canon.append(f"{t}\n{tail}" if tail else t)
            continue
        span = re.search(r"<span[^>]*>(.*)</span>", inner, re.S)
        label_html = inner[:span.start()] if span else inner
        value = _text(span.group(1)) if span else _text(body[m.end():nxt])
        label = _text(label_html)
        sm = _SEC.match(label)
        if not sm:
            continue
        sec, lab = sm.group(1), sm.group(2).strip().rstrip(":")
        off = len("\n".join(canon)) + (1 if canon else 0) + len(label) + 1
        canon.append(f"{label} {value}".strip())
        out.append({"section": sec, "label": lab, "value": value, "offset": off, "part_no": part})
    return out, "\n".join(canon)


def _sv(secs, num, nth=0):
    rows = [s for s in secs if s["section"] == num]
    return rows[nth]["value"] if len(rows) > nth else None


def _num(v):
    if not v:
        return None
    m = re.search(r"\d[\d ]*(?:[,.]\d{1,2})?", v)
    return float(m.group(0).replace(" ", "").replace(",", ".")) if m else None


def _date(v):
    m = re.search(r"\d{4}-\d{2}-\d{2}", v or "")
    return dt.date.fromisoformat(m.group(0)) if m else None


def _yn(v):
    return {"Tak": True, "Nie": False}.get((v or "").strip()[:3].strip())


def _basis_code(v):
    m = re.search(r"art\.\s*455\s*ust\.\s*(\d)(?:\s*pkt\s*(\d))?", v or "")
    return None if not m else ("455." + m.group(1) + ("." + m.group(2) if m.group(2) else ""))


def load(session, notices: list[dict], project_code: str | None = None) -> dict:
    """Insert rows for the notices of one procedure (same tenderId). Returns ids."""
    from riskminer.extract.common import planned_end_from_period

    ocid = notices[0]["tenderId"]
    pid = make_id("procedure", ocid)
    cn = next((n for n in notices if n["noticeType"] == "ContractNotice"), None)
    tr = next((n for n in notices if n["noticeType"] == "TenderResultNotice"), None)
    parsed = {n["objectId"]: sections(n.get("htmlBody") or "") for n in notices}
    tr_secs = parsed[tr["objectId"]][0] if tr else []
    upsert(session, Procedure, dict(
        id=pid, ocid=ocid, bzp_number=(cn or notices[0])["bzpNumber"], title=notices[0]["orderObject"],
        buyer_nip=notices[0]["organizationNationalId"], tier="deep",
        est_value_net=_num(_sv(tr_secs, "4.3")), offers_count=int(_num(_sv(tr_secs, "6.1")) or 0) or None,
        cancelled=bool(tr and "uniewaznienie" in (tr.get("procedureResult") or "")),
        cancel_basis=(_sv(tr_secs, "5.2") or "") + " " + (_sv(tr_secs, "5.2.1") or "") if tr else None,
        first_published_at=(cn or notices[0])["publicationDate"]))
    nids = {}
    for n in notices:
        secs, canon = parsed[n["objectId"]]
        nid = make_id("notice", n["objectId"])
        nids[n["objectId"]] = nid
        upsert(session, Notice, dict(
            id=nid, object_id=n["objectId"], notice_number=n["noticeNumber"], bzp_number=n["bzpNumber"],
            notice_type=n["noticeType"], procedure_id=pid, ocid=ocid, published_at=n["publicationDate"],
            title=n["orderObject"], org_name=n["organizationName"], org_nip=n["organizationNationalId"],
            url=f"https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/{n['objectId']}",
            retrieved_from="zip:notices.jsonl.xz", canonical_text=canon, sections=secs, parser_version="test"))
    session.flush()
    contracts = []
    for n in notices:
        if n["noticeType"] not in ("ContractPerformingNotice", "AgreementUpdateNotice"):
            continue
        secs = parsed[n["objectId"]][0]
        cnip = ((n.get("contractors") or [{}])[0] or {}).get("contractorNationalId")
        cid = make_id("contract", pid, None, cnip)
        signed = _date(_sv(secs, "4.1"))
        planned_end, _ = planned_end_from_period(signed, _sv(secs, "4.2"))
        vals = dict(id=cid, procedure_id=pid, part_no=None, signed_at=signed, value_gross=_num(_sv(secs, "4.4")),
                    planned_end=planned_end, offers_count=int(_num(_sv(tr_secs, "6.1")) or 0) or None,
                    lowest_offer=_num(_sv(tr_secs, "6.2")), highest_offer=_num(_sv(tr_secs, "6.3")),
                    result_notice_id=nids.get(tr["objectId"]) if tr else None, meta={"period_text": _sv(secs, "4.2")})
        if n["noticeType"] == "ContractPerformingNotice":
            vals.update(performing_notice_id=nids[n["objectId"]], performed=_yn(_sv(secs, "5.1")),
                        actual_end=_date(_sv(secs, "5.2")), on_time=_yn(_sv(secs, "5.3")),
                        paid_gross=_num(_sv(secs, "5.5")), proper=_yn(_sv(secs, "5.6")),
                        n_changes=int(_num(_sv(secs, "5.4.1")) or 0))
        existing = session.get(Contract, cid)
        if existing is None:
            session.add(Contract(**vals))
        else:
            for k, v in vals.items():
                if v is not None:
                    setattr(existing, k, v)
        session.flush()
        contracts.append(cid)
        if n["noticeType"] == "ContractPerformingNotice":
            k = 0
            while _sv(secs, "5.4.2", k) is not None:
                desc = _sv(secs, "5.4.5", k)
                session.add(ContractChange(
                    id=make_id("contract_change", cid, nids[n["objectId"]], k + 1), contract_id=cid, procedure_id=pid,
                    notice_id=nids[n["objectId"]], change_no=k + 1, legal_basis=_sv(secs, "5.4.3", k),
                    legal_basis_code=_basis_code(_sv(secs, "5.4.3", k)), reason=_sv(secs, "5.4.4", k), description=desc,
                    method="test"))
                k += 1
        else:
            session.add(ContractChange(
                id=make_id("contract_change", cid, nids[n["objectId"]], 1), contract_id=cid, procedure_id=pid,
                notice_id=nids[n["objectId"]], change_no=1, change_date=_date(_sv(secs, "5.1")),
                legal_basis=_sv(secs, "5.2"), legal_basis_code=_basis_code(_sv(secs, "5.2")),
                reason=_sv(secs, "5.3"), description=_sv(secs, "5.4"), method="test"))
        session.flush()
    project_id = None
    if project_code:
        project_id = make_id("project", project_code)
        if session.get(Project, project_id) is None:
            session.add(Project(id=project_id, code=project_code, title=notices[0]["orderObject"], tier="deep",
                                project_status="Zakończone"))
            session.flush()
        upsert(session, ProjectProcedure, dict(id=make_id("project_procedure", project_id, pid, None),
                                               project_id=project_id, procedure_id=pid, part_no=None,
                                               method="test", status="approved"))
    session.flush()
    return {"procedure_id": pid, "notice_ids": nids, "contract_ids": contracts, "project_id": project_id}


def by_ocid(notices22: list[dict], ocid: str) -> list[dict]:
    return sorted([n for n in notices22 if n["tenderId"] == ocid], key=lambda n: n["publicationDate"])
