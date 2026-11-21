"""Explained neighbours: editable weights × structured similarity + TF-IDF (+ embeddings, P1).

score = Σ_c w_c · s_c / Σ_c w_c over the components the NEW investment has. A component the neighbour lacks
counts as 0.5 (neutral) and is listed in `missing`. Weights come from the knowledge table `similarity_weights`
(DB version first, YAML fallback); `params.weights` overrides per analysis. Fully deterministic: ties are broken
by project code.
"""

from __future__ import annotations

import math
import re
import threading
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session

from riskminer.analysis.caseset import Case
from riskminer.analysis.knowledge import load_table

DEFAULT_WEIGHTS = {"subsector_main": 0.25, "subsector_extra": 0.05, "work_type": 0.10, "formula": 0.10,
                   "value": 0.15, "length_km": 0.10, "voivodeship": 0.05, "tfidf": 0.10, "embedding": 0.10}
LABELS = {"subsector_main": "podsektor główny", "subsector_extra": "podsektory dodatkowe", "work_type": "rodzaj robót",
          "formula": "formuła realizacji", "value": "skala (wartość)", "length_km": "długość sieci",
          "voivodeship": "województwo", "tfidf": "podobieństwo słów w opisie", "embedding": "podobieństwo znaczenia opisu"}
VAT = 1.23
STOP = set("oraz wraz dla przez przy będzie który która które jest się na w z do od i a o u po pod nad ul gmina gminy "
           "gminie miejscowości miejscowość budowa budowy zadanie zadania ramach realizacja realizacji".split())
_SIMILAR_WORK = {"przebudowa", "modernizacja", "rozbudowa", "remont", "renowacja"}


def weights(session: Session | None, override: dict[str, float] | None = None) -> tuple[dict[str, float], str]:
    t = load_table("similarity_weights", session)
    w = {r["component"]: float(r["weight"]) for r in t["rows"] if "component" in r} or dict(DEFAULT_WEIGHTS)
    src = t["source"] if t["rows"] else "default"
    if override:
        w.update({k: float(v) for k, v in override.items() if k in DEFAULT_WEIGHTS})
        src += "+params"
    return w, src


# ---------------------------------------------------------------- text


def stem(tok: str) -> str:
    return tok[:6]


_TOKEN = re.compile(r"[a-ząćęłńóśźż]{3,}")


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in STOP]


def analyzer(text: str) -> list[str]:
    return [stem(t) for t in tokens(text)]


class TextIndex:
    """TF-IDF over case texts (title + description), stem-level so Polish inflection matches."""

    def __init__(self, cases: list[Case]):
        self.codes = [c.code for c in cases]
        self.vec = TfidfVectorizer(analyzer=analyzer, min_df=2, sublinear_tf=True, dtype=np.float32)
        self.m = self.vec.fit_transform([c.text for c in cases])

    def scores(self, text: str) -> np.ndarray:
        q = self.vec.transform([text])
        return (self.m @ q.T).toarray().ravel()


_idx_lock = threading.Lock()
_idx: dict[str, Any] = {"key": None, "index": None}


def text_index(cases: list[Case]) -> TextIndex:
    key = (id(cases), len(cases))
    with _idx_lock:
        if _idx["key"] == key:
            return _idx["index"]
    ix = TextIndex(cases)
    with _idx_lock:
        _idx.update(key=key, index=ix)
    return ix


def shared_terms(new_text: str, case_text: str, limit: int = 8) -> list[str]:
    a = {}
    for t in tokens(new_text):
        a.setdefault(stem(t), t)
    b = {stem(t) for t in tokens(case_text)}
    return [a[s] for s in a if s in b][:limit]


# ---------------------------------------------------------------- structured components


def _log_sim(a: float, b: float, scale: float) -> float:
    """1 at equal size, ~0.37 at one `scale` (in log10) apart."""
    return math.exp(-abs(math.log10(a) - math.log10(b)) / scale)


@dataclass
class Query:
    text: str
    subsector_main: str | None
    subsectors: set[str]
    work_type: str | None
    formula: str | None
    value_gross: float | None  # comparable to contract values (gross); None if VAT basis unknown → approx
    value_note: str | None
    length_km: float | None
    voivodeship: str | None


def make_query(features: dict[str, Any], text: str) -> Query:
    def v(name):
        x = features.get(name)
        return x.get("value") if isinstance(x, dict) else x

    value, vat = v("value"), v("vat_basis") or "unknown"
    vg, note = None, None
    if isinstance(value, int | float) and value > 0:
        if vat == "gross":
            vg = float(value)
        elif vat == "net":
            vg, note = float(value) * VAT, "kwota netto przeliczona na brutto (VAT 23%) wyłącznie do porównania skali"
        else:
            vg, note = float(value), "VAT nieznany – porównanie skali przybliżone (różnica netto/brutto ≤ 23%)"
    extra = v("subsector_extra") or []
    main = v("subsector_main")
    km = v("length_km")
    return Query(text=text or "", subsector_main=main, subsectors={x for x in [main, *extra] if x},
                 work_type=v("work_type"), formula=v("formula"), value_gross=vg, value_note=note,
                 length_km=float(km) if isinstance(km, int | float) and km > 0 else None, voivodeship=v("voivodeship"))


