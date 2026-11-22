"""Budget and schedule assessment against the named neighbours (VAT-aware).

Rules (expert "Porady – Kwoty netto i brutto"): the estimate (wartość zamówienia) is net; the financing amount,
offer prices and contract values are gross. Only like-for-like amounts are compared; a user value with
`vat_basis = unknown` is NEVER compared with neighbour amounts – the assessment asks for the basis instead.
"""

from __future__ import annotations

import bisect
from typing import Any

from riskminer.analysis.caseset import Case
from riskminer.analysis.ranges import quantile

VAT = 1.23


def percentile_rank(x: float, vals: list[float]) -> float:
    """Share of values ≤ x (mid-rank for ties), in [0, 1]."""
    s = sorted(vals)
    lo, hi = bisect.bisect_left(s, x), bisect.bisect_right(s, x)
    return round((lo + hi) / 2 / len(s), 3) if s else 0.0


def comparable_value(value: float | None, vat: str | None, against: str = "gross") -> tuple[float | None, str]:
    """User amount converted to the basis of the comparison. Unknown basis → (None, reason)."""
    if value is None or value <= 0:
        return None, "brak kwoty"
    if vat not in ("net", "gross"):
        return None, "nie porównano: nie wiadomo, czy kwota jest netto czy brutto"
    if vat == against:
        pl = {"net": "netto", "gross": "brutto"}
        return float(value), f"kwota {pl[vat]} porównana z kwotami {pl[against]}"
    if vat == "net" and against == "gross":
        return float(value) * VAT, "kwota netto × 1,23 (ZAŁOŻENIE: VAT 23%) porównana z kwotami brutto"
    return float(value) / VAT, "kwota brutto / 1,23 (ZAŁOŻENIE: VAT 23%) porównana z kwotami netto"


def _q(vals: list[float]) -> dict[str, float | None]:
    return {f"p{p}": round(quantile(vals, p / 100), 2) if vals else None for p in (10, 50, 80, 90)}


def _round_k(x: float, step: float = 10_000) -> float:
    return float(round(x / step) * step)


def _position(pct: float) -> str:
    if pct < 0.1:
        return "niżej niż 9 na 10 podobnych"
    if pct < 0.5:
        return "niżej niż połowa podobnych"
    if pct <= 0.9:
        return "wyżej niż połowa podobnych"
    return "wyżej niż 9 na 10 podobnych"


