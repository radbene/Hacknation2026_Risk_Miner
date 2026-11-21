"""`riskminer report` → docs/raport_z_testu.md (+ copy in exports/przyklad/).

Sections: record counts · linking vs the hand-verified gold set (correct / uncertain / wrong / missing) ·
organizer data errors found · monitoring alerts · new-investment analyses · integration (op_log) · LLM usage.
Linking metrics come from S1's `riskminer.link.quality` when importable, else from the evaluator below.
"""

from __future__ import annotations

import csv
import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from riskminer.core.config import REPO_ROOT, repo_path
from riskminer.models import (
    Alert,
    Analysis,
    AnalysisItem,
    DataIssue,
    LLMCall,
    OpLog,
    Procedure,
    Project,
    ProjectProcedure,
)

GOLD = REPO_ROOT / "backend" / "tests" / "fixtures" / "gold" / "links_gold.csv"
AUTO_CONFIDENCE = 0.9  # ≥ this and still "proposed" counts as an automatic (certain) link
COUNT_TABLES = ["project", "procedure", "project_procedure", "notice", "contract", "contract_change", "event",
                "document", "chunk", "evidence", "data_issue", "analysis", "analysis_item", "alert",
                "knowledge_table", "review", "op_log", "llm_call", "raw_record"]


def table_counts(session: Session, tables=COUNT_TABLES) -> dict[str, int]:
    from sqlalchemy import text

    out = {}
    for t in tables:
        try:
            out[t] = session.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() or 0
        except Exception:  # noqa: BLE001
            session.rollback()
            out[t] = -1
    return out


# ---------------------------------------------------------------- linking evaluation


