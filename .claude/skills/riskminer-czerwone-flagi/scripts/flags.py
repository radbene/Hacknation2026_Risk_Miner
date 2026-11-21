#!/usr/bin/env python3
"""Sygnaly ryzyka (czerwone flagi) dla umow: reguly z dowodem, bez modelu.

  python3 flags.py --data dataset.csv --out flags.jsonl [--table reference_table.json] [--asof 2026-11-21]

Wejscie: zbior w pelnym schemacie (bzp_parse.py + bzp_join.py albo sample_to_full.py).
Wyjscie: JSONL, jeden rekord na umowe: {id, score, level, flags:[{code,name,severity,evidence,basis}]}
oraz podsumowanie czestosci flag. Jesli w danych jest etykieta label_late, skrypt wypisuje tez,
jak czesto umowy z dana flaga byly opoznione (walidacja reguly na danych, nie dowod przyczyny).
Kazda flaga to "sygnal do weryfikacji", nie zarzut. Definicje i zrodla progow: references/katalog-flag.md.
Zaleznosci: pandas, numpy (BSD).
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import numpy as np
import pandas as pd

LEVELS = [(0, "bez sygnalow"), (1, "do przejrzenia"), (4, "podwyzszona uwaga"), (7, "pilne do przejrzenia")]


def _f(code, name, sev, evidence, basis):
    return {"code": code, "name": name, "severity": sev, "evidence": evidence, "basis": basis}


def _num(x):
    return None if x is None or pd.isna(x) else float(x)


def contract_flags(r: pd.Series, hist: dict, p_late: float | None, asof: pd.Timestamp | None) -> list[dict]:
    fl = []
    n_off, val, est = _num(r.get("n_offers")), _num(r.get("value")), _num(r.get("est_value"))
    pmin, pmax, pd_ = _num(r.get("price_min")), _num(r.get("price_max")), _num(r.get("period_days"))
    mode = str(r.get("mode") or "")
    if n_off == 1:
        fl.append(_f("K1", "Jedna oferta", 2, "liczba ofert = 1 (ogloszenie o wyniku, pkt 6.1)",
                     "wskaznik konkurencji: Single Market Scoreboard, Fazekas i Kocsis (CRI)"))
    if re.search(r"wolnej ręki|negocjacj\w+ bez ogłoszenia", mode):
        fl.append(_f("K2", "Tryb niekonkurencyjny", 2, f"tryb: {mode[:80]}", "tryb bez ogloszenia: wskaznik CRI"))
    if val and est:
        ratio = val / (est * 1.23)
        if ratio < 0.70:
            fl.append(_f("C1", "Cena ponizej 70% szacunku", 2,
                         f"wartosc umowy {val:,.0f} zl = {ratio:.0%} szacunku brutto ({est * 1.23:,.0f} zl; VAT 23% przyjety)",
                         "prog 30% ponizej wartosci zamowienia: art. 224 ust. 2 Pzp (razaco niska cena)"))
        elif ratio > 1.10:
            fl.append(_f("C2", "Cena powyzej szacunku", 1,
                         f"wartosc umowy {val:,.0f} zl = {ratio:.0%} szacunku brutto",
                         "presja budzetowa: w probce BZP 11.2026 umowy powyzej szacunku byly czesciej opoznione (maly n)"))
    if pmin and pmax and pmin > 0 and pmax / pmin >= 2.0 and (n_off or 0) >= 3:
        fl.append(_f("C3", "Duzy rozrzut cen ofert", 1, f"najwyzsza/najnizsza = {pmax / pmin:.1f}x przy {int(n_off)} ofertach",
                     "mozliwe niejasne OPZ lub blad wyceny (hipoteza zespolu)"))
    if _num(r.get("n_abn_low")):
        fl.append(_f("C4", "Oferty z razaco niska cena", 1, f"liczba ofert z razaco niska cena = {int(r['n_abn_low'])} (pkt 6.1.7)",
                     "art. 224 Pzp"))
    if val and pd_ and val >= 1e6 and pd_ <= 90:
        fl.append(_f("H1", "Krotki termin przy duzej wartosci", 2, f"{pd_:.0f} dni na umowe za {val:,.0f} zl",
                     "napiety harmonogram (hipoteza; sprawdz w tabeli referencyjnej komorke wartosc x okres)"))
    sd = pd.to_datetime(r.get("signed_date"), errors="coerce")
    if pd.notna(sd) and pd_ and str(r.get("cpv", "")).startswith(("4523", "4511", "4524")):
        end = sd + pd.Timedelta(days=pd_)
        if end.month in (12, 1, 2):
            fl.append(_f("H2", "Planowany koniec robot ziemnych/drogowych zima", 1,
                         f"planowany koniec {end.date()} (CPV {r['cpv']})",
                         "warunki atmosferyczne to czesta przyczyna zmian terminow w ogloszeniach BZP"))
    if p_late is not None and p_late >= 0.40:
        fl.append(_f("R1", "Wysokie ryzyko w klasie referencyjnej", 2 if p_late < 0.55 else 3,
                     f"w podobnych zakonczonych umowach opoznienie zadeklarowano w {p_late:.0%} przypadkow",
                     "klasa referencyjna z ogloszen o wykonaniu umowy (riskminer-klasa-referencyjna)"))
    h = hist.get(("c", r.get("contractor_nip")))
    if h and h[0] >= 3 and h[1] / h[0] >= 0.5:
        fl.append(_f("W1", "Wykonawca: czeste opoznienia w innych umowach", 2,
                     f"{h[1]} z {h[0]} innych zakonczonych umow tego wykonawcy po terminie",
                     "historia z ogloszen o wykonaniu umowy; mala liczba umow = duza niepewnosc"))
    h = hist.get(("b", r.get("buyer_nip")))
    if h and h[0] >= 5 and h[1] / h[0] >= 0.5:
        fl.append(_f("Z1", "Zamawiajacy: czeste opoznienia umow", 1,
                     f"{h[1]} z {h[0]} innych zakonczonych umow tego zamawiajacego po terminie",
                     "moze wskazywac na jakosc przygotowania inwestycji (hipoteza)"))
    # Sygnaly w trakcie realizacji (gdy podano --asof i umowa nie ma jeszcze wyniku)
    if asof is not None and pd.notna(sd) and pd_ and pd.isna(r.get("done")):
        overdue = (asof - (sd + pd.Timedelta(days=pd_))).days
        if overdue > 30:
            fl.append(_f("S1", "Termin minal, brak ogloszenia o wykonaniu", 2 if overdue < 120 else 3,
                         f"planowany koniec minal {overdue} dni temu; ogloszenie o wykonaniu nalezy opublikowac w 30 dni (art. 448 Pzp)",
                         "brak ogloszenia moze oznaczac opoznienie albo zaniedbanie publikacji"))
    if _num(r.get("n_change_notices")):
        k = int(r["n_change_notices"])
        fl.append(_f("S2", "Ogloszenia o zmianie umowy w trakcie realizacji", 1 if k == 1 else 2,
                     f"liczba ogloszen o zmianie umowy: {k}", "art. 455 Pzp; w zakonczonych umowach zmiana wspolwystepuje z opoznieniem"))
    return fl


def history(d: pd.DataFrame) -> dict:
    """Historia opoznien wykonawcy/zamawiajacego liczona z pominieciem biezacej umowy (leave-one-out)."""
    out = {}
    if "label_late" not in d:
        return out
    for key, col in (("c", "contractor_nip"), ("b", "buyer_nip")):
        if col not in d:
            continue
        g = d.dropna(subset=["label_late"]).groupby(col)["label_late"].agg(["count", "sum"])
        out[key] = g
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--table", help="tabela klasy referencyjnej (JSON) do flagi R1")
    ap.add_argument("--asof", help="data oceny (RRRR-MM-DD) dla sygnalow w trakcie realizacji")
    a = ap.parse_args()
    d = pd.read_csv(a.data, dtype={"cpv": str, "buyer_nip": str, "contractor_nip": str})
    asof = pd.Timestamp(a.asof) if a.asof else None
    hist_tabs = history(d)
    table = forecast_rates = None
    if a.table:
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                        "riskminer-klasa-referencyjna", "scripts"))
        from refclass_forecast import rates as forecast_rates  # noqa: E402
        table = json.load(open(a.table, encoding="utf-8"))
    rows, counts = [], {}
    for i, r in d.iterrows():
        hist = {}
        for key, col in (("c", "contractor_nip"), ("b", "buyer_nip")):
            tab = hist_tabs.get(key)
            if tab is not None and r.get(col) in tab.index:
                n, k = tab.loc[r[col]]
                own = r.get("label_late")
                if not pd.isna(own):
                    n, k = n - 1, k - own
                hist[(key, r[col])] = (int(n), int(k))
        p_late = None
        if table and _num(r.get("value")) and _num(r.get("value")) > 0:
            eu = None if pd.isna(r.get("eu_funded")) else int(r["eu_funded"])
            p_late = forecast_rates(table, float(r["value"]), _num(r.get("period_days")), eu)["p_late"]
        fl = contract_flags(r, hist, p_late, asof)
        score = int(sum(f["severity"] for f in fl))
        level = [name for thr, name in LEVELS if score >= thr][-1]
        rows.append({"id": r.get("bzp", i), "score": score, "level": level, "p_late_refclass": p_late, "flags": fl})
        for f in fl:
            counts.setdefault(f["code"], [f["name"], 0, 0, 0])
            counts[f["code"]][1] += 1
            if "label_late" in d and not pd.isna(r.get("label_late")):
                counts[f["code"]][2] += 1
                counts[f["code"]][3] += int(r["label_late"])
    with open(a.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    base = d["label_late"].mean() if "label_late" in d and d["label_late"].notna().any() else None
    print(f"Umowy: {len(rows)}; z co najmniej jednym sygnalem: {sum(1 for r in rows if r['flags'])}"
          + (f"; odsetek opoznionych ogolem: {base:.1%}" if base is not None else ""))
    print("kod | nazwa | liczba | opoznione wsrod oflagowanych")
    for code, (name, n, n_lab, k) in sorted(counts.items()):
        print(f"{code} | {name} | {n} | " + (f"{k}/{n_lab} = {k / n_lab:.0%}" if n_lab else "brak etykiety"))
    if base is not None:
        s = pd.DataFrame({"score": [r["score"] for r in rows], "late": d["label_late"].to_numpy()}).dropna()
        s["grupa"] = pd.cut(s["score"], [-1, 0, 3, 6, 99], labels=["0", "1-3", "4-6", "7+"])
        print("wynik -> odsetek opoznionych:", s.groupby("grupa", observed=True)["late"].agg(["size", "mean"]).round(3).to_dict("index"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