def assess(features: dict[str, Any], neighbours: list[Case], ranges: dict[str, dict[str, Any]],
           min_n: int = 8, all_cases: list[Case] | None = None) -> list[dict[str, Any]]:
    def fv(name):
        x = features.get(name)
        return x.get("value") if isinstance(x, dict) else x

    out: list[dict[str, Any]] = []
    value, vat = fv("value"), fv("vat_basis") or "unknown"
    months = fv("duration_months")
    km, rlm = fv("length_km"), fv("rlm")

    # 1. budget position among neighbours' contract values (gross)
    nb_vals = [(c, c.value_gross) for c in neighbours if c.value_gross]
    uv, how = comparable_value(value, vat, "gross")
    item: dict[str, Any] = {"metric": "budget_percentile", "title": "Budżet na tle podobnych umów",
                            "n": len(nb_vals), "case_ids": [str(c.project_id) for c, _ in nb_vals], "basis": how,
                            "formula": "Percentyl budżetu = jaka część umów podobnych inwestycji (wartość z pkt 4.4, brutto) była tańsza lub równa budżetowi tej inwestycji; P90 oznacza, że budżet jest wyższy niż w 9 na 10 podobnych umów."}
    if uv is not None and nb_vals:
        pct = percentile_rank(uv, [v for _, v in nb_vals])
        item.update(value=round(uv, 2), percentile=pct, position=_position(pct), quantiles=_q([v for _, v in nb_vals]))
        pr = ranges.get("paid_ratio") or {}
        if pr.get("p80"):
            # `amount` is the reserve itself (budget × (P80 − 1)), `total` the budget including it; both rounded to
            # 10 000 zł – the ratio comes from a dozen contracts, grosze would suggest false precision.
            reserve = max(0.0, uv * (pr["p80"] - 1))
            item["reserve_p80"] = {"ratio": pr["p80"], "amount": _round_k(reserve), "total": _round_k(uv + reserve),
                                   "pct": round((pr["p80"] - 1) * 100, 1),
                                   "note": f"rezerwa = budżet × (P80(wypłata/wartość) − 1) = {uv:,.0f} × {pr['p80'] - 1:.3f} (poziom: {pr['fallback_level']}, n={pr['n']})".replace(",", " ")}
    else:
        item["status"] = "not_compared"
        item["message"] = how if uv is None else "podobne inwestycje nie mają wartości umów"
    out.append(item)

    # 2. schedule: planned duration vs neighbours' planned and actual durations
    pd_ = [c.planned_days for c in neighbours if c.planned_days]
    ad = [c.actual_days for c in neighbours if c.actual_days and c.actual_days > 0]
    # plan is compared with the neighbours' PLANNED durations (like with like); actual durations already contain
    # the delays and would make almost every plan look "ambitious". Actual is the fallback when plans are missing.
    use_planned = len(pd_) >= 5
    base = pd_ if use_planned else ad
    item = {"metric": "schedule_percentile", "title": "Harmonogram na tle podobnych umów",
            "n": len(base), "n_planned": len(pd_), "n_actual": len(ad), "compared_to": "planned" if use_planned else "actual",
            "case_ids": [str(c.project_id) for c in neighbours if (c.planned_days if use_planned else c.actual_days)],
            "formula": ("Planowany czas realizacji podobnej umowy = okres realizacji zapisany w umowie (pkt 4.2 ogłoszenia o wykonaniu umowy) – porównujemy plan z planem. "
                        if use_planned else
                        "Faktyczny czas realizacji podobnej umowy = data wykonania (pkt 5.2) minus data zawarcia (pkt 4.1) – podobne umowy nie podają planu, więc porównujemy z faktycznym czasem (zawiera opóźnienia). ")
                       + "Percentyl harmonogramu = jaka część podobnych umów miała czas krótszy lub równy planowanemu czasowi tej inwestycji; niski percentyl oznacza ambitny harmonogram."}
    if months and base:
        days = float(months) * 30
        pct = percentile_rank(days, base)
        item.update(value_days=round(days), percentile=pct, position=_position(pct), quantiles=_q(base),
                    actual_quantiles=_q(ad) if ad else None, planned_quantiles=_q(pd_) if pd_ else None,
                    percentile_actual=percentile_rank(days, ad) if ad else None,
                    percentile_planned=percentile_rank(days, pd_) if pd_ else None)
        dl = ranges.get("delay_days") or {}
        if dl.get("p80") is not None:
            item["p80_end_days"] = round(days + dl["p80"])
            item["note"] = f"Plan {days:.0f} dni; z opóźnieniem takim jak w 8 na 10 podobnych umów: {days + dl['p80']:.0f} dni"
        item["tight"] = pct < 0.25
    else:
        item["status"] = "not_compared"
        item["message"] = "brak planowanego czasu realizacji w opisie" if not months else "podobne inwestycje nie mają dat realizacji"
    out.append(item)

    # 3. cost per km / per RLM (gross paid or contract value)
    for metric, size, attr, unit in (("cost_per_km", km, "length_km", "km"), ("cost_per_rlm", rlm, "rlm", "RLM")):
        pool = [c for c in neighbours if getattr(c, attr) and (c.paid_gross or c.value_gross)]
        src = "sąsiedzi"
        if len(pool) < min_n and all_cases:
            sub = fv("subsector_main")
            pool = [c for c in all_cases if c.completed and getattr(c, attr) and (c.paid_gross or c.value_gross)
                    and (not sub or c.subsector_main == sub)]
            src = f"podsektor {sub}" if sub else "wszystkie"
        unit_costs = [((c.paid_gross or c.value_gross) / getattr(c, attr), c) for c in pool]
        item = {"metric": metric, "title": f"Koszt na {unit}", "n": len(unit_costs), "pool": src,
                "case_ids": [str(c.project_id) for _, c in unit_costs][:50],
                "formula": f"Koszt jednostkowy = wypłata (pkt 5.5) albo wartość umowy (pkt 4.4), brutto, podzielona przez {unit} z opisu przedmiotu zamówienia; liczymy tylko podobne umowy, w których opis podaje tę skalę."}
        if size and unit_costs:
            vals = [u for u, _ in unit_costs]
            item["quantiles"] = _q(vals)
            if uv is not None:
                mine = uv / float(size)
                item.update(value=round(mine, 2), percentile=percentile_rank(mine, vals), position=_position(percentile_rank(mine, vals)))
            else:
                item["message"] = how
        else:
            item["status"] = "not_compared"
            item["message"] = "brak skali w opisie" if not size else f"brak przypadków z podaną skalą ({unit})"
        out.append(item)

    # 4. winning offer vs estimate / budget among neighbours (like-for-like only)
    for metric, title in (("offer_vs_budget", "Cena oferty a budżet zamawiającego"),
                          ("offer_vs_estimate", "Cena oferty a wartość szacunkowa")):
        r = ranges.get(metric) or {}
        out.append({"metric": metric, "title": title, "n": r.get("n", 0), "p50": r.get("p50"), "p80": r.get("p80"),
                    "p95": r.get("p95"), "fallback_level": r.get("fallback_level"), "case_ids": r.get("case_ids", []),
                    "formula": r.get("formula")})

    # 5. cancellations under art. 255 pkt 3 (offer above the financing amount)
    r = ranges.get("share_cancelled_255_3") or {}
    out.append({"metric": "cancelled_255_3", "title": "Unieważnienia z powodu ceny (art. 255 pkt 3 Pzp)",
                "n": r.get("n", 0), "k": r.get("k"), "estimate": r.get("estimate"), "ci_low": r.get("ci_low"),
                "ci_high": r.get("ci_high"), "fallback_level": r.get("fallback_level"), "case_ids": r.get("case_ids", []),
                "formula": r.get("formula")})
    return out
