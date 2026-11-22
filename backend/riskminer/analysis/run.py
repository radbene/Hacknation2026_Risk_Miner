"""Path B orchestration: features → neighbours (explained) → ranges → assessment → flags → actions → records.

Every block is stored as an AnalysisItem with its label ([Dane źródłowe] / [Obliczenia] / [Wniosek modelu]),
so the expert can accept/reject items and exclude neighbours (→ recompute). Deterministic for the same DB state.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from riskminer.analysis.assess import assess
from riskminer.analysis.caseset import load_wodkan_cases
from riskminer.analysis.flags import build_actions, build_flags
from riskminer.analysis.knowledge import thresholds
from riskminer.analysis.ranges import change_basis_distribution, compute_ranges
from riskminer.analysis.similarity import find_neighbours
from riskminer.models import Analysis, AnalysisItem, Document

RANGE_TITLES = {
    "p_late": "Prawdopodobieństwo opóźnienia", "delay_days": "Opóźnienie [dni]",
    "delay_days_if_late": "Opóźnienie wśród opóźnionych [dni]", "paid_ratio": "Wypłata / wartość umowy",
    "p_change": "Prawdopodobieństwo zmiany umowy", "share_cancelled": "Udział unieważnionych postępowań",
    "share_cancelled_255_3": "Unieważnienia – art. 255 pkt 3 Pzp", "offer_vs_budget": "Cena oferty / kwota na sfinansowanie",
    "offer_vs_estimate": "Cena oferty / wartość szacunkowa × 1,23",
}


def _jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, list | tuple | set):
        return [_jsonable(v) for v in x]
    if isinstance(x, uuid.UUID):
        return str(x)
    if isinstance(x, float):
        return round(x, 6)
    if hasattr(x, "isoformat"):
        return x.isoformat()
    return x


def analysis_text(session: Session, a: Analysis) -> str:
    parts = [a.input_text or ""]
    for d in session.execute(select(Document).where(Document.analysis_id == a.id)).scalars():
        from riskminer.models import Chunk

        parts += [c.text for c in session.execute(select(Chunk).where(Chunk.document_id == d.id).order_by(Chunk.ord)
                                                  .limit(200)).scalars()]
    return "\n".join(p for p in parts if p).strip()


def compute(session: Session, a: Analysis, actor: str = "system") -> Analysis:
    th = thresholds(session)
    k = int((a.params or {}).get("k") or th.get("neighbours_k") or 12)
    min_n = int((a.params or {}).get("min_n") or th.get("min_n_for_quantiles") or 8)
    text = analysis_text(session, a)
    features = a.features or {}
    # the base is wod-kan: auto-tier cases whose title names another main object (sports hall, school …) only
    # inherited a sewer subsector from their description – keep them out of neighbours and reference pools
    cases = load_wodkan_cases(session)
    if a.project_id:  # analysing an existing project: never compare it with itself
        cases = [c for c in cases if c.project_id != a.project_id]
    excl = {str(x) for x in a.excluded_project_ids or []}
    nb = find_neighbours(cases, features, text, session, k=k, exclude=excl,
                         weight_override=(a.params or {}).get("weights"), pool="completed")
    similar = find_neighbours(cases, features, text, session, k=max(30, 3 * k), exclude=excl, pool="all")
    neighbours = nb["neighbours"]
    nb_cases = [n["case"] for n in neighbours]
    sub = features.get("subsector_main")
    sub = sub.get("value") if isinstance(sub, dict) else sub
    ranges_list = compute_ranges(nb_cases, cases, sub, min_n=min_n, similar_pool=[n["case"] for n in similar["neighbours"]])
    ranges = {r["metric"]: r for r in ranges_list}
    assessment = assess(features, nb_cases, ranges, min_n=min_n, all_cases=cases)
    flags = build_flags(session, features, text, neighbours, ranges, assessment)
    actions = build_actions(session, flags)

    # keep expert decisions on items that survive (same kind + key) – rebuild the rest
    old = {(i.kind, (i.payload or {}).get("key")): i for i in
           session.execute(select(AnalysisItem).where(AnalysisItem.analysis_id == a.id)).scalars()}
    session.execute(delete(AnalysisItem).where(AnalysisItem.analysis_id == a.id, AnalysisItem.status == "proposed",
                                               AnalysisItem.excluded.is_(False)))
    ordn = 0

    def item(kind: str, key: str, label: str, title: str, payload: dict, ref=None, risk_codes=None,
             method="rule", excluded=False):
        nonlocal ordn
        ordn += 1
        prev = old.get((kind, key))
        iid = uuid.uuid5(a.id, f"{kind}:{key}")
        payload = _jsonable({**payload, "key": key})
        if prev is not None and (prev.status != "proposed" or prev.excluded):
            prev.ord = ordn
            if prev.payload != payload:
                prev.proposal = {"payload": payload}
            return
        session.merge(AnalysisItem(id=iid, analysis_id=a.id, kind=kind, ord=ordn, label=label, title=title,
                                   payload=payload, ref_project_id=ref, risk_codes=risk_codes or [], excluded=excluded,
                                   status="proposed", method=method, confidence=None, evidence_ids=[]))

    for n in neighbours + nb["excluded"]:
        c = n["case"]
        outcome = {"delay_days": c.delay_days, "late": c.late, "paid_ratio": c.paid_ratio, "n_changes": c.n_changes,
                   "cancelled": c.cancelled, "value_gross": c.value_gross, "planned_days": c.planned_days,
                   "change_codes": c.change_codes, "evidence_ids": c.evidence_ids[:5]}
        item("neighbour", str(c.project_id), "obliczenia", f"{c.code}: {c.title[:160]}",
             {"project_id": c.project_id, "project_code": c.code, "title": c.title, "score": n["score"],
              "breakdown": n["breakdown"], "shared_terms": n["shared_terms"], "differences": n["differences"],
              "missing": n["missing"], "tier": c.tier, "outcome": outcome, "subsector_main": c.subsector_main},
             ref=c.project_id, excluded=str(c.project_id) in excl)
    for r in ranges_list:
        item("range", r["metric"], "obliczenia", RANGE_TITLES.get(r["metric"], r["metric"]), r)
    for x in assessment:
        item("assessment", x["metric"], "obliczenia", x.get("title") or x["metric"], x)
    for f in flags:
        item("flag", f["code"], "obliczenia", f["title"], f, risk_codes=f["risk_codes"])
    for ac in actions:
        item("action", ac["risk_code"], "dane_zrodlowe", f"{ac['risk_code']} {ac.get('risk_name') or ''}".strip(), ac,
             risk_codes=[ac["risk_code"]], method="knowledge")
    summary = _summary(nb, neighbours, ranges, assessment, flags, cases)
    summary["change_basis"] = change_basis_distribution(nb_cases)
    llm = _llm_summary(features, summary, flags) if (a.params or {}).get("use_llm", True) else None
    if llm:
        item("action", "_llm_summary", "wniosek_modelu", "Podsumowanie (Wniosek modelu)", llm, method="llm")
        summary["llm_label"] = llm.get("model_label")
    a.summary = _jsonable(summary)
    a.version = (a.version or 0) + 1
    session.flush()
    return a


def _summary(nb, neighbours, ranges, assessment, flags, cases) -> dict[str, Any]:
    def r(name, *keys):
        x = ranges.get(name) or {}
        return {k: x.get(k) for k in ("n", "fallback_level", *keys)}

    tiers = {}
    for c in cases:
        tiers[c.tier] = tiers.get(c.tier, 0) + 1
    return {
        "n_cases": len(cases), "cases_by_tier": tiers, "n_pool": nb["n_pool"], "n_neighbours": len(neighbours),
        "weights": nb["weights"], "weights_source": nb["weights_source"],
        "p_late": r("p_late", "k", "raw", "estimate", "ci_low", "ci_high"), "delay_days": r("delay_days", "p50", "p80", "p95"),
        "delay_days_if_late": r("delay_days_if_late", "p50", "p80", "p95"),
        "paid_ratio": r("paid_ratio", "p50", "p80", "p95"), "p_change": r("p_change", "estimate"),
        "share_cancelled_255_3": r("share_cancelled_255_3", "estimate"),
        "n_flags": len(flags), "flags_high": sum(1 for f in flags if f["severity"] == "wysoka"),
        "risk_codes": sorted({c for f in flags for c in f["risk_codes"]}),
        "budget": next(({k: a.get(k) for k in ("percentile", "position", "value", "basis", "message", "reserve_p80")}
                        for a in assessment if a.get("metric") == "budget_percentile"), None),
        "schedule": next(({k: a.get(k) for k in ("percentile", "position", "value", "value_days", "message", "compared_to", "n")}
                          for a in assessment if a.get("metric") == "schedule_percentile"), None),
        "unit_costs": [{k: a.get(k) for k in ("metric", "title", "value", "percentile", "position", "n", "pool", "message")}
                       for a in assessment if a.get("metric") in ("cost_per_km", "cost_per_rlm")],
    }


def _llm_summary(features: dict, summary: dict, flags: list[dict]) -> dict | None:
    """Optional narrative (task 'recommendations'); rules-only fallback = no item."""
    from pydantic import BaseModel

    from riskminer.llm import complete

    class Out(BaseModel):
        summary: str
        top_actions: list[str]

    facts = {"cechy": {k: (v.get("value") if isinstance(v, dict) else v) for k, v in features.items() if k not in ("cues", "extra")},
             "podsumowanie": {k: summary.get(k) for k in ("n_neighbours", "p_late", "delay_days", "paid_ratio", "p_change",
                                                          "share_cancelled_255_3", "budget", "schedule", "unit_costs",
                                                          "delay_days_if_late")},
             "flagi": [{"tytul": f["title"], "kategorie": f["risk_codes"], "waga": f["severity"]} for f in flags[:12]]}
    try:
        res = complete("recommendations", [{"role": "user", "content": "Dane analizy (JSON):\n" + str(_jsonable(facts))}], Out,
                       system="Jesteś ekspertem ds. inwestycji wodno-kanalizacyjnych. Na podstawie WYŁĄCZNIE podanych liczb i flag "
                              "napisz po polsku 3–5 zdań podsumowania ryzyka i do 5 konkretnych działań zapobiegawczych. "
                              "Nie wymyślaj liczb. Odsetki podawaj w pełnych procentach, kwoty zaokrąglone (np. 2,2 mln zł). "
                              "budget.reserve_p80.amount to KWOTA REZERWY ponad budżet, a total to budżet razem z rezerwą. "
                              "percentile budżetu opisuje tylko wielkość inwestycji na tle podobnych, nie jej realność – "
                              "o realności kosztu mówią unit_costs (koszt na km / RLM).", prompt_version="summary-v2", untrusted=False)
    except Exception:  # noqa: BLE001
        return None
    if res.data is None:
        return None
    return {"summary": res.data.summary, "top_actions": res.data.top_actions, "model_label": res.label}


def create(session: Session, *, title: str, text: str | None, features: dict | None, params: dict | None = None,
           document_ids: list[uuid.UUID] | None = None, project_id: uuid.UUID | None = None, actor: str = "system",
           use_llm: bool = True) -> Analysis:
    from riskminer.analysis.features import extract_features

    a = Analysis(id=uuid.uuid4(), title=title, input_text=text, features={}, params={**(params or {}), "use_llm": use_llm},
                 summary={},
                 excluded_project_ids=[], created_by=actor, project_id=project_id, version=0, status="proposed",
                 method="rule", evidence_ids=[])
    session.add(a)
    session.flush()
    for did in document_ids or []:
        d = session.get(Document, did)
        if d is not None and d.analysis_id is None and d.project_id is None:
            d.analysis_id = a.id
    session.flush()
    if features:
        a.features = _jsonable(features)
    else:
        fx = extract_features(analysis_text(session, a), session, use_llm=use_llm)
        a.features = fx.features.model_dump(mode="json", exclude_none=True)
        a.params = {**a.params, "missing": fx.missing, "questions": fx.questions, "features_model": fx.model_label}
        a.llm_profile = fx.model_label
    compute(session, a, actor)
    return a
