"""Rule events from structured BZP data (knowledge: extra/event_rules.yaml, extra/art455_map.yaml).

Inputs are S1's tables (procedure, notice.sections, contract, contract_change). Every event cites the notice
section it comes from (permanent ezamowienia URL + verbatim quote); every computed effect (days, PLN) has a
derivation evidence (input evidence ids + formula). Writes go through `upsert_reviewable`, so an expert's
decision is never overwritten (a rerun stores a proposal instead).

    rep = extract_project(session, project_id)      # → {"events": {...}, "results": {id: inserted|...}}
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.evidence import add_evidence
from riskminer.core.upsert import upsert_reviewable
from riskminer.extract.catalog import ensure_proposed
from riskminer.extract.common import (
    derivation_evidence,
    find_dates,
    knowledge_rows,
    notice_evidence,
    notice_url,
    planned_end_from_period,
    section_value,
    to_float,
)
from riskminer.extract.reasons import PROPOSED, classify_reason, sentence_around
from riskminer.ids import make_id
from riskminer.models import Contract, ContractChange, Event, Notice, Procedure, ProjectProcedure

RULES_VERSION = "rules-v1"
CHANGE_PRIORITY = ("change_contractor", "change_scope", "change_value", "change_deadline")


@dataclass
class Report:
    results: dict[str, str] = field(default_factory=dict)  # event id → inserted|updated|unchanged|proposal
    by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        counts: dict[str, int] = defaultdict(int)
        for v in self.results.values():
            counts[v] += 1
        return {"events": len(self.results), "by_type": dict(self.by_type), "results": dict(counts),
                "errors": self.errors[:50]}


# ---------------------------------------------------------------- knowledge lookups


def _event_rules(session: Session) -> dict[str, dict[str, Any]]:
    return {r["event_type"]: r for r in knowledge_rows("event_rules", session)}


def _art455(session: Session) -> dict[str, dict[str, Any]]:
    meaning = {r["basis"]: r.get("meaning") for r in knowledge_rows("art455", session)}
    out = {}
    for r in knowledge_rows("art455_map", session):
        out[r["code"]] = {**r, "meaning": meaning.get(r["basis"])}
    return out


def basis_code(text: str | None) -> str | None:
    m = re.search(r"art\.?\s*455\s*ust\.?\s*(\d)(?:\s*pkt\.?\s*(\d))?", text or "", re.I)
    return None if not m else "455." + m.group(1) + ("." + m.group(2) if m.group(2) else "")


# ---------------------------------------------------------------- helpers


def _project_for(session: Session, procedure_id: uuid.UUID, part_no: int | None) -> uuid.UUID | None:
    links = session.execute(select(ProjectProcedure).where(ProjectProcedure.procedure_id == procedure_id,
                                                           ProjectProcedure.status != "rejected")
                            .order_by(ProjectProcedure.rank)).scalars().all()
    if part_no is not None:
        lot = [lk for lk in links if lk.part_no == part_no]
        if lot:
            return lot[0].project_id
    whole = [lk for lk in links if lk.part_no is None]
    return (whole or links or [None])[0].project_id if (whole or links) else None


def _emit(session: Session, rep: Report, *, event_type: str, key: tuple, **values: Any) -> uuid.UUID:
    eid = make_id("event", event_type, *key)
    vals = {"id": eid, "event_type": event_type, "method": values.pop("method", "rule"), **values}
    vals["evidence_ids"] = [str(e) for e in dict.fromkeys(vals.get("evidence_ids") or []) if e]
    for k in ("effect_pln",):
        if vals.get(k) is not None:
            vals[k] = Decimal(str(round(float(vals[k]), 2)))
    rep.results[str(eid)] = upsert_reviewable(session, Event, vals)
    rep.by_type[event_type] += 1
    return eid


def _codes(session: Session, hits, default: list[str]) -> tuple[list[str], float]:
    codes = list(dict.fromkeys(h.code for h in hits))
    for c in codes:
        if c.startswith("P-") and c in PROPOSED:
            ensure_proposed(session, c, PROPOSED[c][0], PROPOSED[c][1])
    return (codes, 0.8) if codes else (list(default), 0.5)


def _rule_derivation(session: Session, key: tuple, text: str, hits) -> uuid.UUID | None:
    if not hits:
        return None
    return derivation_evidence(session, key=("rule_hits", *key), inputs=[],
                               formula="reguły słownikowe przyczyn → kody R (extract/reasons.py)",
                               values={"hits": [{"code": h.code, "match": h.match} for h in hits]},
                               quote="; ".join(f"{h.code} ← „{h.match}”" for h in hits))


def _days(a: dt.date | None, b: dt.date | None) -> int | None:
    return (b - a).days if a and b else None


def _fmt(v: float | None) -> str:
    return "brak" if v is None else f"{v:,.2f}".replace(",", " ").replace(".", ",") + " zł"


# ---------------------------------------------------------------- contract-level rules


def _contract_events(session: Session, rep: Report, c: Contract, proc: Procedure, rules: dict, a455: dict) -> None:
    perf = session.get(Notice, c.performing_notice_id) if c.performing_notice_id else None
    project_id = _project_for(session, proc.id, c.part_no)
    base = dict(project_id=project_id, procedure_id=proc.id, contract_id=c.id, tier=proc.tier or "auto")
    part = c.part_no
    rd = lambda t: list((rules.get(t) or {}).get("default_risk_codes") or [])  # noqa: E731

    # planned end (calendar months) and its evidence
    period = section_value(perf, "4.2", part) or (c.meta or {}).get("period_text")
    planned_end, formula = (c.planned_end, "termin umowny") if c.planned_end else planned_end_from_period(c.signed_at, period)
    ev_signed = notice_evidence(session, perf, "4.1", part_no=part) if perf else None
    ev_period = notice_evidence(session, perf, "4.2", part_no=part) if perf else None

    changes = session.execute(select(ContractChange).where(ContractChange.contract_id == c.id)
                              .order_by(ContractChange.change_date.nulls_last(), ContractChange.change_no)).scalars().all()
    change_events = _change_events(session, rep, c, proc, perf, changes, planned_end, base, rules, a455)
    deadline_ends = [e for (t, e, _eid) in change_events if t == "deadline" and e]
    last_new_end = max(deadline_ends) if deadline_ends else None

    if perf is None:
        return
    # late (5.3)
    if c.on_time is False or (c.on_time is None and c.actual_end and planned_end and c.actual_end > planned_end):
        ev53 = notice_evidence(session, perf, "5.3", part_no=part)
        ev52 = notice_evidence(session, perf, "5.2", part_no=part)
        days = _days(planned_end, c.actual_end)
        der = None
        if days is not None:
            der = derivation_evidence(session, key=("late_days", c.id), inputs=[e for e in (ev_signed, ev_period, ev52) if e],
                                      formula=f"dni opóźnienia = termin wykonania (5.2) − termin pierwotny ({formula})",
                                      values={"signed_at": c.signed_at, "period": period, "planned_end": planned_end,
                                              "actual_end": c.actual_end, "days": days})
        beyond = _days(last_new_end, c.actual_end) if last_new_end else None
        effect = (f"Umowę wykonano {c.actual_end} zamiast {planned_end} (+{days} dni)" if days is not None
                  else "Umowy nie wykonano w pierwotnym terminie (5.3 = Nie)")
        if beyond is not None:
            effect += f"; względem terminu po aneksach ({last_new_end}): {'+' if beyond > 0 else ''}{beyond} dni"
        planned_days = _days(c.signed_at, planned_end)
        _emit(session, rep, event_type="late", key=(proc.id, c.id), **base, notice_id=perf.id,
              event_date=c.actual_end, risk_codes=rd("late"), title="Wykonanie po pierwotnym terminie",
              effect=effect, effect_days=days, effect_pct=(round(100 * days / planned_days, 1) if days and planned_days else None),
              quote=section_value(perf, "5.3", part), confidence=0.95 if c.on_time is False else 0.7,
              evidence_ids=[ev53, ev52, der])
    # paid above value (5.5 vs 4.4)
    paid, value = to_float(c.paid_gross), to_float(c.value_gross)
    if paid is not None and value and paid > value + 0.01:
        ev55 = notice_evidence(session, perf, "5.5", part_no=part)
        ev44 = notice_evidence(session, perf, "4.4", part_no=part)
        der = derivation_evidence(session, key=("paid_above", c.id), inputs=[ev55, ev44],
                                  formula="nadwyżka = wypłacono (5.5) − wartość umowy (4.4); % = nadwyżka / 4.4",
                                  values={"paid": paid, "value": value, "delta": round(paid - value, 2)})
        _emit(session, rep, event_type="paid_above_value", key=(proc.id, c.id), **base, notice_id=perf.id,
              event_date=c.actual_end, risk_codes=rd("paid_above_value"), title="Wypłata wyższa niż wartość umowy",
              effect=f"Wypłacono {_fmt(paid)} przy wartości umowy {_fmt(value)}", effect_pln=paid - value,
              effect_pct=round(100 * (paid - value) / value, 2), quote=section_value(perf, "5.5", part),
              confidence=0.95, evidence_ids=[ev55, ev44, der])
    # not performed (5.1)
    if c.performed is False:
        ev51 = notice_evidence(session, perf, "5.1", part_no=part)
        _emit(session, rep, event_type="not_performed", key=(proc.id, c.id), **base, notice_id=perf.id,
              risk_codes=rd("not_performed"), title="Umowa niewykonana (5.1 = Nie)", quote=section_value(perf, "5.1", part),
              confidence=0.95, evidence_ids=[ev51])
    text = perf.canonical_text or ""
    # terminated / withdrawn (free text in section V/VI)
    m = re.search(r"rozwiąza\w* umow|odstąpi\w* od umow|wypowiedz\w* umow", text, re.I)
    if m:
        q = sentence_around(text, m.start(), m.end())
        ev = add_evidence(session, source_code="bzp", kind="notice_section", key=(perf.object_id, "text", m.start()),
                          url=notice_url(perf), retrieved_from=perf.retrieved_from, retrieved_at=perf.retrieved_at,
                          locator={"section": "V/VI", "start": m.start(), "end": m.end(), "notice_number": perf.notice_number},
                          quote=q, notice_id=perf.id)
        _emit(session, rep, event_type="terminated", key=(proc.id, c.id), **base, notice_id=perf.id,
              risk_codes=rd("terminated"), title="Rozwiązanie / odstąpienie od umowy", quote=q, confidence=0.7,
              evidence_ids=[ev])
    # improper (5.6) or contractual penalties mentioned
    mk = re.search(r"kar\w* umown\w*", text, re.I)
    if c.proper is False or mk:
        evs, quote = [], None
        if c.proper is False:
            evs.append(notice_evidence(session, perf, "5.6", part_no=part))
            quote = section_value(perf, "5.6", part)
        if mk:
            q = sentence_around(text, mk.start(), mk.end())
            evs.append(add_evidence(session, source_code="bzp", kind="notice_section",
                                    key=(perf.object_id, "text", mk.start()), url=notice_url(perf),
                                    retrieved_from=perf.retrieved_from, retrieved_at=perf.retrieved_at,
                                    locator={"section": "VI", "start": mk.start(), "end": mk.end(),
                                             "notice_number": perf.notice_number}, quote=q, notice_id=perf.id))
            quote = quote or q
        title = ("Nienależyte wykonanie umowy (5.6 = Nie)" if c.proper is False
                 else "Kary umowne w ogłoszeniu o wykonaniu (5.6 = Tak)")
        effect = None
        if mk and paid is not None and value and paid < value:
            effect = f"Wypłata niższa od wartości umowy o {_fmt(value - paid)} (może obejmować kary umowne)"
        _emit(session, rep, event_type="improper", key=(proc.id, c.id), **base, notice_id=perf.id,
              risk_codes=rd("improper"), title=title, effect=effect, quote=quote,
              confidence=0.9 if c.proper is False else 0.6, evidence_ids=evs)
    _mitigation_effect(session, c, change_events, planned_end, last_new_end)


def _change_kinds(ch: ContractChange, code: str | None, text: str) -> list[str]:
    kinds = set(ch.change_kind or [])
    t = text.lower()
    if ch.new_end or re.search(r"termin|przedłuż|wydłuż|harmonogram", t):
        kinds.add("termin")
    if ch.value_delta or ch.new_value or re.search(r"wynagrodz\w* (?:umown|ryczałt|wykonawc)|zmian\w+ (?:kwoty|wartości|wynagrodz)|wzrost\w* (?:ceny|wynagrodz)|zwiększ\w+ wynagrodz", t):
        kinds.add("wynagrodzenie")
    if re.search(r"zakres|rob[oó]t\w* (?:dodatk|zamienn)|dodatkow\w+ (?:rob|prac)", t):
        kinds.add("zakres")
    if code == "455.1.2" or re.search(r"zmian\w+ wykonawc|nowy wykonawc|następc\w+ prawn", t):
        kinds.add("wykonawca")
    return sorted(kinds)


_KIND_TO_TYPE = {"wykonawca": "change_contractor", "zakres": "change_scope", "wynagrodzenie": "change_value",
                 "termin": "change_deadline"}


def _change_events(session, rep, c, proc, perf, changes, planned_end, base, rules, a455):
    """One event per distinct change (AgreementUpdate + ContractPerforming 5.4.x of the same change → one event)."""
    seen: dict[str, uuid.UUID] = {}
    out: list[tuple[str, dt.date | None, uuid.UUID]] = []
    prev_end = planned_end
    for ch in changes:
        notice = session.get(Notice, ch.notice_id) if ch.notice_id else None
        reason = (ch.reason or "").strip()
        desc = (ch.description or "").strip()
        dedup = re.sub(r"\W+", " ", reason.lower())[:120] or f"no-reason-{ch.id}"
        is_perf = notice is not None and notice.notice_type == "ContractPerformingNotice"
        nth = (ch.change_no or 1) - 1 if is_perf else 0
        sec_reason, sec_basis, sec_desc = ("5.4.4", "5.4.3", "5.4.5") if is_perf else ("5.3", "5.2", "5.4")
        evs = []
        if notice is not None:
            evs = [notice_evidence(session, notice, sec_reason, quote=reason or None, part_no=c.part_no, nth=nth,
                                   extra={"change_no": ch.change_no}),
                   notice_evidence(session, notice, sec_basis, part_no=c.part_no, nth=nth, extra={"change_no": ch.change_no})]
            if desc:
                evs.append(notice_evidence(session, notice, sec_desc, quote=desc, part_no=c.part_no, nth=nth,
                                           extra={"change_no": ch.change_no}))
        code = ch.legal_basis_code or basis_code(ch.legal_basis)
        basis = a455.get(code or "", {})
        kinds = _change_kinds(ch, code, f"{reason} {desc}")
        etype = next((_KIND_TO_TYPE[k] for k in ("wykonawca", "zakres", "wynagrodzenie", "termin") if k in kinds),
                     "change_other")
        hits = classify_reason(reason) or classify_reason(desc)
        default = list(basis.get("default_risk_codes") or []) or list((rules.get(etype) or {}).get("default_risk_codes") or [])
        codes, conf = _codes(session, hits, default)
        rule_ev = _rule_derivation(session, (c.id, dedup), reason, hits)
        new_end = ch.new_end
        if new_end is None and "termin" in kinds:
            ds = [d for d in find_dates(desc) + find_dates(reason) if not c.signed_at or d > c.signed_at]
            new_end = max(ds) if ds else None
        days = _days(prev_end, new_end) if new_end else None
        der = None
        if days is not None:
            der = derivation_evidence(session, key=("change_days", ch.id), inputs=[e for e in evs if e],
                                      formula="przesunięcie = nowy termin (opis zmiany) − poprzedni termin",
                                      values={"previous_end": prev_end, "new_end": new_end, "days": days})
        quote = reason
        if hits and len(reason) > 300:
            quote = sentence_around(reason, hits[0].start, hits[0].end)
        effect_parts = []
        if new_end:
            effect_parts.append(f"nowy termin {new_end}" + (f" (+{days} dni)" if days else ""))
        if ch.value_delta:
            effect_parts.append(f"zmiana wynagrodzenia {_fmt(to_float(ch.value_delta))}")
        mitigation = "Zmiana umowy" + (f" na podstawie {ch.legal_basis.strip()}" if ch.legal_basis else "")
        if basis.get("meaning"):
            mitigation += f" ({basis['meaning']})"
        if basis.get("note"):
            mitigation += f". {basis['note']}"
        if dedup in seen:  # same change also listed in another notice → add evidence only
            ev_old = session.get(Event, seen[dedup])
            if ev_old is not None and ev_old.status == "proposed":
                ev_old.evidence_ids = list(dict.fromkeys([*(ev_old.evidence_ids or []), *[str(e) for e in evs if e]]))
            continue
        eid = _emit(session, rep, event_type=etype, key=(proc.id, c.id, dedup), **base, change_id=ch.id,
                    notice_id=notice.id if notice else None, event_date=ch.change_date, risk_codes=codes,
                    title=f"Zmiana umowy nr {ch.change_no}" + (f" – {', '.join(kinds)}" if kinds else ""),
                    cause=reason or None, effect="; ".join(effect_parts) or None, effect_days=days,
                    effect_pln=to_float(ch.value_delta), mitigation=mitigation, quote=quote or None,
                    confidence=conf, evidence_ids=[*evs, der, rule_ev])
        seen[dedup] = eid
        out.append(("deadline" if "termin" in kinds else etype, new_end, eid))
        if new_end:
            prev_end = new_end
    return out


def _mitigation_effect(session, c: Contract, change_events, planned_end, last_new_end) -> None:
    """P1: did the amendments work? finished by the amended date, repeated extensions, 5.6, paid ≤ value + changes."""
    n_ext = sum(1 for t, _e, _ in change_events if t == "deadline")
    if not change_events:
        return
    paid, value = to_float(c.paid_gross), to_float(c.value_gross)
    delta = sum(to_float(session.get(Event, eid).effect_pln) or 0 for _t, _e, eid in change_events)
    checks = []
    verdict = "brak danych"
    if c.actual_end and last_new_end:
        ok = c.actual_end <= last_new_end
        checks.append(f"wykonano {c.actual_end} vs termin po zmianach {last_new_end}: {'dotrzymany' if ok else 'przekroczony'}")
        verdict = "skuteczne" if ok else "nieskuteczne"
        if ok and n_ext > 1:
            verdict = "częściowo"
    if n_ext > 1:
        checks.append(f"powtórne przedłużenia: {n_ext}")
    if c.proper is not None:
        checks.append(f"5.6 należyte wykonanie: {'Tak' if c.proper else 'Nie'}")
        if c.proper is False:
            verdict = "nieskuteczne"
    if paid is not None and value:
        okp = paid <= value + delta + 0.01
        checks.append(f"wypłata {_fmt(paid)} {'≤' if okp else '>'} wartość + zmiany {_fmt(value + delta)}")
        if not okp and verdict == "skuteczne":
            verdict = "częściowo"
    rule = f"n zmian = {len(change_events)}; " + "; ".join(checks) if checks else f"n zmian = {len(change_events)}; brak danych o wykonaniu"
    for _t, _e, eid in change_events:
        ev = session.get(Event, eid)
        if ev is not None and ev.status == "proposed":
            ev.mitigation_effect, ev.mitigation_rule = verdict, rule


# ---------------------------------------------------------------- procedure-level rules


def _procedure_events(session: Session, rep: Report, proc: Procedure, rules: dict) -> None:
    project_id = _project_for(session, proc.id, None)
    base = dict(project_id=project_id, procedure_id=proc.id, tier=proc.tier or "auto")
    rd = lambda t: list((rules.get(t) or {}).get("default_risk_codes") or [])  # noqa: E731
    notices = session.execute(select(Notice).where(Notice.procedure_id == proc.id)
                              .order_by(Notice.published_at)).scalars().all()
    results = [n for n in notices if n.notice_type == "TenderResultNotice"]
    tr = results[-1] if results else None
    # cancellation
    if proc.cancelled and tr is not None:
        reason = section_value(tr, "5.2.1") or section_value(tr, "5.2") or proc.cancel_basis or ""
        basis = " ".join(filter(None, [section_value(tr, "5.2"), section_value(tr, "5.1"), proc.cancel_basis]))
        over = bool(re.search(r"255\s*pkt\.?\s*3", basis + " " + reason) or
                    re.search(r"przewyższa\w* kwot|przekracza\w* kwot", reason, re.I))
        etype = "cancelled_over_budget" if over else "cancelled"
        evs = [notice_evidence(session, tr, "5.2.1" if section_value(tr, "5.2.1") else "5.2"),
               notice_evidence(session, tr, "5.1")]
        hits = classify_reason(reason)
        codes, conf = _codes(session, hits, rd(etype))
        if over and "R13" not in codes:
            codes = ["R13", *codes]
        _emit(session, rep, event_type=etype, key=(proc.id,), **base, notice_id=tr.id,
              event_date=tr.published_at.date() if tr.published_at else None, risk_codes=codes,
              title="Unieważnienie – oferty przewyższają kwotę (art. 255 pkt 3)" if over else "Unieważnienie postępowania",
              cause=reason or None, quote=reason[:600] or None, confidence=0.9 if over else conf, evidence_ids=evs)
    # single offer / offers above budget
    offers = proc.offers_count
    if offers is None and tr is not None:
        offers = int(to_float((section_value(tr, "6.1") or "").split()[0] if section_value(tr, "6.1") else None) or 0) or None
    if offers == 1 and tr is not None:
        _emit(session, rep, event_type="single_offer", key=(proc.id,), **base, notice_id=tr.id,
              risk_codes=rd("single_offer"), title="Złożono jedną ofertę", quote=section_value(tr, "6.1"),
              effect="Brak konkurencji cenowej – wyższe ryzyko ceny i wykonawcy", confidence=0.95,
              evidence_ids=[notice_evidence(session, tr, "6.1")])
    lowest = _amount(section_value(tr, "6.2")) if tr is not None else None
    budget = to_float(proc.budget_gross)
    if tr is not None and lowest:
        if budget and lowest > budget:
            der = derivation_evidence(session, key=("over_budget", proc.id), inputs=[notice_evidence(session, tr, "6.2")],
                                      formula="najniższa oferta (6.2) − kwota na sfinansowanie (brutto)",
                                      values={"lowest": lowest, "budget_gross": budget})
            _emit(session, rep, event_type="offers_above_budget", key=(proc.id,), **base, notice_id=tr.id,
                  risk_codes=rd("offers_above_budget"), title="Najniższa oferta powyżej kwoty na sfinansowanie",
                  effect=f"{_fmt(lowest)} > {_fmt(budget)}", effect_pln=lowest - budget,
                  effect_pct=round(100 * (lowest / budget - 1), 1), quote=section_value(tr, "6.2"), confidence=0.9,
                  evidence_ids=[notice_evidence(session, tr, "6.2"), der])
        elif not budget and proc.est_value_net:
            proxy = float(proc.est_value_net) * 1.23
            if lowest > proxy * 1.10:
                ev62, ev43 = notice_evidence(session, tr, "6.2"), notice_evidence(session, tr, "4.3")
                der = derivation_evidence(session, key=("over_estimate", proc.id), inputs=[ev62, ev43],
                                          formula="najniższa oferta (6.2, brutto) vs wartość zamówienia (4.3, netto) × 1,23 "
                                                  "(założenie VAT 23% – brak kwoty na sfinansowanie)",
                                          values={"lowest": lowest, "est_net": float(proc.est_value_net), "proxy_gross": proxy})
                _emit(session, rep, event_type="offers_above_budget", key=(proc.id,), **base, notice_id=tr.id,
                      risk_codes=rd("offers_above_budget"),
                      title="Najniższa oferta > szacunek brutto (przybliżenie: brak kwoty na sfinansowanie)",
                      effect=f"{_fmt(lowest)} vs {_fmt(proxy)} (szacunek netto × 1,23)", effect_pln=lowest - proxy,
                      effect_pct=round(100 * (lowest / proxy - 1), 1), quote=section_value(tr, "6.2"),
                      confidence=0.5, evidence_ids=[ev62, ev43, der])
    _repeated(session, rep, proc, notices, base, rd("repeated"))


def _amount(v: str | None) -> float | None:
    m = re.search(r"\d[\d ]*(?:[,.]\d{1,2})?", v or "")
    return float(m.group(0).replace(" ", "").replace(",", ".")) if m else None


def _repeated(session, rep, proc: Procedure, notices, base, default_codes) -> None:
    """Earlier cancelled procedure of the same buyer with (nearly) the same title → repeated procedure."""
    if not proc.buyer_nip or not proc.title:
        return
    from rapidfuzz import fuzz

    cands = session.execute(select(Procedure).where(Procedure.buyer_nip == proc.buyer_nip, Procedure.id != proc.id,
                                                    Procedure.cancelled.is_(True))).scalars().all()
    rel = {str(x) for x in (proc.related_procedure_ids or [])}
    for prev in cands:
        if proc.first_published_at and prev.first_published_at and prev.first_published_at >= proc.first_published_at:
            continue
        score = fuzz.token_set_ratio((prev.title or "").lower(), proc.title.lower())
        if score < 85 and str(prev.id) not in rel:
            continue
        cn = next((n for n in notices if n.notice_type == "ContractNotice"), notices[0] if notices else None)
        prev_n = session.execute(select(Notice).where(Notice.procedure_id == prev.id)
                                 .order_by(Notice.published_at)).scalars().first()
        evs = [add_evidence(session, source_code="bzp", kind="notice_section", key=(n.object_id, "title"),
                            url=notice_url(n), retrieved_from=n.retrieved_from, locator={"field": "orderObject",
                            "notice_number": n.notice_number}, quote=n.title, notice_id=n.id)
               for n in (cn, prev_n) if n is not None]
        der = derivation_evidence(session, key=("repeated", proc.id, prev.id), inputs=evs,
                                  formula="ten sam zamawiający (NIP), poprzednie postępowanie unieważnione, podobieństwo tytułów",
                                  values={"token_set_ratio": score, "previous_ocid": prev.ocid})
        _emit(session, rep, event_type="repeated", key=(proc.id, prev.id), **base,
              notice_id=cn.id if cn else None, risk_codes=default_codes,
              title=f"Postępowanie powtórzone po unieważnieniu ({prev.bzp_number or prev.ocid})",
              cause=prev.cancel_basis, quote=proc.title, confidence=round(min(0.95, score / 100), 2),
              evidence_ids=[*evs, der])


# ---------------------------------------------------------------- entry points


def extract_procedure(session: Session, procedure_id: uuid.UUID, rep: Report | None = None) -> Report:
    rep = rep or Report()
    proc = session.get(Procedure, procedure_id)
    if proc is None:
        rep.errors.append(f"procedure {procedure_id} not found")
        return rep
    rules, a455 = _event_rules(session), _art455(session)
    try:
        with session.begin_nested():
            _procedure_events(session, rep, proc, rules)
            for c in session.execute(select(Contract).where(Contract.procedure_id == proc.id)).scalars():
                _contract_events(session, rep, c, proc, rules, a455)
    except Exception as e:  # noqa: BLE001 – one bad procedure must not stop a batch
        rep.errors.append(f"{proc.ocid}: {type(e).__name__}: {e}")
    session.flush()
    return rep


def procedures_of_project(session: Session, project_id: uuid.UUID) -> list[uuid.UUID]:
    return list(session.execute(select(ProjectProcedure.procedure_id).where(
        ProjectProcedure.project_id == project_id, ProjectProcedure.status != "rejected")).scalars())


def extract_project(session: Session, project_id: uuid.UUID, rep: Report | None = None) -> Report:
    rep = rep or Report()
    for pid in procedures_of_project(session, project_id):
        extract_procedure(session, pid, rep)
    return rep
