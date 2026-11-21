"""`riskminer knowledge import <docx>...` – turn the MFiPR expert docx files into knowledge/<sector>/*.yaml.

Tables are recognised by their header row (not by position), so a new edition of the docx – or a docx for
another sector with the same table headers – imports without code changes. Output YAML is expert-editable
and versioned in the DB by the knowledge router (S5).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Any

import docx
import yaml

R_RE = re.compile(r"^(R\d{2})\s+(.*)$", re.S)


def _clean(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s.replace("\xa0", " ")).strip()


def _split_head(s: str) -> tuple[str, str]:
    """'Planowanie\\nOkreślenie potrzeby…' → ('Planowanie', 'Określenie potrzeby…')."""
    parts = [p.strip() for p in s.split("\n") if p.strip()]
    return (parts[0], " ".join(parts[1:])) if parts else ("", "")


def _rows(table) -> list[list[str]]:
    return [[c.text for c in r.cells] for r in table.rows]


def _semis(s: str) -> list[str]:
    return [x.strip() for x in re.split(r";\s*", _clean(s)) if x.strip()]


def parse_porady_docx(path: Path) -> dict[str, Any]:
    d = docx.Document(str(path))
    out: dict[str, Any] = {}
    boxes: list[str] = []
    for t in d.tables:
        rows = _rows(t)
        head = [_clean(h).lower() for h in rows[0]]
        if len(rows) == 1 and len(rows[0]) == 1:
            boxes.append(_clean(rows[0][0]))
            continue
        body = rows[1:]
        if head[:2] == ["faza i zakres", "typowe dokumenty powstające lub aktualizowane"]:
            out["phases"] = [
                {"order": i + 1, "phase": _split_head(r[0])[0], "scope": _split_head(r[0])[1], "documents": _semis(r[1])}
                for i, r in enumerate(body)
            ]
        elif head[:2] == ["podsektor", "zakres"]:
            out["subsectors"] = [{"name": _clean(r[0]), "scope": _clean(r[1])} for r in body]
        elif head[:2] == ["źródło", "znaczenie dla pakietu"]:
            out["sources"] = [{"name": _clean(r[0]), "meaning": _clean(r[1])} for r in body]
        elif head[:2] == ["dokument", "czym jest i co zawiera"]:
            group = "postepowanie" if "postepowanie" not in {x.get("group") for x in out.get("documents", [])} else "umowa"
            out.setdefault("documents", []).extend(
                {"name": _clean(r[0]), "description": _clean(r[1]), "group": group} for r in body)
        elif head[:2] == ["materiał", "czym jest i co może potwierdzać"]:
            out.setdefault("documents", []).extend(
                {"name": _clean(r[0]), "description": _clean(r[1]), "group": "zewnetrzne"} for r in body)
        elif head[:2] == ["zdarzenie", "źródło w danych publicznych"]:
            out["event_sources"] = [{"event": _clean(r[0]), "sources": _semis(r[1].replace(",", ";"))} for r in body]
        elif head[:2] == ["podstawa", "znaczenie"]:
            out["art455"] = [{"basis": _clean(r[0]), "meaning": _clean(r[1])} for r in body]
        elif head[:2] == ["ryzyko", "efekty"]:
            risks = []
            for r in body:
                m = R_RE.match(_clean(r[0]))
                if m:
                    risks.append({"code": m.group(1), "name": _clean(m.group(2)), "effects": _clean(r[1])})
            out["risks"] = risks
        elif head[:2] == ["mechanika", "porada"]:
            out["porady"] = [{"mechanic": _clean(r[0]), "advice": _clean(r[1])} for r in body]
    out["texts"] = [{"id": f"box_{i + 1}", "text": b} for i, b in enumerate(boxes)]
    return out


CHECK_RE = re.compile(r"^(.*?)\s*\(([\d.;–\- ]+)\)\s*$")


def parse_checklist_docx(path: Path) -> dict[str, Any]:
    """Expert guide (wodociąg): the 9-point summary checklist + section headings."""
    d = docx.Document(str(path))
    items, sections, in_summary = [], [], False
    for p in d.paragraphs:
        txt = _clean(p.text)
        if not txt:
            continue
        if p.style.name.startswith("Heading"):
            in_summary = "checklista" in txt.lower()
            sections.append({"level": int(p.style.name[-1]) if p.style.name[-1].isdigit() else 1, "title": txt})
            continue
        if in_summary and p.style.name == "List Paragraph":
            m = CHECK_RE.match(txt)
            items.append({"no": len(items) + 1, "item": m.group(1) if m else txt,
                          "guide_sections": m.group(2).strip() if m else None})
    title = _clean(d.paragraphs[0].text) if d.paragraphs else path.stem
    return {"checklist_title": title, "checklist": items, "guide_sections": sections}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_docx(files: list[Path], out_dir: Path, sector: str = "wodkan") -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables: dict[str, Any] = {}
    manifest_files = []
    for f in files:
        d = docx.Document(str(f))
        has_tables = len(d.tables) > 0
        parsed = parse_porady_docx(f) if has_tables else parse_checklist_docx(f)
        for k, v in parsed.items():
            tables[k] = v
        manifest_files.append({"file": f.name, "sha256": sha256(f), "tables": sorted(parsed)})
    header = (f"# GENERATED by `riskminer knowledge import` from the MFiPR expert docx – {dt.date.today()}.\n"
              "# Expert-editable: edit here or in the UI (Wiedza ekspercka); the DB keeps every version.\n")
    counts = {}
    for name, rows in tables.items():
        if name in ("checklist_title",):
            continue
        (out_dir / f"{name}.yaml").write_text(
            header + yaml.safe_dump({"sector": sector, "name": name, "rows": rows}, allow_unicode=True,
                                    sort_keys=False, width=120), encoding="utf-8")
        counts[name] = len(rows) if isinstance(rows, list) else 1
    (out_dir / "manifest.yaml").write_text(header + yaml.safe_dump(
        {"sector": sector, "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
         "checklist_title": tables.get("checklist_title"), "sources": manifest_files, "tables": counts},
        allow_unicode=True, sort_keys=False), encoding="utf-8")
    return counts
