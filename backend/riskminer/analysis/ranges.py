"""Deviation ranges over the NAMED neighbours, with shrinkage toward priors (no Monte Carlo).

Adapted from prep refclass_build.cell() / refclass_forecast._shrink():
- proportions (P(late), P(change), share cancelled): k/n among neighbours, shrunk toward the parent level
  (subsector → wod-kan → all works): p = (k + m·p_parent)/(n + m), m = `min_n_for_quantiles`; Wilson 95% CI on k/n;
- quantiles (delay days, paid/value): empirical over neighbours when n ≥ min_n, otherwise the first parent level
  that has n ≥ min_n (reported as `fallback_level`).
Every metric carries n, period, case ids and the formula.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from riskminer.analysis.caseset import Case

LEVELS = ["neighbours", "subsector", "wodkan", "works"]
LEVEL_PL = {"neighbours": "najbardziej podobne inwestycje", "subsector": "wszystkie inwestycje z tego podsektora",
            "wodkan": "wszystkie inwestycje wodno-kanalizacyjne", "works": "wszystkie roboty w bazie"}
Z95 = 1.959963984540054


def wilson(k: int, n: int, z: float = Z95) -> tuple[float | None, float | None]:
    """Wilson score interval for k successes in n trials."""
    if n <= 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)


def shrink(k: int, n: int, parent: float | None, m: float) -> float | None:
    """_shrink(): weighted mean of the cell rate and the parent rate, m virtual cases."""
    if parent is None:
        return k / n if n else None
    return (k + m * parent) / (n + m)


def quantile(vals: list[float], p: float) -> float:
    return float(np.quantile(np.asarray(vals, dtype=float), p, method="linear"))


def _period(cases: list[Case]) -> str | None:
    ys = sorted(c.year for c in cases if c.year)
    return f"{ys[0]}–{ys[-1]}" if ys else None


class Levels:
    """Case sets per fallback level for one analysis (neighbours are named; parents are pools)."""

    def __init__(self, neighbours: list[Case], all_cases: list[Case], subsector: str | None):
        self.sets: dict[str, list[Case]] = {
            "neighbours": neighbours,
            "subsector": [c for c in all_cases if subsector and c.subsector_main == subsector],
            "wodkan": [c for c in all_cases if c.subsector_main],
            "works": all_cases,
        }

    def chain(self) -> list[tuple[str, list[Case]]]:
        return [(lv, self.sets[lv]) for lv in LEVELS if self.sets[lv]]


def proportion(levels: Levels, name: str, pred: Callable[[Case], bool | None], min_n: int, formula: str,
               pool_filter: Callable[[Case], bool] | None = None) -> dict[str, Any]:
    chain = [(lv, [c for c in cs if (pool_filter is None or pool_filter(c)) and pred(c) is not None])
             for lv, cs in levels.chain()]
    rates = {lv: (sum(bool(pred(c)) for c in cs), len(cs)) for lv, cs in chain}
    # parent rate for a level = shrunk rate of the next level up (recursively from the top)
    shrunk: dict[str, float | None] = {}
    parent = None
    for lv, _ in reversed(chain):
        k, n = rates[lv]
        shrunk[lv] = shrink(k, n, parent, min_n) if n else parent
        parent = shrunk[lv]
    lv0, cs0 = chain[0]
    k, n = rates[lv0]
    used = lv0 if n >= min_n else next((lv for lv, _ in chain if rates[lv][1] >= min_n), lv0)
    lo, hi = wilson(k, n)
    parent_lv = next((lv for lv, _ in chain[1:]), None)
    return {
        "metric": name, "n": n, "k": k, "raw": round(k / n, 4) if n else None,
        "estimate": round(shrunk[lv0], 4) if shrunk.get(lv0) is not None else None,
        "ci_low": lo, "ci_high": hi, "fallback_level": used, "period": _period(cs0),
        "case_ids": [str(c.project_id) for c in cs0],
        "parent": {"level": parent_lv, "k": rates[parent_lv][0], "n": rates[parent_lv][1]} if parent_lv else None,
        "formula": (f"{formula} Wygładzenie małej próbki: wynik = (k + m·p) / (n + m), gdzie p – ten sam odsetek w "
                    f"szerszej grupie ({LEVEL_PL.get(parent_lv, parent_lv) if parent_lv else 'brak'}), m = {min_n} – tyle "
                    "„przypadków” z szerszej grupy dokładamy, żeby kilka nietypowych inwestycji nie dawało skrajnego wyniku. "
                    "Przedział 95% (metoda Wilsona): zakres, w którym z 95-procentową pewnością leży prawdziwy odsetek "
                    "– im mniej przypadków, tym szerszy."),
    }


def quantiles(levels: Levels, name: str, value: Callable[[Case], float | None], min_n: int, formula: str,
              ps: tuple[float, ...] = (0.5, 0.8, 0.95)) -> dict[str, Any]:
    chain = [(lv, [(c, value(c)) for c in cs]) for lv, cs in levels.chain()]
    chain = [(lv, [(c, v) for c, v in xs if v is not None and math.isfinite(v)]) for lv, xs in chain]
    lv_used, xs_used = next(((lv, xs) for lv, xs in chain if len(xs) >= min_n), chain[-1] if chain else ("works", []))
    nb = chain[0][1] if chain else []
    out: dict[str, Any] = {"metric": name, "n": len(xs_used), "fallback_level": lv_used, "period": _period([c for c, _ in xs_used]),
                           "n_neighbours_with_data": len(nb),
                           "case_ids": [str(c.project_id) for c, _ in (xs_used if lv_used == "neighbours" else nb)],
                           "formula": formula + " P50 – wartość środkowa (połowa przypadków ma mniej, połowa więcej); "
                                      "P80 – 8 na 10 przypadków ma nie więcej; P95 – 19 na 20 przypadków ma nie więcej."
                                      + (f" Podobne inwestycje mają tylko {len(nb)} takich wartości (mniej niż {min_n}), więc "
                                         f"liczymy na grupie: {LEVEL_PL.get(lv_used, lv_used)} (n = {len(xs_used)})."
                                         if lv_used != "neighbours" else "")}
    vals = [v for _, v in xs_used]
    for p in ps:
        out[f"p{int(p * 100)}"] = round(quantile(vals, p), 4) if vals else None
    if nb:
        out["neighbour_values"] = [{"project_id": str(c.project_id), "code": c.code, "value": round(v, 4)} for c, v in nb]
    return out


def compute_ranges(neighbours: list[Case], all_cases: list[Case], subsector: str | None, min_n: int = 8,
                   similar_pool: list[Case] | None = None) -> list[dict[str, Any]]:
    completed = [c for c in all_cases if c.completed]
    lv = Levels(neighbours, completed, subsector)
    out = [
        proportion(lv, "p_late", lambda c: c.late, min_n,
                   "Odsetek opóźnionych = k / n, gdzie n – liczba podobnych umów, dla których zamawiający podał w ogłoszeniu o wykonaniu umowy, czy dotrzymano terminu (pkt 5.3), a k – ile z nich wykonano po pierwotnym terminie."),
        quantiles(lv, "delay_days", lambda c: c.delay_days, min_n,
                  "Opóźnienie w dniach = faktyczna data wykonania (pkt 5.2 ogłoszenia o wykonaniu) minus planowany termin (data zawarcia umowy, pkt 4.1, plus okres realizacji, pkt 4.2); umowy wykonane w terminie liczą się jako 0.",
                  ps=(0.5, 0.8)),
        quantiles(lv, "delay_days_if_late", lambda c: c.delay_days if c.late else None, min_n,
                  "Opóźnienie w dniach liczone tylko dla umów, które wykonano po terminie – pokazuje, jak duże bywa opóźnienie, gdy już wystąpi.", ps=(0.5, 0.8)),
        quantiles(lv, "paid_ratio", lambda c: c.paid_ratio, min_n,
                  "Stosunek wypłaty do umowy = wynagrodzenie faktycznie wypłacone (pkt 5.5) / wartość zawartej umowy (pkt 4.4), obie kwoty brutto, tylko umowy wykonane; 1,10 oznacza wypłatę o 10% wyższą niż w umowie."),
        proportion(lv, "p_change", lambda c: (c.n_changes or 0) > 0 if c.n_changes is not None else None, min_n,
                   "Odsetek zmienianych umów = k / n, gdzie n – liczba podobnych umów z informacją o zmianach, a k – ile z nich zmieniono co najmniej raz (pkt 5.4.1 ogłoszenia o wykonaniu)."),
    ]
    # cancellation is measured on the similar *procedures* (completed + cancelled), not on completed contracts
    pool = similar_pool or neighbours
    lv2 = Levels(pool, all_cases, subsector)
    out.append(proportion(lv2, "share_cancelled", lambda c: c.cancelled, min_n,
                          "Odsetek unieważnionych = k / n, gdzie n – liczba podobnych postępowań (zakończonych umową albo unieważnionych), a k – ile z nich unieważniono."))
    out.append(proportion(lv2, "share_cancelled_255_3", lambda c: c.cancelled_255_3, min_n,
                          "Odsetek unieważnień z powodu ceny = k / n, gdzie n – liczba podobnych postępowań, a k – ile unieważniono na podstawie art. 255 pkt 3 Pzp (najtańsza oferta przewyższała kwotę, którą zamawiający mógł przeznaczyć)."))
    out.append(quantiles(lv, "offer_vs_budget", lambda c: (c.price_won / c.budget_gross) if c.price_won and c.budget_gross else None,
                         min_n, "Cena / budżet = cena wybranej oferty (pkt 6.4, brutto) / kwota, którą zamawiający zamierzał przeznaczyć (brutto); 1,20 oznacza ofertę o 20% droższą niż budżet. Porównujemy tylko kwoty tego samego rodzaju (obie z VAT)."))
    out.append(quantiles(lv, "offer_vs_estimate", lambda c: (c.price_won / (c.est_value_net * 1.23)) if c.price_won and c.est_value_net else None,
                         min_n, "Cena / szacunek = cena wybranej oferty (brutto) / (wartość zamówienia netto z pkt 4.3 × 1,23). Założenie: VAT 23% dla robót budowlanych."))
    return out


def change_basis_distribution(cases: list[Case]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    ids: dict[str, list[str]] = {}
    for c in cases:
        for code in c.change_codes:
            counts[code] = counts.get(code, 0) + 1
            ids.setdefault(code, [])
            if str(c.project_id) not in ids[code]:
                ids[code].append(str(c.project_id))
    total = sum(counts.values())
    return {"n_changes": total, "n_cases": len(cases), "counts": dict(sorted(counts.items())),
            "shares": {k: round(v / total, 3) for k, v in sorted(counts.items())} if total else {},
            "case_ids": ids}
