#!/usr/bin/env python3
"""Baseline end-to-end: tabela (CSV/XLSX/JSON/Parquet) -> model ryzyka -> metryki i raport.

Przyklady:
  python3 baseline.py --data contracts_works_sample_500.csv --preset bzp-sample --out out/
  python3 baseline.py --data dataset.csv --preset bzp-full --out out/
  python3 baseline.py --data dane_partnera.xlsx --label czy_opozniony --time-col data_umowy \
      --drop id,nazwa --leak data_zakonczenia,kwota_koncowa --out out/

Co robi: wybiera cechy (liczbowe i kategoryczne o malej liczbie wartosci), odrzuca kolumny
z przeciekiem etykiety, dzieli dane czasowo (ostatnie 25% jako test, jesli jest --time-col),
uczy regresje logistyczna i gradient boosting, liczy AUC, PR-AUC, Brier, precision@k i lift,
zapisuje metrics.json, report.md, predictions.csv. Zaleznosci: pandas, numpy, scikit-learn (BSD).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

PRESETS = {
    # probka z data-samples/bzp (schemat skrocony)
    # Uwaga: probka to przekroj ogloszen z 2 tygodni, wiec podzial po dacie zawarcia umowy
    # bylby obciazony (swiezo zawarte umowy w probce to tylko te krotkie i terminowe).
    # Dlatego: podzial losowy grupowany po zamawiajacym.
    "bzp-sample": dict(
        label="late", time_col=None, group_col="bid", month_from="signed",
        leak=["paid", "done", "n_changes", "price_up", "proper", "pub_day", "signed"],
        drop=["cid"], prefix={"cpv": 3}, as_cat=["prov", "cpv"],
    ),
    # pelny zbior z bzp_parse.py + bzp_join.py
    "bzp-full": dict(
        label="label_late", time_col="pub_date", group_col=None, month_from=None, as_cat=["cpv3", "province"],
        leak=["paid", "done", "done_date", "on_time", "n_changes", "sum_changes", "price_up", "proper",
              "change_reasons", "extra_info", "label_cost_up", "label_failed", "signed_date", "pub_date"],
        drop=["bzp", "notice_no", "notice_no_res", "tender_id", "title", "buyer_name", "buyer_nip",
              "contractor_nip", "eu_name", "eu_project_no", "prior_notice", "result_notice", "period_raw",
              "mode", "currency", "order_type", "cpv", "cpv5", "signed_year"],
        prefix={},
    ),
}


def load(path: Path) -> pd.DataFrame:
    s = path.suffix.lower()
    if s in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if s == ".parquet":
        return pd.read_parquet(path)
    if s in (".json", ".jsonl"):
        return pd.read_json(path, lines=(s == ".jsonl"))
    for sep in (",", ";", "\t"):
        d = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=True)
        if d.shape[1] > 1:
            break
    for c in d.columns:  # liczby tam, gdzie sie da (takze zapis z przecinkiem)
        conv = pd.to_numeric(d[c].str.replace(" ", "").str.replace(",", "."), errors="coerce")
        if conv.notna().sum() >= 0.95 * d[c].notna().sum() and d[c].notna().any():
            d[c] = conv
    return d


def to_binary(y: pd.Series) -> pd.Series:
    if y.dtype == object:
        m = {"tak": 1, "nie": 0, "true": 1, "false": 0, "1": 1, "0": 0, "t": 1, "n": 0, "yes": 1, "no": 0}
        return y.str.strip().str.lower().map(m)
    return y.astype(float)


def precision_at(y: np.ndarray, p: np.ndarray, frac: float) -> float:
    k = max(1, int(round(frac * len(y))))
    return float(y[np.argsort(-p)[:k]].mean())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--label")
    ap.add_argument("--time-col", help="kolumna czasu do podzialu trening/test (nie jest cecha)")
    ap.add_argument("--group-col", help="kolumna grupy (np. zamawiajacy): ta sama grupa nie trafia do treningu i testu")
    ap.add_argument("--as-cat", default="", help="kolumny liczbowe traktowane jako kategorie (np. kody)")
    ap.add_argument("--leak", default="", help="kolumny znane dopiero po fakcie (przeciek), po przecinku")
    ap.add_argument("--drop", default="", help="identyfikatory i inne kolumny do pominiecia")
    ap.add_argument("--max-card", type=int, default=40, help="maks. liczba wartosci cechy kategorycznej")
    ap.add_argument("--out", type=Path, default=Path("out"))
    a = ap.parse_args()

    cfg = dict(label=a.label, time_col=a.time_col, group_col=a.group_col, month_from=None, leak=[], drop=[], prefix={}, as_cat=[])
    if a.preset:
        cfg.update(PRESETS[a.preset])
    cfg["label"] = a.label or cfg["label"]
    cfg["time_col"] = a.time_col or cfg["time_col"]
    cfg["group_col"] = a.group_col or cfg["group_col"]
    cfg["as_cat"] = cfg["as_cat"] + [c for c in a.as_cat.split(",") if c]
    cfg["leak"] = cfg["leak"] + [c for c in a.leak.split(",") if c]
    cfg["drop"] = cfg["drop"] + [c for c in a.drop.split(",") if c]
    if not cfg["label"]:
        raise SystemExit("Podaj --label albo --preset.")

    d = load(a.data)
    if cfg["label"] not in d.columns:
        raise SystemExit(f"Brak kolumny etykiety '{cfg['label']}'. Kolumny: {list(d.columns)}")
    for col, n in cfg["prefix"].items():
        if col in d:
            d[col] = d[col].astype(str).str.split(".").str[0].str[:n]
    y_all = to_binary(d[cfg["label"]])
    d = d[y_all.notna()].reset_index(drop=True)
    y = y_all[y_all.notna()].astype(int).to_numpy()

    tcol = cfg["time_col"] if cfg["time_col"] in d.columns else None
    gcol = cfg["group_col"] if cfg["group_col"] in d.columns else None
    order = None
    if tcol:
        t = d[tcol]
        tnum = pd.to_datetime(t, errors="coerce") if t.dtype == object else t
        order = np.argsort(pd.Series(tnum).rank(method="first").to_numpy())
    if cfg["month_from"] in d.columns:  # data w zapisie RRMMDD -> miesiac zawarcia umowy
        d["signed_month"] = pd.to_numeric(d[cfg["month_from"]], errors="coerce") // 100 % 100
    for c in cfg["as_cat"]:
        if c in d.columns:
            d[c] = d[c].astype(str).str.split(".").str[0].where(d[c].notna())

    excl = set(cfg["leak"]) | set(cfg["drop"]) | {cfg["label"]} | ({tcol} if tcol else set()) | ({gcol} if gcol else set())
    num, cat, skipped = [], [], []
    for c in d.columns:
        if c in excl:
            continue
        if pd.api.types.is_numeric_dtype(d[c]):
            (num if d[c].notna().any() else skipped).append(c)
        elif d[c].nunique(dropna=True) <= a.max_card:
            cat.append(c)
        else:
            skipped.append(c)
    X = d[num + cat].copy()
    for c in cat:
        X[c] = X[c].astype(object).where(X[c].notna(), "brak").astype(str)

    if order is not None:
        cut = int(0.75 * len(d))
        tr, te = order[:cut], order[cut:]
        split = f"czasowy wg '{tcol}' (ostatnie 25% jako test)"
    elif gcol:
        tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=0).split(X, y, d[gcol].astype(str)))
        split = f"losowy 75/25 grupowany po '{gcol}'"
    else:
        tr, te = train_test_split(np.arange(len(d)), test_size=0.25, stratify=y, random_state=0)
        split = "losowy warstwowy 75/25 (brak kolumny czasu)"
    if len(set(y[te])) < 2 or len(set(y[tr])) < 2:
        raise SystemExit("Jedna klasa w zbiorze treningowym lub testowym: za malo danych albo zly podzial.")

    lr = Pipeline([
        ("prep", ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)), ("sc", StandardScaler())]), num),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=5), cat),
        ])),
        ("clf", LogisticRegression(max_iter=2000, C=0.5)),
    ])
    gb = Pipeline([
        ("prep", ColumnTransformer([
            ("num", "passthrough", num),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat),
        ])),
        ("clf", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=150,
                                               l2_regularization=1.0, random_state=0)),
    ])
    base = float(y[te].mean())
    res = {"n": int(len(d)), "n_train": int(len(tr)), "n_test": int(len(te)), "base_rate_test": round(base, 4),
           "base_rate_train": round(float(y[tr].mean()), 4), "split": split, "features_num": num,
           "features_cat": cat, "skipped": skipped, "excluded_leak": sorted(set(cfg["leak"]) & set(d.columns)),
           "models": {}}
    preds = {}
    for name, m in (("logreg", lr), ("gboost", gb)):
        m.fit(X.iloc[tr], y[tr])
        p = m.predict_proba(X.iloc[te])[:, 1]
        preds[name] = p
        cv = cross_val_score(m, X.iloc[tr], y[tr], scoring="roc_auc",
                             cv=StratifiedKFold(5, shuffle=True, random_state=0))
        res["models"][name] = {
            "auc": round(float(roc_auc_score(y[te], p)), 3),
            "pr_auc": round(float(average_precision_score(y[te], p)), 3),
            "brier": round(float(brier_score_loss(y[te], p)), 4),
            "brier_baseline": round(base * (1 - base), 4),
            "precision_at_10pct": round(precision_at(y[te], p, 0.10), 3),
            "precision_at_20pct": round(precision_at(y[te], p, 0.20), 3),
            "lift_at_20pct": round(precision_at(y[te], p, 0.20) / base, 2) if base else None,
            "cv_auc_train_mean": round(float(cv.mean()), 3), "cv_auc_train_std": round(float(cv.std()), 3),
        }
    best = max(res["models"], key=lambda k: res["models"][k]["auc"])
    imp = permutation_importance({"logreg": lr, "gboost": gb}[best], X.iloc[te], y[te], scoring="roc_auc",
                                 n_repeats=10, random_state=0)
    top = sorted(zip(X.columns, imp.importances_mean), key=lambda kv: -kv[1])[:8]
    res["best_model"] = best
    res["top_features_permutation_auc_drop"] = [[k, round(float(v), 4)] for k, v in top]

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "metrics.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    out = d.iloc[te].copy()
    out["y"] = y[te]
    for k, p in preds.items():
        out[f"p_{k}"] = p.round(4)
    out.to_csv(a.out / "predictions.csv", index=False)
    lines = [f"# Baseline: {a.data.name}", "",
             f"- Wiersze: {res['n']} (trening {res['n_train']}, test {res['n_test']}); podzial: {split}",
             f"- Odsetek klasy 1: trening {res['base_rate_train']:.1%}, test {base:.1%}",
             f"- Cechy liczbowe: {', '.join(num)}", f"- Cechy kategoryczne: {', '.join(cat)}",
             f"- Wykluczone jako przeciek: {', '.join(res['excluded_leak'])}", "",
             "| Model | AUC | PR-AUC | Brier (baza) | P@10% | P@20% | Lift@20% | CV AUC (trening) |", "|---|---|---|---|---|---|---|---|"]
    for k, m in res["models"].items():
        lines.append(f"| {k} | {m['auc']} | {m['pr_auc']} | {m['brier']} ({m['brier_baseline']}) | "
                     f"{m['precision_at_10pct']} | {m['precision_at_20pct']} | {m['lift_at_20pct']} | "
                     f"{m['cv_auc_train_mean']} +/- {m['cv_auc_train_std']} |")
    lines += ["", f"Najwazniejsze cechy ({best}, spadek AUC po permutacji): " +
              ", ".join(f"{k} ({v:+.3f})" for k, v in res["top_features_permutation_auc_drop"])]
    (a.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
