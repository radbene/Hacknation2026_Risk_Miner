"""Red flags and recommended actions for a new investment (path B), rules only – every flag says why.

Sources of a flag (each keeps n / case ids / quotes so the expert can check it):
  1. neighbours' history – risk codes of events (contract changes, delays, cancellations) of the named neighbours;
  2. ranges – P(late), P(change), paid/contract ratio, art. 255 pkt 3 cancellations among similar procedures;
  3. assessment – budget / schedule position against the neighbours;
  4. the description – cues (land, permits, collisions, PFU, lump sum, start-up …) and stated gaps ("brak zgód");
  5. checklist – 9-point expert checklist items with no information in the description.
Actions = expert clause per flagged risk + lessons (NIK, exemplary events) + checklist items.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.analysis.knowledge import rows as krows
from riskminer.models import Clause, Event, Lesson

CUE_RISKS = {
    "land": (["R03"], "Trasa / teren wymaga praw do nieruchomości", "średnia"),
    "permits": (["R04"], "Inwestycja zależy od decyzji i uzgodnień podmiotów trzecich", "średnia"),
    "environment": (["R02", "R04"], "Uwarunkowania środowiskowe lub gruntowo-wodne", "średnia"),
    "collisions": (["R03", "R02"], "Kolizje z istniejącą infrastrukturą", "średnia"),
    "existing_asset": (["R06", "R10"], "Roboty przy czynnym obiekcie", "średnia"),
    "pfu": (["R01", "R05", "R09"], "Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności", "średnia"),
    "lump_sum": (["R08"], "Wynagrodzenie ryczałtowe przy niepewnym zakresie", "niska"),
    "startup": (["R10"], "Rozruch / próby / odbiór parametrów", "niska"),
}
SEV_ORDER = {"wysoka": 0, "średnia": 1, "niska": 2}
LEVEL_PL = {"neighbours": "sąsiedzi", "subsector": "podsektor", "wodkan": "wod-kan", "works": "wszystkie roboty"}


def _pct(x: float | None) -> str:
    return "?" if x is None else f"{x:.0%}"


def _fv(features: dict[str, Any], name: str) -> Any:
    x = features.get(name)
    return x.get("value") if isinstance(x, dict) else x


def risk_names(session: Session | None) -> dict[str, str]:
    return {r["code"]: r["name"] for r in krows("risks", session)}


def _signal_codes(sentence: str, session: Session | None) -> list[str]:
    out = []
    low = sentence.lower()
    for r in krows("risk_signals", session):
        if any(p.lower() in low for p in r.get("patterns") or []):
            out.append(r["code"])
    return out


def neighbour_history(session: Session, neighbour_ids: list[uuid.UUID], cases: list | None = None) -> dict[str, dict[str, Any]]:
    """{R-code: {k: #neighbours with an event of that code, events:[…]}}.

    Deep-tier neighbours: their events (rules + expert decisions). Auto-tier neighbours have no event rows, so
    their contract-change reasons (BZP section 7.x / 5.4) are classified to R-codes with the same rule classifier.
    """
    from riskminer.extract.reasons import classify_reason

    out: dict[str, dict[str, Any]] = defaultdict(lambda: {"projects": set(), "events": []})
    if not neighbour_ids:
        return {}
    with_events = set(session.execute(select(Event.project_id).where(Event.project_id.in_(neighbour_ids))).scalars())
    for c in cases or []:
        if c.project_id in with_events:
            continue
        for ch in c.change_reasons:
            for h in classify_reason(ch.get("reason")):
                if not h.code.startswith("R"):
                    continue
                d = out[h.code]
                d["projects"].add(c.project_id)
                if len(d["events"]) < 5:
                    d["events"].append({"event_id": f"{c.project_id}:{h.code}:{len(d['events'])}", "project_id": str(c.project_id),
                                        "title": f"{c.code}: zmiana umowy ({ch.get('code') or 'podstawa ?'})",
                                        "cause": ch.get("reason", "")[:300], "quote": ch.get("reason", "")[:300], "match": h.match,
                                        "evidence_ids": ch.get("evidence_ids", [])[:3]})
    evs = session.execute(select(Event).where(Event.project_id.in_(neighbour_ids), Event.status != "rejected")).scalars()
    for e in evs:
        for code in e.risk_codes or []:
            d = out[str(code)]
            d["projects"].add(e.project_id)
            if len(d["events"]) < 5:
                d["events"].append({"event_id": str(e.id), "project_id": str(e.project_id), "title": e.title,
                                    "cause": (e.cause or "")[:300], "quote": (e.quote or "")[:300],
                                    "evidence_ids": [str(x) for x in (e.evidence_ids or [])[:3]]})
    return {k: {"k": len(v["projects"]), "project_ids": [str(x) for x in v["projects"]], "events": v["events"]}
            for k, v in out.items()}


def build_flags(session: Session, features: dict[str, Any], text: str, neighbours: list[dict[str, Any]],
                ranges: dict[str, dict[str, Any]], assessment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = risk_names(session)
    flags: list[dict[str, Any]] = []

    def add(code: str, title: str, risk_codes: list[str], severity: str, axis: str, why: str, **extra):
        flags.append({"code": code, "title": title, "risk_codes": risk_codes, "severity": severity, "axis": axis,
                      "why": why, "risk_names": {c: names.get(c) for c in risk_codes}, **extra})

    # 1. neighbours' history
    nb_ids = [n["case"].project_id for n in neighbours]
    n_nb = len(nb_ids)
    hist = neighbour_history(session, nb_ids, [n["case"] for n in neighbours])
    for code, h in sorted(hist.items(), key=lambda kv: -kv[1]["k"]):
        share = h["k"] / n_nb if n_nb else 0
        if h["k"] >= 2 and share >= 0.25:
            sev = "wysoka" if share >= 0.5 else "średnia"
            add(f"N-{code}", f"{names.get(code, code)}: u {h['k']} z {n_nb} podobnych inwestycji",
                [code], sev, "realizacja",
                f"U {h['k']} z {n_nb} najbliższych sąsiadów odnotowano zdarzenie z kategorią {code} "
                f"({share:.0%}); przykłady poniżej z cytatami ze źródeł.",
                n=n_nb, k=h["k"], case_ids=h["project_ids"], examples=h["events"],
                formula="Udział = liczba podobnych inwestycji, w których wystąpiło co najmniej jedno zdarzenie tej kategorii, podzielona przez liczbę podobnych inwestycji. Flaga pojawia się, gdy dotyczy to co najmniej 2 inwestycji i co najmniej co czwartej.")

    # 2. ranges
    def rng(name):
        return ranges.get(name) or {}

    pl = rng("p_late")
    if (pl.get("estimate") or 0) >= 0.4:
        add("R-LATE", f"Wysokie prawdopodobieństwo opóźnienia: {pl['estimate']:.0%}", ["R06"],
            "wysoka" if pl["estimate"] >= 0.55 else "średnia", "realizacja",
            f"Wśród podobnych zakończonych umów {pl.get('k')} z {pl.get('n')} nie wykonano w pierwotnym terminie "
            f"(poziom: {LEVEL_PL.get(pl.get('fallback_level'), pl.get('fallback_level'))}; 95% CI {_pct(pl.get('ci_low'))}–{_pct(pl.get('ci_high'))}).",
            n=pl.get("n"), k=pl.get("k"), case_ids=pl.get("case_ids", [])[:50], formula=pl.get("formula"))
    pc = rng("p_change")
    if (pc.get("estimate") or 0) >= 0.5:
        add("R-CHANGE", f"Zmiana umowy prawdopodobna: {pc['estimate']:.0%}", ["R07"], "średnia", "realizacja",
            f"{pc.get('k')} z {pc.get('n')} podobnych umów zmieniano (art. 455 Pzp).", n=pc.get("n"), k=pc.get("k"),
            case_ids=pc.get("case_ids", [])[:50], formula=pc.get("formula"))
    pr = rng("paid_ratio")
    if (pr.get("p80") or 0) > 1.05:
        add("R-OVERRUN", f"Ryzyko przekroczenia wartości umowy (P80 wypłaty = {pr['p80']:.2f} × wartość umowy)",
            ["R07", "R13"], "średnia", "realizacja",
            f"W 20% podobnych umów wypłata przekroczyła wartość umowy o ponad {(pr['p80'] - 1):.0%} (n={pr.get('n')}).",
            n=pr.get("n"), case_ids=pr.get("case_ids", [])[:50], formula=pr.get("formula"))
    c255 = rng("share_cancelled_255_3")
    if (c255.get("estimate") or 0) >= 0.15:
        add("R-255", f"Unieważnienia z powodu ceny powyżej budżetu: {c255['estimate']:.0%} podobnych postępowań",
            ["R13"], "wysoka" if c255["estimate"] >= 0.3 else "średnia", "postępowanie",
            f"{c255.get('k')} z {c255.get('n')} podobnych postępowań unieważniono na podstawie art. 255 pkt 3 Pzp.",
            n=c255.get("n"), k=c255.get("k"), case_ids=c255.get("case_ids", [])[:50], formula=c255.get("formula"))

    # 3. assessment
    for a in assessment:
        pct = a.get("percentile")
        if pct is None:
            continue
        if a.get("metric") == "budget_percentile" and pct <= 0.25:
            add("A-BUDGET", f"Budżet niski na tle sąsiadów (percentyl {pct:.0%})", ["R13", "R08"], "średnia",
                "przygotowanie", f"Tylko {pct:.0%} umów podobnych inwestycji miało wartość ≤ budżetowi ({a.get('basis')}).",
                n=a.get("n"), case_ids=a.get("case_ids", [])[:50], formula=a.get("formula"))
        if a.get("metric") == "schedule_percentile" and pct <= 0.25:
            add("A-SCHEDULE", f"Krótki harmonogram na tle sąsiadów (percentyl {pct:.0%})", ["R06"], "średnia",
                "przygotowanie", f"Tylko {pct:.0%} podobnych umów miało okres realizacji ≤ planowanemu.",
                n=a.get("n"), case_ids=a.get("case_ids", [])[:50], formula=a.get("formula"))
        if str(a.get("metric", "")).startswith("unit_cost") and pct <= 0.15:
            add("A-UNIT", f"Niski koszt jednostkowy ({a.get('title')}, percentyl {pct:.0%})", ["R13", "R01"], "średnia",
                "przygotowanie", "Koszt na jednostkę skali jest niższy niż w 85% podobnych umów. Sprawdź kompletność zakresu i budżet.",
                n=a.get("n"), case_ids=a.get("case_ids", [])[:50], formula=a.get("formula"))

    # 4. description
    value, months = _fv(features, "value"), _fv(features, "duration_months")
    if isinstance(value, int | float) and isinstance(months, int | float) and value >= 1_000_000 and months <= 3:
        add("H1", "Krótki termin przy dużej wartości", ["R06"], "średnia", "przygotowanie",
            f"Wartość {value:,.0f} zł przy okresie {months:g} mies.".replace(",", " "))
    start = _fv(features, "start_date")
    if start and isinstance(months, int | float):
        try:
            d0 = dt.date.fromisoformat(str(start)[:10])
            m = (d0.month - 1 + int(round(months))) % 12 + 1
            if m in (12, 1, 2):
                add("H2", "Planowany koniec robót w okresie zimowym", ["R06"], "niska", "przygotowanie",
                    f"Start {d0:%m.%Y} + {months:g} mies. → koniec w miesiącu {m}; roboty ziemne zimą to częsta przyczyna zmian terminu.")
        except ValueError:
            pass
    cues = features.get("cues") or {}
    for key, (codes, title, sev) in CUE_RISKS.items():
        cv = cues.get(key)
        if cv:
            add(f"D-{key}", title, codes, sev, "przygotowanie", "Opis inwestycji wskazuje ten czynnik.",
                quote=(cv.get("quote") if isinstance(cv, dict) else None), source="opis")
    for key, cv in cues.items():
        if key.startswith("gap_") and isinstance(cv, dict) and cv.get("quote"):
            codes = _signal_codes(cv["quote"], session) or ["R01"]
            add(f"D-{key}", "Opis wskazuje brak lub niepewność", codes[:3], "średnia", "przygotowanie",
                "Zdanie z opisu wskazuje brak lub niepewność. Wyjaśnij to przed ogłoszeniem przetargu.", quote=cv["quote"],
                source="opis")
    if (_fv(features, "vat_basis") or "unknown") == "unknown" and value:
        add("Q-VAT", "Nie wiadomo, czy kwota jest netto czy brutto", [], "niska", "dane",
            "Porównujemy tylko kwoty tego samego rodzaju, więc ocena budżetu czeka na tę informację.")

    # 5. checklist (water network)
    sub = _fv(features, "subsector_main")
    cl_codes = {r["no"]: r for r in krows("checklist_rcodes", session)}
    covered = {"land": [6], "permits": [5, 8], "environment": [8], "operator": [5], "collisions": [7]}
    have = {n for k, ns in covered.items() if cues.get(k) for n in ns}
    if _fv(features, "length_km"):
        have.add(4)
    missing_items = []
    for item in krows("checklist", session):
        no = int(item.get("no"))
        meta = cl_codes.get(no) or {}
        if sub and meta.get("applies_to") and sub not in meta["applies_to"]:
            continue
        if no not in have and no in (4, 5, 6, 7, 8, 9):
            missing_items.append({"no": no, "item": item.get("item"), "risk_codes": meta.get("risk_codes", []),
                                  "guide_sections": item.get("guide_sections")})
    if missing_items:
        codes = sorted({c for m in missing_items for c in m["risk_codes"]})
        add("C-CHECK", f"Brak informacji dla {len(missing_items)} punktów listy kontrolnej eksperta", codes, "niska",
            "dane", "Opis nie zawiera informacji z listy kontrolnej eksperta. Uzupełnij je przed analizą ryzyka.",
            items=missing_items)
    flags.sort(key=lambda f: (SEV_ORDER.get(f["severity"], 3), f["code"]))
    return flags


def build_actions(session: Session, flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clause + lessons per flagged risk code (dane źródłowe: expert knowledge / NIK)."""
    codes: dict[str, list[str]] = defaultdict(list)
    for f in flags:
        for c in f["risk_codes"]:
            codes[c].append(f["code"])
    names = risk_names(session)
    out = []
    for code in sorted(codes):
        clauses = session.execute(select(Clause).where(Clause.risk_code == code, Clause.status != "rejected")
                                  .order_by(Clause.code)).scalars().all()
        lessons = session.execute(select(Lesson).where(Lesson.risk_codes.contains([code]), Lesson.status != "rejected")
                                  .limit(3)).scalars().all()
        exemplary = session.execute(select(Event).where(Event.risk_codes.contains([code]), Event.exemplary.is_(True))
                                    .limit(2)).scalars().all()
        out.append({
            "risk_code": code, "risk_name": names.get(code), "flags": codes[code],
            "clauses": [{"id": str(c.id), "code": c.code, "title": c.title, "text": c.text, "legal_basis": c.legal_basis,
                         "trigger": c.trigger, "status": c.status} for c in clauses],
            "lessons": [{"id": str(x.id), "title": x.title, "recommendation": x.recommendation, "source_kind": x.source_kind,
                         "evidence_ids": [str(e) for e in (x.evidence_ids or [])[:3]]} for x in lessons],
            "examples": [{"id": str(e.id), "title": e.title, "cause": e.cause, "mitigation": e.mitigation,
                          "mitigation_effect": e.mitigation_effect} for e in exemplary],
        })
    return out


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()
