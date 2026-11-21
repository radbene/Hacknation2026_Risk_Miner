#!/usr/bin/env python3
"""Prognoza z klasy referencyjnej: P(opoznienie), P(wzrost kosztu), P50/P80 terminu i kosztu.

  python3 refclass_forecast.py --table reference_table.json --value 3200000 --period-days 270 --eu 1 \
      --start 2026-12-01
  python3 refclass_forecast.py --table reference_table.json --batch inwestycje.csv --out prognozy.csv

Metoda (opis dla jury: research/04_technologia_i_ewaluacja.md):
1. Odsetek z komorki wartosc x okres jest "sciagany" do odsetka dla przedzialu wartosci, a ten do
   odsetka ogolnego (srednia wazona: (k + m*p_rodzica)/(n + m), m = 20). Male komorki nie daja skrajnych wynikow.
2. Korekta o finansowanie UE: iloraz szans z tabeli by_value_eu, sciagany do 1 przy malej liczbie umow.
3. Monte Carlo (domyslnie 20 000 losowan): opoznienie tak/nie z prawdopodobienstwem p; dlugosc opoznienia
   z empirycznych kwantyli opoznienia wzglednego wsrod umow opoznionych; koszt koncowy z kwantyli
   wyplata/wartosc. Opoznienie i koszt sa powiazane kopula Gaussa (RHO = 0.45, oszacowane na probce 500 umow:
   wzrost kosztu w 46% umow opoznionych i 19% terminowych), a rozklady brzegowe pozostaja zgodne z tabela.
   Ogony (opoznienie powyzej ostatniego kwantyla w tabeli, koszt powyzej P95) sa ekstrapolowane: to zalozenie.
Zaleznosci: numpy (BSD); pandas tylko dla --batch.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, timedelta
from statistics import NormalDist

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from refclass_build import period_bucket, value_bucket  # noqa: E402

M = 20  # sila sciagania do rodzica (liczba "wirtualnych" umow)
RHO = 0.45  # korelacja ukryta opoznienie-koszt (kopula Gaussa), oszacowana na probce 500 umow BZP
DEFAULT_DELAY_Q = {"p25": 0.13, "p50": 0.28, "p75": 0.54, "p90": 0.91}  # BZP roboty, 2-13.11.2026, n=561
_PHI = np.vectorize(lambda z: 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))


def _shrink(c: dict | None, key: str, parent: float) -> tuple[float, int]:
    if not c or c.get(key) is None:
        return parent, 0
    n = c["n"]
    return (c[key] / 100 * n + M * parent) / (n + M), n


def rates(t: dict, value: float, period_days: float | None, eu: int | None) -> dict:
    vb, pb = value_bucket(value), period_bucket(period_days)
    out = {"value_bucket": vb, "period_bucket": pb}
    for key, name in (("late_pct", "p_late"), ("cost_up_pct", "p_cost_up")):
        g = t["global"][key] / 100
        pv, _ = _shrink(t["by_value"].get(vb), key, g)
        p, n_cell = _shrink(t["by_value_period"].get(f"{vb}|{pb}"), key, pv)
        if eu in (0, 1):
            c = t["by_value_eu"].get(f"{vb}|eu={eu}")
            if c and c.get(key) is not None and 0 < pv < 1:
                pe = min(max(c[key] / 100, 0.01), 0.99)
                w = c["n"] / (c["n"] + 50)
                log_or = w * (np.log(pe / (1 - pe)) - np.log(pv / (1 - pv)))
                odds = p / (1 - p) * np.exp(log_or)
                p = odds / (1 + odds)
        out[name] = round(float(p), 3)
        out["n_cell"] = n_cell
    cell = t["by_value_period"].get(f"{vb}|{pb}")
    src = cell if cell and cell["n"] >= 30 and cell.get("ratio_p95") else t["by_value"].get(vb) or t["global"]
    out["ratio_q"] = {k: src[k] for k in ("ratio_p50", "ratio_p80", "ratio_p95")}
    out["ratio_from"] = "komorka" if src is cell else "przedzial wartosci"
    return out


def _sample_from_quantiles(rng, qs: list[tuple[float, float]], n: int) -> np.ndarray:
    ps, vs = zip(*qs)
    return np.interp(rng.random(n), ps, vs)


def forecast(t: dict, value: float, period_days: float, eu: int | None = None, start: date | None = None,
             n_sim: int = 20000, seed: int = 0) -> dict:
    if not (value > 0) or not (period_days > 0):
        raise ValueError("value i period_days musza byc wieksze od zera")
    r = rates(t, value, period_days, eu)
    rng = np.random.default_rng(seed)
    dq = t.get("delay_rel_q_among_late")
    delay_src = "tabela" if dq else "domyslny (BZP roboty 11.2026, n=561)"
    dq = dq or DEFAULT_DELAY_Q
    # Kopula Gaussa: z_l steruje opoznieniem, z_c pozycja w rozkladzie kosztu; u jest jednostajne na (0,1).
    z_l = rng.standard_normal(n_sim)
    late = z_l > NormalDist().inv_cdf(1 - min(max(r["p_late"], 1e-4), 1 - 1e-4))
    z_c = RHO * z_l + math.sqrt(1 - RHO ** 2) * rng.standard_normal(n_sim)
    u = _PHI(z_c)
    last_p, last_v = (0.95, dq["p95"]) if "p95" in dq else (0.9, dq["p90"])
    pts = [(0, 0.01), (0.25, dq["p25"]), (0.5, dq["p50"]), (0.75, dq["p75"]), (0.9, dq["p90"])]
    if last_p > 0.9:
        pts.append((last_p, last_v))
    pts.append((1.0, last_v * 2.5))
    rel = np.interp(rng.random(n_sim), [p for p, _ in pts], [v for _, v in pts])
    days = period_days * (1 + np.where(late, rel, 0.0))
    q = r["ratio_q"]
    ratio = np.interp(u, [0, 0.1, 0.5, 0.8, 0.95, 1.0],
                      [0.90, min(1.0, q["ratio_p50"]), q["ratio_p50"], q["ratio_p80"], q["ratio_p95"], q["ratio_p95"] * 1.15])
    cost = value * ratio
    pct = lambda a, p: float(np.quantile(a, p))  # noqa: E731
    d80, c80 = pct(days, 0.8), pct(cost, 0.8)
    res = {
        **r,
        "days_planned": period_days,
        "days_p50": round(pct(days, 0.5)), "days_p80": round(d80), "days_p95": round(pct(days, 0.95)),
        "cost_planned": round(value),
        "cost_p50": round(pct(cost, 0.5)), "cost_p80": round(c80), "cost_p95": round(pct(cost, 0.95)),
        "reserve_p80_pct": round(100 * (c80 / value - 1), 1),
        "p_within_both_p80": round(float(((days <= d80) & (cost <= c80)).mean()), 3),
        "assumptions": [f"rozklad dlugosci opoznienia: {delay_src}; ogon powyzej P{int(last_p * 100)} ekstrapolowany",
                        "koszt: kwantyle wyplata/wartosc z tabeli; ogon powyzej P95 i ponizej P10 ekstrapolowany",
                        f"powiazanie opoznienia z kosztem: kopula Gaussa, RHO={RHO} (z probki 500 umow)",
                        "klasa referencyjna: " + t["meta"].get("source", "")],
    }
    if start:
        res.update(end_planned=(start + timedelta(days=int(period_days))).isoformat(),
                   end_p50=(start + timedelta(days=res["days_p50"])).isoformat(),
                   end_p80=(start + timedelta(days=res["days_p80"])).isoformat())
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--value", type=float)
    ap.add_argument("--period-days", type=float)
    ap.add_argument("--eu", type=int, choices=[0, 1])
    ap.add_argument("--start", type=date.fromisoformat)
    ap.add_argument("--batch", help="CSV z kolumnami value, period_days, opcjonalnie eu (albo eu_funded)")
    ap.add_argument("--out")
    a = ap.parse_args()
    t = json.load(open(a.table, encoding="utf-8"))
    if a.batch:
        import pandas as pd
        d = pd.read_csv(a.batch)
        eu_col = "eu" if "eu" in d else ("eu_funded" if "eu_funded" in d else None)
        rows = []
        for _, x in d.iterrows():
            if not (x["value"] > 0) or pd.isna(x["period_days"]) or not (x["period_days"] > 0):
                rows.append({}); continue
            eu = int(x[eu_col]) if eu_col and not pd.isna(x[eu_col]) else None
            f = forecast(t, float(x["value"]), float(x["period_days"]), eu, n_sim=4000)
            rows.append({k: f[k] for k in ("p_late", "p_cost_up", "n_cell", "days_p80", "cost_p80", "reserve_p80_pct")})
        res = pd.concat([d, pd.DataFrame(rows)], axis=1)
        res.to_csv(a.out or "prognozy.csv", index=False)
        print(f"Zapisano {len(res)} prognoz do {a.out or 'prognozy.csv'}; srednie P(opoznienie) = {res['p_late'].mean():.3f}")
        return 0
    if a.value is None or a.period_days is None:
        raise SystemExit("Podaj --value i --period-days albo --batch.")
    if a.value <= 0 or a.period_days <= 0:
        raise SystemExit("--value i --period-days musza byc wieksze od zera.")
    print(json.dumps(forecast(t, a.value, a.period_days, a.eu, a.start), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
