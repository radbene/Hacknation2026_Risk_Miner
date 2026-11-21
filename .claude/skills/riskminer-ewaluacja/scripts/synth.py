#!/usr/bin/env python3
"""Generator danych syntetycznych w pelnym schemacie zbioru (plan B, gdy brak danych albo do testow UI).

  python3 synth.py --n 5000 --table ../../riskminer-klasa-referencyjna/references/reference_table_bzp_works_2026-11.json --out synth.csv

Odsetki opoznien i wzrostu kosztu sa losowane z tabeli klasy referencyjnej (prawdziwe czestosci z BZP),
wiec rozklady brzegowe sa realistyczne, ale zaleznosci miedzy cechami sa uproszczone.
Dane syntetyczne zawsze oznaczaj w interfejsie i w prezentacji. Zaleznosci: numpy, pandas (BSD).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "riskminer-klasa-referencyjna", "scripts"))
from refclass_forecast import rates  # noqa: E402


def generate(n: int, table: dict, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    value = np.round(10 ** rng.normal(5.75, 0.62, n)).clip(8e3, 3e8)       # mediana ok. 560 tys. zl
    period = np.round(np.exp(rng.normal(4.6, 0.75, n)) * (value / 5e5) ** 0.18).clip(7, 1500)
    eu = (rng.random(n) < 0.147).astype(int)                               # 14,7% umow z UE (BZP 11.2026)
    signed = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 600, n), unit="D")
    n_offers = np.maximum(1, rng.poisson(3.2, n))
    rows = []
    for i in range(n):
        r = rates(table, float(value[i]), float(period[i]), int(eu[i]))
        late = int(rng.random() < r["p_late"])
        cost_up = int(rng.random() < min(0.95, r["p_cost_up"] * (1.5 if late else 0.8)))
        ratio = 1 + (abs(rng.normal(0.06, 0.07)) + 0.011 if cost_up else -abs(rng.normal(0, 0.004)))
        rel = float(np.interp(rng.random(), [0, .25, .5, .75, .9, 1], [0.01, .13, .28, .54, .91, 2.2])) if late else -rng.random() * 0.05
        done_date = signed[i] + pd.Timedelta(days=int(period[i] * (1 + rel)))
        est = value[i] / 1.23 * float(np.exp(rng.normal(0.08, 0.2)))
        rows.append(dict(
            bzp=f"SYNT-{i:06d}", pub_date=(done_date + pd.Timedelta(days=int(rng.integers(3, 30)))).date().isoformat(),
            province=f"PL{int(rng.choice(np.arange(2, 34, 2))):02d}", buyer_nip=f"b{int(rng.integers(0, max(5, n // 4))):05d}",
            contractor_nip=f"c{int(rng.integers(0, max(5, n // 3))):05d}", below_eu=int(value[i] < 2.5e7),
            cpv=str(rng.choice(["45000000", "45233120", "45233140", "45210000", "45453000", "45231300", "45310000"])),
            eu_funded=int(eu[i]), mode=str(rng.choice(["tryb podstawowy, art. 275 pkt 1", "tryb podstawowy, art. 275 pkt 2",
                                                       "zamówienie z wolnej ręki", "przetarg nieograniczony, art. 132"], p=[.71, .23, .03, .03])),
            signed_date=signed[i].date().isoformat(), period_days=int(period[i]), value=float(value[i]),
            done=1, done_date=done_date.date().isoformat(), on_time=1 - late, n_changes=int(late or cost_up) + int(rng.random() < 0.15),
            price_up=cost_up, paid=round(float(value[i] * ratio), 2), proper=1,
            n_offers=int(n_offers[i]), est_value=round(est, 2), price_min=float(value[i]),
            price_max=round(float(value[i] * (1 + abs(rng.normal(0.25, 0.3)) * (n_offers[i] > 1))), 2),
            label_late=late, label_cost_up=cost_up, label_failed=0, synthetic=1))
    d = pd.DataFrame(rows)
    sys.path.insert(0, os.path.join(HERE, "..", "..", "riskminer-dane-i-zrodla", "scripts"))
    from bzp_join import add_features  # noqa: E402
    return add_features(d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--table", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    d = generate(a.n, json.load(open(a.table, encoding="utf-8")), a.seed)
    d.to_csv(a.out, index=False)
    print(f"Zapisano {len(d)} umow syntetycznych do {a.out}; opoznione {d.label_late.mean():.1%}, wzrost kosztu {d.label_cost_up.mean():.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