def components(q: Query, c: Case, tfidf: float, emb: float | None) -> dict[str, tuple[float | None, str]]:
    """component → (similarity in [0,1] or None when the neighbour lacks it, detail)."""
    out: dict[str, tuple[float | None, str]] = {}
    if q.subsector_main:
        if not c.subsector_main:
            out["subsector_main"] = (None, "brak podsektora u sąsiada")
        elif c.subsector_main == q.subsector_main:
            out["subsector_main"] = (1.0, c.subsector_main)
        elif q.subsector_main in c.subsector_extra or c.subsector_main in q.subsectors:
            out["subsector_main"] = (0.5, f"{c.subsector_main} (częściowo wspólny)")
        else:
            out["subsector_main"] = (0.0, f"{c.subsector_main} ≠ {q.subsector_main}")
    if len(q.subsectors) > 1:
        cs = {x for x in [c.subsector_main, *c.subsector_extra] if x}
        j = len(q.subsectors & cs) / len(q.subsectors | cs) if cs else None
        out["subsector_extra"] = (j, ", ".join(sorted(q.subsectors & cs)) or "brak wspólnych")
    if q.work_type:
        if not c.work_type:
            out["work_type"] = (None, "brak rodzaju robót u sąsiada")
        else:
            s = 1.0 if c.work_type == q.work_type else (0.5 if {c.work_type, q.work_type} <= _SIMILAR_WORK else 0.0)
            out["work_type"] = (s, c.work_type)
    if q.formula:
        cf = c.formula or "tradycyjna"  # BZP: no D&B wording → traditional (assumption, shown in detail)
        s = 1.0 if cf == q.formula else 0.0
        out["formula"] = (s, cf + ("" if c.formula else " (przyjęto: brak wzmianki o „zaprojektuj i wybuduj”)"))
    if q.value_gross:
        cv = c.value_gross or c.budget_gross or (c.est_value_net * VAT if c.est_value_net else None)
        if cv and cv > 0:
            out["value"] = (_log_sim(q.value_gross, cv, 0.5), f"{cv:,.0f} zł brutto vs {q.value_gross:,.0f} zł".replace(",", " "))
        else:
            out["value"] = (None, "brak wartości umowy")
    if q.length_km:
        if c.length_km:
            out["length_km"] = (_log_sim(q.length_km, c.length_km, 0.4), f"{c.length_km:g} km vs {q.length_km:g} km")
        else:
            out["length_km"] = (None, "brak długości sieci w danych sąsiada")
    if q.voivodeship:
        if c.voivodeship:
            out["voivodeship"] = (1.0 if c.voivodeship == q.voivodeship else 0.0, c.voivodeship)
        else:
            out["voivodeship"] = (None, "brak województwa")
    if q.text.strip():
        lvl = "duża" if tfidf >= 0.3 else "średnia" if tfidf >= 0.12 else "mała"
        out["tfidf"] = (float(min(1.0, tfidf)), f"{lvl} zbieżność słów (rzadkie wspólne słowa liczą się bardziej niż częste)")
    if emb is not None:
        out["embedding"] = (float(emb), "zbieżność znaczenia opisów")
    return out


def score_case(q: Query, c: Case, w: dict[str, float], tfidf: float, emb: float | None = None) -> dict[str, Any]:
    comps = components(q, c, tfidf, emb)
    total_w = sum(w.get(k, 0.0) for k in comps)
    breakdown, missing, score = [], [], 0.0
    for k, (s, detail) in comps.items():
        wk = w.get(k, 0.0)
        eff = 0.5 if s is None else s
        if s is None:
            missing.append(LABELS[k])
        contrib = wk * eff / total_w if total_w else 0.0
        score += contrib
        breakdown.append({"component": k, "label": LABELS[k], "similarity": None if s is None else round(s, 3),
                          "weight": round(wk, 3), "contribution": round(contrib, 4), "detail": detail})
    differences = [f"{b['label']}: {b['detail']}" for b in breakdown
                   if b["similarity"] is not None and b["similarity"] < 0.5 and b["component"] not in ("tfidf", "embedding")]
    return {"score": round(score, 4), "breakdown": breakdown, "missing": missing, "differences": differences}


def find_neighbours(cases: list[Case], features: dict[str, Any], text: str, session: Session | None = None,
                    k: int = 12, exclude: set[str] | None = None, weight_override: dict[str, float] | None = None,
                    pool: str = "completed", embeddings: dict[str, float] | None = None) -> dict[str, Any]:
    """Top-k cases. pool = completed (outcomes for ranges) | all (incl. cancelled procedures)."""
    w, wsrc = weights(session, weight_override)
    if not embeddings:
        w = {**w, "embedding": 0.0}
    q = make_query(features, text)
    ix = text_index(cases)
    tf = ix.scores(q.text) if q.text.strip() else np.zeros(len(cases))
    excl = exclude or set()
    scored = []
    for i, c in enumerate(cases):
        if pool == "completed" and not c.completed:
            continue
        s = score_case(q, c, w, float(tf[i]), (embeddings or {}).get(c.code))
        scored.append((s["score"], c.code, i, s))
    scored.sort(key=lambda t: (-t[0], t[1]))
    out, excluded = [], []
    for _sc, _code, i, s in scored:
        c = cases[i]
        item = {"case": c, **s, "shared_terms": shared_terms(q.text, c.text), "tfidf": round(float(tf[i]), 4)}
        if str(c.project_id) in excl:
            excluded.append(item)
            continue
        if len(out) < k:
            out.append(item)
        if len(out) >= k and len(excluded) >= len(excl):
            break
    return {"neighbours": out, "excluded": excluded, "weights": w, "weights_source": wsrc,
            "query": q, "n_pool": len(scored)}
