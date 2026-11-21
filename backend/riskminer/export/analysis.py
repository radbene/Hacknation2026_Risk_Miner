"""Analysis record exports: JSON (full), CSV (one row per item), DOCX ("Karta analizy inwestycji")."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from riskminer.schemas.analysis import AnalysisOut

LABEL_PL = {"dane_zrodlowe": "Dane źródłowe", "obliczenia": "Obliczenia", "wniosek_modelu": "Wniosek modelu"}
KIND_PL = {"neighbour": "Podobna inwestycja", "range": "Zakres", "assessment": "Ocena", "flag": "Czerwona flaga",
           "action": "Działanie / klauzula", "clause": "Klauzula", "lesson": "Lekcja", "checklist": "Lista kontrolna"}


def to_json(a: AnalysisOut) -> bytes:
    return a.model_dump_json(indent=1).encode("utf-8")


def to_csv(a: AnalysisOut) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["analysis_id", "kind", "ord", "label", "title", "status", "excluded", "risk_codes", "ref_project_id", "payload"])
    for i in a.items:
        w.writerow([a.id, i.kind, i.ord, i.label.value if hasattr(i.label, "value") else i.label, i.title, i.status.value,
                    i.excluded, " ".join(i.risk_codes), i.ref_project_id or "", json.dumps(i.payload, ensure_ascii=False)])
    return buf.getvalue().encode("utf-8")


def _v(x: Any) -> str:
    if x is None:
        return "–"
    if isinstance(x, float):
        return f"{x:,.2f}".replace(",", " ").replace(".", ",")
    return str(x)


def _fv(f: dict, k: str) -> Any:
    x = f.get(k)
    return x.get("value") if isinstance(x, dict) else x


def to_docx(a: AnalysisOut) -> bytes:
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.styles["Normal"].font.size = Pt(10)
    doc.add_heading(f"Karta analizy inwestycji: {a.title}", 0)
    doc.add_paragraph(f"Wersja {a.version} · status: {a.status.value} · autor: {a.created_by or '–'} · "
                      f"{a.created_at:%Y-%m-%d %H:%M}" if a.created_at else "")
    doc.add_paragraph("Każdy blok jest oznaczony: [Dane źródłowe] – fakty ze źródeł, [Obliczenia] – wyliczenia z bazy "
                      "doświadczeń (z liczebnością n i wzorem), [Wniosek modelu] – tekst wygenerowany przez model językowy, "
                      "wymaga weryfikacji eksperta.")
    doc.add_heading("1. Cechy inwestycji", 1)
    t = doc.add_table(rows=1, cols=3)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text, t.rows[0].cells[2].text = "Cecha", "Wartość", "Źródło / cytat"
    for k, v in (a.features or {}).items():
        if k in ("cues", "extra") or not isinstance(v, dict):
            continue
        r = t.add_row().cells
        r[0].text, r[1].text = k, _v(v.get("value")) + (f" {v['unit']}" if v.get("unit") else "")
        r[2].text = f"{v.get('source') or ''}: {v.get('quote') or ''}"[:300]
    s = a.summary or {}
    doc.add_heading("2. Podsumowanie [Obliczenia]", 1)
    pl = s.get("p_late") or {}
    for line in (
        f"Baza doświadczeń: {s.get('n_cases')} przypadków {s.get('cases_by_tier')}; sąsiadów: {s.get('n_neighbours')}.",
        f"P(opóźnienie) = {_v(pl.get('estimate'))} (n={pl.get('n')}, poziom: {pl.get('fallback_level')}, "
        f"95% CI {_v(pl.get('ci_low'))}–{_v(pl.get('ci_high'))}).",
        f"Opóźnienie [dni]: P50 {_v((s.get('delay_days') or {}).get('p50'))}, P80 {_v((s.get('delay_days') or {}).get('p80'))}.",
        f"Wypłata / wartość umowy: P50 {_v((s.get('paid_ratio') or {}).get('p50'))}, P80 {_v((s.get('paid_ratio') or {}).get('p80'))}.",
        f"Flagi: {s.get('n_flags')} (wysokie: {s.get('flags_high')}); kategorie ryzyka: {', '.join(s.get('risk_codes') or [])}.",
    ):
        doc.add_paragraph(line, style="List Bullet")
    sections = [("flag", "3. Czerwone flagi"), ("assessment", "4. Budżet i harmonogram"), ("range", "5. Zakresy z bazy doświadczeń"),
                ("neighbour", "6. Podobne inwestycje (z wyjaśnieniem podobieństwa)"), ("action", "7. Działania i klauzule")]
    for kind, title in sections:
        items = [i for i in a.items if i.kind == kind and not i.excluded and i.status.value != "rejected"]
        if not items:
            continue
        doc.add_heading(title, 1)
        for i in items:
            label = LABEL_PL.get(getattr(i.label, "value", i.label), str(i.label))
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(f"[{label}] ").italic = True
            p.add_run(i.title or "").bold = True
            pay = i.payload or {}
            if kind == "flag":
                doc.add_paragraph(f"{pay.get('why') or ''} (waga: {pay.get('severity')}, oś: {pay.get('axis')}"
                                  + (f", n={pay.get('n')}" if pay.get("n") else "") + ")")
                if pay.get("quote"):
                    doc.add_paragraph(f"„{pay['quote']}”")
            elif kind == "neighbour":
                comps = ", ".join(f"{b.get('label')} {_v(b.get('similarity'))}" for b in pay.get("breakdown") or [])
                o = pay.get("outcome") or {}
                doc.add_paragraph(f"podobieństwo {_v(pay.get('score'))}: {comps}. Wynik: opóźnienie {_v(o.get('delay_days'))} dni, "
                                  f"zmian {_v(o.get('n_changes'))}, wypłata/umowa {_v(o.get('paid_ratio'))}.")
            elif kind in ("range", "assessment"):
                keys = [k for k in ("n", "estimate", "p50", "p80", "p95", "percentile", "position", "fallback_level") if pay.get(k) is not None]
                doc.add_paragraph(", ".join(f"{k}={_v(pay.get(k))}" for k in keys))
                if pay.get("formula"):
                    doc.add_paragraph(f"Wzór: {pay['formula']}")
            elif kind == "action":
                if pay.get("summary"):
                    doc.add_paragraph(pay["summary"])
                    for x in pay.get("top_actions") or []:
                        doc.add_paragraph(x, style="List Number")
                for c in pay.get("clauses") or []:
                    doc.add_paragraph(f"{c.get('title')} ({c.get('legal_basis')}): {c.get('text')}")
                for les in pay.get("lessons") or []:
                    doc.add_paragraph(f"Lekcja ({les.get('source_kind')}): {les.get('title')} – {les.get('recommendation') or ''}")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