def load_gold(path: Path = GOLD) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate_links(session: Session, gold: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Procedure-level evaluation: one expected unit = (rm_id, ocid, part_no) from gold rows labelled `link`."""
    gold = load_gold() if gold is None else gold
    if not gold:
        return {"available": False}
    expected: dict[str, set[tuple[str, str]]] = defaultdict(set)
    negatives: dict[str, set[tuple[str, str]]] = defaultdict(set)
    missing_in_bzp: set[str] = set()
    for g in gold:
        key = (g.get("ocid") or "", (g.get("part_no") or "").strip())
        if g["label"] == "link" and key[0]:
            expected[g["rm_id"]].add(key)
        elif g["label"] in ("decoy", "other_part") and key[0]:
            negatives[g["rm_id"]].add(key)
        elif g["label"] == "missing_in_bzp":
            missing_in_bzp.add(g["rm_id"])

    rows = session.execute(
        select(Project.code, Procedure.ocid, ProjectProcedure.part_no, ProjectProcedure.status,
               ProjectProcedure.confidence, ProjectProcedure.method, ProjectProcedure.alternatives)
        .join(Project, Project.id == ProjectProcedure.project_id)
        .join(Procedure, Procedure.id == ProjectProcedure.procedure_id)
    ).all()
    system: dict[str, list] = defaultdict(list)
    for r in rows:
        system[r.code].append(r)

    def _match(exp: tuple[str, str], r) -> bool:
        return r.ocid == exp[0] and (not exp[1] or r.part_no is None or str(r.part_no) == exp[1])

    details, verdicts = [], Counter()
    for rm in sorted(set(expected) | set(system) | missing_in_bzp):
        links = system.get(rm, [])
        for exp in sorted(expected.get(rm, set())):
            hit = [r for r in links if _match(exp, r)]
            alt_hit = any(exp[0] in str(r.alternatives or "") for r in links)
            if hit and hit[0].status in ("approved", "edited"):
                v = "correct"
            elif hit and hit[0].status == "rejected":
                v = "wrong"
            elif hit and (hit[0].confidence or 0) >= AUTO_CONFIDENCE:
                v = "correct"
            elif hit or alt_hit:
                v = "uncertain"
            else:
                v = "missing"
            verdicts[v] += 1
            r0 = hit[0] if hit else None
            details.append({"rm_id": rm, "ocid": exp[0], "part_no": exp[1] or None, "verdict": v,
                            "method": r0.method if r0 else None, "confidence": r0.confidence if r0 else None,
                            "status": r0.status if r0 else None})
        for r in links:  # false positives: linked to a decoy / other lot, or not in gold at all
            if r.status == "rejected" or any(_match(e, r) for e in expected.get(rm, ())):
                continue
            neg = any(r.ocid == n[0] and (not n[1] or str(r.part_no or "") == n[1]) for n in negatives.get(rm, ()))
            verdicts["wrong"] += 1
            details.append({"rm_id": rm, "ocid": r.ocid, "part_no": r.part_no, "verdict": "wrong",
                            "method": r.method, "confidence": r.confidence, "status": r.status,
                            "note": "pułapka (decoy/inna część)" if neg else "brak w zbiorze wzorcowym"})
    n_exp = sum(len(v) for v in expected.values())
    found = verdicts["correct"] + verdicts["uncertain"]
    linked = found + verdicts["wrong"]
    return {
        "available": True, "gold_rows": len(gold), "projects": len({g["rm_id"] for g in gold}),
        "expected_links": n_exp, "verdicts": dict(verdicts),
        "precision": round(found / linked, 3) if linked else None,
        "recall": round(found / n_exp, 3) if n_exp else None,
        "auto_precision": round(verdicts["correct"] / (verdicts["correct"] + verdicts["wrong"]), 3)
        if (verdicts["correct"] + verdicts["wrong"]) else None,
        "missing_in_bzp": sorted(missing_in_bzp), "details": details,
    }


def s1_quality(session: Session) -> dict | None:
    try:
        from riskminer.link import quality  # type: ignore
    except ImportError:
        return None
    for name in ("compute", "compute_quality", "quality_metrics", "evaluate"):
        fn = getattr(quality, name, None)
        if callable(fn):
            try:
                res = fn(session)
                return res.model_dump() if hasattr(res, "model_dump") else dict(res)
            except Exception as e:  # noqa: BLE001
                return {"error": f"{type(e).__name__}: {e}"}
    return None


# ---------------------------------------------------------------- report


def _fmt(v) -> str:
    if v is None:
        return "–"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".") if v < 1000 else f"{v:,.0f}".replace(",", " ")
    return str(v)


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(_fmt(c).replace("|", "/") for c in r) + " |" for r in rows]
    return "\n".join(out)


def build_report(session: Session) -> tuple[str, dict]:
    now = dt.datetime.now(dt.UTC).astimezone()
    counts = table_counts(session)
    ev = evaluate_links(session)
    s1q = s1_quality(session)
    L: list[str] = [
        "# Raport z testu – RISK MINER",
        "",
        f"Wygenerowano automatycznie: {now:%Y-%m-%d %H:%M %Z} (`riskminer report`). "
        "Wszystkie liczby pochodzą z bazy po przebiegu `riskminer demo`; nic nie jest wpisane ręcznie.",
        "",
        "## 1. Liczba rekordów",
        "",
        _table(["Tabela", "Rekordy"], [[k, v] for k, v in counts.items()]),
        "",
    ]
    tiers = session.execute(select(Procedure.tier, func.count()).group_by(Procedure.tier)).all()
    if tiers:
        L += ["Postępowania wg poziomu szczegółowości: " + ", ".join(f"**{t}**: {n}" for t, n in tiers) + ".", ""]

    L += ["## 2. Powiązania projekt → postępowanie vs zbiór wzorcowy", ""]
    if not ev.get("available"):
        L += ["Brak pliku `backend/tests/fixtures/gold/links_gold.csv` – sekcja pominięta.", ""]
    else:
        v = ev["verdicts"]
        L += [
            f"Zbiór wzorcowy: {ev['gold_rows']} wierszy (ręcznie zweryfikowanych), {ev['projects']} projektów, "
            f"{ev['expected_links']} oczekiwanych powiązań (projekt, OCID, część).",
            "",
            _table(["Wynik", "Liczba", "Znaczenie"], [
                ["poprawne", v.get("correct", 0), "powiązanie zgodne ze wzorcem (zatwierdzone lub pewność ≥ 0,9)"],
                ["niepewne", v.get("uncertain", 0), "zgodne, ale czeka w kolejce przeglądu eksperta"],
                ["błędne", v.get("wrong", 0), "powiązanie z pułapką / inną częścią / spoza wzorca"],
                ["brakujące", v.get("missing", 0), "oczekiwane powiązanie nie zostało znalezione"],
            ]),
            "",
            f"Precyzja: **{_fmt(ev['precision'])}** · kompletność (recall): **{_fmt(ev['recall'])}** · "
            f"precyzja powiązań automatycznych: **{_fmt(ev['auto_precision'])}**.",
            "",
        ]
        if ev["missing_in_bzp"]:
            L += ["Projekty, dla których wzorzec stwierdza brak ogłoszeń w BZP: " + ", ".join(ev["missing_in_bzp"]) + ".", ""]
        bad = [d for d in ev["details"] if d["verdict"] != "correct"]
        if bad:
            L += ["Szczegóły (wszystko poza „poprawne”):", "",
                  _table(["Projekt", "OCID", "Część", "Wynik", "Metoda", "Pewność", "Status", "Uwagi"],
                         [[d["rm_id"], d["ocid"], d["part_no"], d["verdict"], d["method"], d["confidence"],
                           d["status"], d.get("note")] for d in bad]), ""]
    if s1q and "error" not in s1q:
        keys = [("n_projects", "projekty"), ("n_gold_links", "ogłoszenia wzorcowe"), ("n_predicted", "ogłoszenia powiązane"),
                ("tp", "trafione"), ("fp", "nadmiarowe"), ("fn", "pominięte"), ("precision", "precyzja"),
                ("recall", "kompletność"), ("f1", "F1"), ("projects_fully_correct", "projekty w pełni poprawne"),
                ("projects_uncertain", "projekty niepewne (pewność < 0,95)")]
        L += ["Poziom ogłoszeń (moduł dopasowania, `riskminer.link.quality.evaluate`):", "",
              _table(["Miara", "Wartość"], [[label, s1q.get(k)] for k, label in keys if k in s1q]), ""]
        if s1q.get("decoys_linked"):
            L += ["Powiązane pułapki: " + ", ".join(f"{d['rm_id']}/{d['object_id']}" for d in s1q["decoys_linked"]), ""]
        if s1q.get("missed"):
            L += ["Pominięte: " + ", ".join(f"{d['rm_id']}/{d['object_id']}" for d in s1q["missed"][:40]), ""]
    elif s1q:
        L += [f"Moduł dopasowania S1 zgłosił błąd: {s1q['error']}", ""]

    L += ["## 3. Błędy i braki w danych organizatora", ""]
    issues = session.execute(select(DataIssue).order_by(DataIssue.kind, DataIssue.field)).scalars().all()
    dq = session.execute(select(Alert).where(Alert.kind == "data_quality")).scalars().all()
    if not issues and not dq:
        L += ["Nie wykryto (lub import nie został jeszcze uruchomiony).", ""]
    else:
        code = {p.id: p.code for p in session.execute(select(Project)).scalars()}
        by_kind = Counter(i.kind for i in issues)
        L += ["Wykryte problemy wg rodzaju: " + ", ".join(f"{k}: {n}" for k, n in by_kind.items()) + ".", ""]
        L += [_table(["Projekt", "Rodzaj", "Pole", "Stan", "Opis"],
                     [[code.get(i.project_id), i.kind, i.field, i.state, (i.message or "")[:200]] for i in issues[:80]])]
        if dq:
            L += ["", "Alerty jakości danych (monitoring):", ""]
            L += [f"- {a.message}" for a in dq]
        L += [""]

    L += ["## 4. Monitoring", ""]
    akinds = session.execute(select(Alert.kind, Alert.severity, func.count()).group_by(Alert.kind, Alert.severity)).all()
    L += [_table(["Rodzaj alertu", "Waga", "Liczba"], [list(r) for r in akinds]) if akinds else "Brak alertów.", ""]

    L += ["## 5. Analizy nowych inwestycji", ""]
    analyses = session.execute(select(Analysis).order_by(Analysis.created_at)).scalars().all()
    if not analyses:
        L += ["Brak analiz w bazie.", ""]
    for a in analyses:
        items = Counter(k for (k,) in session.execute(select(AnalysisItem.kind).where(AnalysisItem.analysis_id == a.id)))
        s = a.summary or {}
        L += [f"### {a.title}", "",
              "- pozycje analizy: " + (", ".join(f"{k}: {n}" for k, n in items.items()) or "brak"),
              f"- profil LLM: {a.llm_profile or 'reguły (bez LLM)'} · status: {a.status}"]
        for k in ("budget", "schedule", "cost_range", "time_range", "assessment", "n_neighbours", "headline"):
            if k in s:
                L += [f"- {k}: {str(s[k])[:300]}"]
        L += [""]

    L += ["## 6. Integracja ze źródłami (op_log)", ""]
    ops = session.execute(select(OpLog.connector, OpLog.operation, func.count(), func.sum(OpLog.n_results),
                                 func.count(OpLog.error), func.max(OpLog.at))
                          .group_by(OpLog.connector, OpLog.operation).order_by(OpLog.connector)).all()
    L += [_table(["Źródło", "Operacja", "Zapytania", "Wyniki", "Błędy", "Ostatnio"],
                 [[c, o, n, r, e, (m.strftime("%Y-%m-%d %H:%M") if m else None)] for c, o, n, r, e, m in ops])
          if ops else "Brak zapytań w dzienniku.", ""]

    L += ["## 7. Wywołania modeli językowych", ""]
    llm = session.execute(select(LLMCall.task, LLMCall.provider, LLMCall.data_location, func.count(),
                                 func.count().filter(LLMCall.cached.is_(True)),
                                 func.coalesce(func.sum(LLMCall.cost_usd), 0.0))
                          .group_by(LLMCall.task, LLMCall.provider, LLMCall.data_location)).all() \
        if counts.get("llm_call", 0) > 0 else []
    L += [_table(["Zadanie", "Dostawca", "Miejsce przetwarzania", "Wywołania", "Z cache", "Koszt USD"],
                 [list(r) for r in llm]) if llm else "Brak wywołań LLM (tryb reguł lub replay bez wpisów).", ""]
    summary = {"counts": counts, "linking": {k: ev.get(k) for k in ("verdicts", "precision", "recall")},
               "issues": len(issues), "analyses": len(analyses)}
    return "\n".join(L) + "\n", summary


def write_report(session: Session, out: str | Path = "docs/raport_z_testu.md",
                 copy_to: str | Path | None = "exports/przyklad/raport_z_testu.md") -> tuple[Path, dict]:
    md, summary = build_report(session)
    p = repo_path(str(out))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(md, encoding="utf-8")
    if copy_to:
        c = repo_path(str(copy_to))
        c.parent.mkdir(parents=True, exist_ok=True)
        c.write_text(md, encoding="utf-8")
    return p, summary
