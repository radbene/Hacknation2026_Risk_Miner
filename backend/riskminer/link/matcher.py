"""Project → procedure linking: keys first, scored candidates for the rest.

Order (design §5): expert override (rule kind=link_override) → KPO number found in notice sections →
BZP number from the xlsx (→ OCID, NIP check) → cross-reference chain (the number appears only as a
prior-notice reference, e.g. Wolin) → lot (part N via TenderResult part / 'Umowa dla części nr N') →
fuzzy scoring of same-NIP procedures (title, location tokens, CPV/subsector, soft date window, value, consistency).
Every component carries an evidence id. Decoys are stored in `alternatives`; cancelled look-alikes become
siblings (`procedure.related_procedure_ids`). Writes use upsert_reviewable – expert decisions survive reruns.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Any

from rapidfuzz import fuzz
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from riskminer.connectors.bzp_store import api_evidence, field_evidence, is_wodkan
from riskminer.core.upsert import upsert_reviewable
from riskminer.ids import make_id
from riskminer.models import (
    Contract,
    DataIssue,
    Entity,
    Notice,
    Procedure,
    Project,
    ProjectProcedure,
    ReviewStatus,
    Rule,
)
from riskminer.parse.bzp_notices import norm_notice_no

WEIGHTS = {"title": 0.40, "location": 0.15, "cpv": 0.10, "date": 0.10, "value": 0.10, "scope": 0.10,
           "consistency": 0.05}
STOP = set("budowa przebudowa rozbudowa modernizacja sieci sieć sanitarnej sanitarna kanalizacji kanalizacja "
           "wodociągowej wodociągowa wodociągowych w na i oraz z ze do terenie gminy gminie gmina miejscowości "
           "miejscowość m. ul. wraz etap część formule zaprojektuj wybuduj dla od o".split())
AUTO_ACCEPT = 0.80  # fuzzy best above this (and clear margin) → linked; still 'proposed' for the expert


def norm_title(s: str | None) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[„”\"“'`,.;:()\[\]–—-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def place_tokens(s: str | None) -> set[str]:
    toks = {t for t in norm_title(s).split() if len(t) > 3 and t not in STOP and not t.isdigit()}
    return {t[:6] for t in toks}  # crude stemming for Polish inflection (Modlikowice/Modlikowicach)


@dataclass
class Candidate:
    procedure: Procedure
    score: float
    method: str
    components: list[dict[str, Any]] = field(default_factory=list)
    part_no: int | None = None
    why_not: str | None = None


def _comp(name: str, score: float, detail: str, evidence_id: str | None = None, weight: float | None = None) -> dict:
    return {"name": name, "score": round(float(score), 3), "weight": weight, "detail": detail,
            "evidence_id": evidence_id}


def _notices(session: Session, proc: Procedure) -> list[Notice]:
    return session.execute(select(Notice).where(Notice.procedure_id == proc.id).order_by(Notice.published_at)).scalars().all()


def _title_ev(session: Session, proc: Procedure, notices: list[Notice]) -> str | None:
    for n in notices:
        if n.notice_type == "ContractNotice" and (e := field_evidence(session, n, "title")):
            return e
    return api_evidence(session, notices[0], "orderObject", notices[0].title) if notices else None


def _xlsx_ev(project: Project, fld: str) -> str | None:
    return ((project.import_row or {}).get("evidence") or {}).get(fld)


def _year_window(project: Project) -> tuple[int, int] | None:
    m = re.search(r"/(\d{2})$", project.public_id_value or "")
    if m and (project.public_id_type or "").lower().startswith("projekt kpo"):
        y = 2000 + int(m.group(1))
        return y - 1, y + 2
    m = re.match(r"^(\d{4})/BZP", project.public_id_value or "")
    if m:
        y = int(m.group(1))
        return y - 1, y + 1
    return None


def score_candidate(session: Session, project: Project, proc: Procedure, notices: list[Notice]) -> Candidate:
    comps = []
    pt = norm_title(project.title)
    titles = {norm_title(proc.title)} | {norm_title(n.title) for n in notices if n.title}
    t_ratio = max((fuzz.token_set_ratio(pt, t) * 0.5 + fuzz.ratio(pt, t) * 0.5) / 100 for t in titles) if titles else 0
    comps.append(_comp("title", t_ratio, f"Podobieństwo tytułu {t_ratio:.0%}: „{proc.title}”",
                       _title_ev(session, proc, notices), WEIGHTS["title"]))
    ptoks = place_tokens(project.title) | place_tokens(project.description)
    ntext = " ".join([proc.title or ""] + [(n.parsed or {}).get("description") or "" for n in notices[:3]]
                     + [((n.parsed or {}).get("parts") or {}).get("0", {}).get("description") or "" for n in notices[:2]])
    ntoks = place_tokens(ntext)
    shared = sorted(ptoks & ntoks)
    loc = len(shared) / max(1, min(len(ptoks), 6))
    comps.append(_comp("location", min(1.0, loc), f"Wspólne nazwy: {', '.join(shared) or 'brak'}",
                       _xlsx_ev(project, "title"), WEIGHTS["location"]))
    wk = 1.0 if any(is_wodkan({"cpvCode": n.cpv, "orderObject": n.title}) for n in notices) else 0.0
    comps.append(_comp("cpv", wk, f"CPV {proc.cpv_main or '?'} – {'roboty wodno-kanalizacyjne' if wk else 'poza robotami wodno-kanalizacyjnymi'}",
                       api_evidence(session, notices[0], "cpvCode", notices[0].cpv) if notices else None, WEIGHTS["cpv"]))
    win = _year_window(project)
    year = proc.first_published_at.year if proc.first_published_at else None
    if win and year:
        d = 0 if win[0] <= year <= win[1] else min(abs(year - win[0]), abs(year - win[1]))
        ds = max(0.0, 1 - 0.5 * d)
        comps.append(_comp("date", ds, f"Rok publikacji {year}; oczekiwane {win[0]}–{win[1]} (z numeru {project.public_id_value})",
                           _xlsx_ev(project, "public_id_value"), WEIGHTS["date"]))
    else:
        comps.append(_comp("date", 0.5, "Brak okna dat", None, WEIGHTS["date"]))
    contracts = session.execute(select(Contract).where(Contract.procedure_id == proc.id)).scalars().all()
    pv = float(project.project_value) if project.project_value else None
    cv = sum(float(c.value_gross or 0) for c in contracts) or None
    if pv and cv:
        r = min(pv, cv) / max(pv, cv)
        comps.append(_comp("value", r, f"Wartość umów {cv:,.2f} zł vs wartość przedsięwzięcia {pv:,.2f} zł "
                                       f"(stosunek {r:.2f}, bez założeń o VAT)", _xlsx_ev(project, "annotation"),
                           WEIGHTS["value"]))
    else:
        comps.append(_comp("value", 0.5, "Brak wartości do porównania", None, WEIGHTS["value"]))
    status_done = (project.project_status or "").lower().startswith("zakończ")
    has_cp = any(n.notice_type == "ContractPerformingNotice" for n in notices)
    cons = 1.0 if (status_done == has_cp) else 0.3
    if proc.cancelled:
        cons = 0.0
    comps.append(_comp("consistency", cons, ("unieważnione; " if proc.cancelled else "")
                       + f"status xlsx {project.project_status!r}, ogłoszenie o wykonaniu: {'tak' if has_cp else 'nie'}",
                       _xlsx_ev(project, "project_status"), WEIGHTS["consistency"]))
    comps.append(_comp("scope", 0.5, "Zakres (km, przyłącza) – porównanie niedostępne w regułach", None, WEIGHTS["scope"]))
    total = sum(c["score"] * (c["weight"] or 0) for c in comps) / sum(WEIGHTS.values())
    return Candidate(procedure=proc, score=round(total, 3), method="fuzzy", components=comps)


def _override(session: Session, project: Project) -> dict | None:
    rows = session.execute(select(Rule).where(Rule.kind == "link_override", Rule.key == project.code,
                                              Rule.active.is_(True)).order_by(Rule.version.desc())).scalars().all()
    return rows[0].body if rows else None


def _proc_by(session: Session, **kw) -> Procedure | None:
    return session.execute(select(Procedure).filter_by(**kw)).scalars().first()


def key_candidates(session: Session, project: Project, nip: str | None, procs: list[Procedure]) -> list[Candidate]:
    out: list[Candidate] = []
    pid_type = (project.public_id_type or "").lower()
    pid = (project.public_id_value or "").strip()
    if "kpo" in pid_type and pid:
        for p in procs:
            if pid in ((p.meta or {}).get("kpo_numbers") or []):
                ns = _notices(session, p)
                ev = next((e for n in ns if pid in " ".join((n.parsed or {}).get("eu", {}).get("kpo_numbers") or [])
                           and (e := field_evidence(session, n, "eu.name"))), None)
                out.append(Candidate(p, 1.0, "kpo_ref", [
                    _comp("kpo_ref", 1.0, f"Numer KPO {pid} w treści ogłoszenia (sekcja projektu UE)", ev),
                    _comp("nip", 1.0, f"NIP zamawiającego {p.buyer_nip} = NIP odbiorcy", api_evidence(session, ns[0], "organizationNationalId", p.buyer_nip))]))
    if "bzp" in pid_type and pid:
        num = norm_notice_no(pid)
        p = _proc_by(session, bzp_number=num)
        if p is not None:
            ns = _notices(session, p)
            has_cn = (p.meta or {}).get("has_contract_notice")
            nip_ok = p.buyer_nip == nip
            if has_cn:
                cn = next(n for n in ns if n.notice_type == "ContractNotice")
                comps = [_comp("notice_no", 1.0, f"Numer ogłoszenia {pid} → OCID {p.ocid}", api_evidence(session, cn, "noticeNumber", cn.notice_number))]
                method, conf = "notice_no", 1.0
            else:  # number exists only as a cross-reference (organizer number of a notice absent from BZP)
                xn = next((n for n in ns for x in n.xrefs or [] if x.get("notice_number") == num), ns[0])
                comps = [_comp("xref", 0.95, f"Numer {pid} nie istnieje w BZP; występuje jako odwołanie (sekcja 3.2.1/2.14) "
                                             f"w ogłoszeniu {xn.notice_number} → OCID {p.ocid}",
                               field_evidence(session, xn, "prior_notice"))]
                method, conf = "xref", 0.95
            comps.append(_comp("nip", 1.0 if nip_ok else 0.0, f"NIP zamawiającego {p.buyer_nip} {'=' if nip_ok else '≠'} NIP odbiorcy {nip}",
                               api_evidence(session, ns[0], "organizationNationalId", p.buyer_nip)))
            out.append(Candidate(p, conf if nip_ok else 0.5, method, comps))
    return out


def _lot(session: Session, project: Project, cand: Candidate) -> None:
    if not project.part_no:
        return
    cand.part_no = project.part_no
    c = session.execute(select(Contract).where(Contract.procedure_id == cand.procedure.id,
                                               Contract.part_no == project.part_no)).scalars().first()
    if c is None:
        cand.components.append(_comp("lot", 0.0, f"Brak umowy dla części {project.part_no}", None))
        cand.score = round(cand.score * 0.8, 3)
        return
    ent = session.get(Entity, c.contractor_id) if c.contractor_id else None
    cand.components.append(_comp("lot", 1.0, f"Część {project.part_no}: wykonawca {ent.name if ent else '?'} "
                                             f"({(c.meta or {}).get('contractor_id')}), wartość {c.value_gross} zł, "
                                             f"umowa z {c.signed_at}", (c.evidence_ids or [None])[0]))


def link_project(session: Session, project: Project, actor: str = "system") -> dict[str, Any]:
    """Link one project. Returns {status: linked|uncertain|unlinked|override, method, confidence, procedure}."""
    ent = session.get(Entity, project.beneficiary_id) if project.beneficiary_id else None
    nip = ent.nip if ent else None
    procs = session.execute(select(Procedure).where(Procedure.buyer_nip == nip)).scalars().all() if nip else []
    ov = _override(session, project)
    chosen: list[Candidate] = []
    if ov:
        p = None
        if ov.get("procedure_id"):
            p = session.get(Procedure, uuid.UUID(str(ov["procedure_id"])))
        elif ov.get("ocid"):
            p = _proc_by(session, ocid=ov["ocid"])
        if p is not None:
            c = Candidate(p, 1.0, "expert", [_comp("expert", 1.0, f"Powiązanie wskazane przez eksperta: {ov.get('comment') or ''}".strip(), None)],
                          part_no=ov.get("part_no", project.part_no))
            chosen = [c]
    keys = [] if chosen else key_candidates(session, project, nip, procs)
    scored = []
    for p in procs:
        ns = _notices(session, p)
        if ns:
            scored.append(score_candidate(session, project, p, ns))
    scored.sort(key=lambda c: -c.score)
    if not chosen and keys:
        best = max(keys, key=lambda c: c.score)
        fz = next((s for s in scored if s.procedure.id == best.procedure.id), None)
        if fz:  # explanation also for key matches
            best.components += [c for c in fz.components if c["name"] in ("title", "date", "value")]
        chosen = [best]
    if not chosen and scored:
        best = scored[0]
        second = scored[1].score if len(scored) > 1 else 0.0
        best.components.append(_comp("margin", min(1.0, (best.score - second) * 5),
                                     f"Przewaga nad kolejnym kandydatem: {best.score - second:+.2f}", None))
        if best.score >= 0.5:
            chosen = [best]
    for c in chosen:
        _lot(session, project, c)

    # alternatives (decoys) + siblings
    status = "unlinked"
    linked_ids = {c.procedure.id for c in chosen}
    for c in chosen:
        alts = []
        for s in scored:
            if s.procedure.id in linked_ids or s.score < 0.35:
                continue
            why = "unieważnione" if s.procedure.cancelled else f"niższy wynik ({s.score:.2f} < {c.score:.2f})"
            alts.append({"procedure_id": str(s.procedure.id), "ocid": s.procedure.ocid, "bzp_number": s.procedure.bzp_number,
                         "title": s.procedure.title, "score": s.score, "components": s.components, "why_not": why})
        alts = alts[:5]
        siblings = [s.procedure for s in scored if s.procedure.id not in linked_ids and s.procedure.cancelled
                    and next((x["score"] for x in s.components if x["name"] == "title"), 0) >= 0.8]
        if siblings:
            proc = c.procedure
            proc.related_procedure_ids = sorted({*(proc.related_procedure_ids or []), *[str(s.id) for s in siblings]})
            c.components.append(_comp("siblings", 1.0, "Powiązane postępowania unieważnione/powtórzone: "
                                      + "; ".join(f"{s.bzp_number} {s.title}" for s in siblings), None))
        conf = 1.0 if c.method in ("kpo_ref", "notice_no", "expert") else c.score
        if c.method == "fuzzy":
            margin = c.score - (alts[0]["score"] if alts else 0)
            conf = round(min(0.95, c.score), 3)
            status = "linked" if c.score >= AUTO_ACCEPT and margin >= 0.15 else "uncertain"
        else:
            status = "override" if c.method == "expert" else ("linked" if conf >= 0.95 else "uncertain")
        lid = make_id("project_procedure", project.id, c.procedure.id, c.part_no or 0)
        upsert_reviewable(session, ProjectProcedure, dict(
            id=lid, project_id=project.id, procedure_id=c.procedure.id, part_no=c.part_no, method=c.method,
            confidence=conf, components=c.components, alternatives=alts, is_override=c.method == "expert", rank=1,
            evidence_ids=sorted({x["evidence_id"] for x in c.components if x.get("evidence_id")})), actor=actor)
        if c.method == "expert":
            row = session.get(ProjectProcedure, lid)
            if row.status == ReviewStatus.proposed.value:
                row.status, row.reviewed_by = ReviewStatus.approved.value, actor
        if c.method == "xref":
            upsert_reviewable(session, DataIssue, dict(
                id=make_id("data_issue", project.code, "organizer_error", "public_id_value"), project_id=project.id,
                procedure_id=c.procedure.id, kind="organizer_error", field="public_id_value", state="sprzeczne",
                message=f"Numer ogłoszenia {project.public_id_value} z pliku nie istnieje w BZP. Postępowanie odnalezione "
                        f"przez odwołania w ogłoszeniach (OCID {c.procedure.ocid}).",
                what_to_add="Potwierdź numer ogłoszenia o zamówieniu u organizatora",
                impact="Brak ogłoszenia o zamówieniu – brak kryteriów i pierwotnego terminu z SWZ",
                method="rule", confidence=0.95, evidence_ids=[x["evidence_id"] for x in c.components if x.get("evidence_id")][:3]),
                actor=actor)
    # drop stale machine proposals (never reviewed rows)
    session.execute(delete(ProjectProcedure).where(
        ProjectProcedure.project_id == project.id, ProjectProcedure.status == ReviewStatus.proposed.value,
        ProjectProcedure.id.notin_([make_id("project_procedure", project.id, c.procedure.id, c.part_no or 0) for c in chosen] or [uuid.uuid4()])))
    if not chosen:
        upsert_reviewable(session, DataIssue, dict(
            id=make_id("data_issue", project.code, "missing", "procedure"), project_id=project.id, kind="missing",
            field="procedure", state="brak",
            message=f"Nie znaleziono postępowania BZP dla NIP {nip} ({len(procs)} postępowań kandydujących).",
            what_to_add="Wskaż OCID lub numer ogłoszenia (powiązanie ręczne)", impact="Brak umów, zmian i zdarzeń",
            method="rule", confidence=1.0), actor=actor)
    c0 = chosen[0] if chosen else None
    return {"project": project.code, "status": status, "method": c0.method if c0 else None,
            "confidence": (1.0 if c0 and c0.method in ("kpo_ref", "notice_no", "expert") else (c0.score if c0 else None)),
            "procedure": c0.procedure.ocid if c0 else None, "part_no": c0.part_no if c0 else None,
            "candidates": len(scored), "alternatives": len(scored) - (1 if c0 else 0)}


def link_all(session: Session, project_ids: list[uuid.UUID] | None = None, actor: str = "system") -> list[dict]:
    q = select(Project).where(Project.tier == "deep")
    if project_ids:
        q = q.where(Project.id.in_(project_ids))
    return [link_project(session, p, actor) for p in session.execute(q.order_by(Project.code)).scalars().all()]
