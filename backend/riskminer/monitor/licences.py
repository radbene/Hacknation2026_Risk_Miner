"""Licence inventory: data sources + Python (uv.lock) + npm (package-lock.json) + models.

`riskminer licences --check` writes LICENSES-THIRD-PARTY.md and exits non-zero on GPL/AGPL (copyright
transfer forbids copyleft). LGPL (psycopg) and MPL are allowed with a note: used unmodified, dynamically
linked / file-level copyleft only.
"""

from __future__ import annotations

import importlib.metadata as md
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

from riskminer.core.config import REPO_ROOT, get_config

DATA_SOURCES = [
    ("bzp", "Biuletyn Zamówień Publicznych (e-Zamówienia API)", "informacja publiczna (ustawa o dostępie do informacji publicznej, art. 1–2; ponowne wykorzystywanie – ustawa z 11.08.2021)",
     "https://ezamowienia.gov.pl"),
    ("bzp_zip", "Paczka ogłoszeń BZP 2021–2026 (lustro organizatora HackNation)", "jak BZP – informacja publiczna; kopia udostępniona przez organizatora", "https://bzp.cytr.us/paczka/risk_miner_bzp_kopia.zip"),
    ("vat_whitelist", "Biała lista podatników VAT (KAS)", "rejestr publiczny (art. 96b ustawy o VAT), API bezpłatne", "https://wl-api.mf.gov.pl"),
    ("nik", "Raporty NIK (wod-kan)", "dokumenty publiczne (informacja publiczna)", "https://www.nik.gov.pl"),
    ("ted", "TED – Tenders Electronic Daily", "dane otwarte UE (decyzja Komisji 2011/833/UE – ponowne wykorzystanie)", "https://ted.europa.eu"),
    ("krs", "KRS – API Ministerstwa Sprawiedliwości", "rejestr publiczny", "https://api-krs.ms.gov.pl"),
    ("kio", "Orzeczenia KIO (UZP)", "dokumenty publiczne", "https://orzeczenia.uzp.gov.pl"),
    ("bk2021", "Baza Konkurencyjności 2021", "informacja publiczna", "https://bazakonkurencyjnosci.funduszeeuropejskie.gov.pl"),
    ("xlsx", "Lista 22 projektów i materiały eksperckie MFiPR (docx)", "materiały organizatora udostępnione na potrzeby HackNation 2026", None),
]

MODEL_LICENCES = {
    "anthropic": "usługa API (Anthropic Commercial Terms) – brak trenowania na danych API",
    "openai": "usługa API (OpenAI Services Agreement)",
    "openai_compatible": "zależnie od modelu (Bielik: Apache-2.0)",
    "gemini": "usługa API (Google Gemini API Terms)",
    "litellm": "zależnie od wybranego dostawcy",
    "none": "brak modelu (reguły deterministyczne)",
}
OPEN_MODELS = {
    "bielik": "Apache-2.0 (SpeakLeash Bielik 11B v2.x)",
    "pllum": "Llama 3.1 Community / CC-BY-NC (zależnie od wariantu PLLuM) – sprawdzić przed wdrożeniem",
    "paraphrase-multilingual-minilm": "Apache-2.0 (sentence-transformers)",
}


@dataclass
class Lic:
    name: str
    kind: str  # data | library | model
    licence: str
    url: str | None = None
    notes: str | None = None
    version: str | None = None
    ecosystem: str | None = None
    verdict: str = "ok"  # ok | note | unknown | forbidden | optional


def classify(lic: str) -> str:
    u = (lic or "").upper()
    if not u or u in ("UNKNOWN", "NONE"):
        return "unknown"
    if "AGPL" in u or re.search(r"(?<!L)GPL", u):
        # "GPL" alone, not LGPL. Dual licences offering a permissive option are fine.
        if re.search(r"\b(MIT|BSD|APACHE|ISC)\b", u) and " OR " in u:
            return "ok"
        return "forbidden"
    if "LGPL" in u or "MPL" in u or "EPL" in u:
        return "note"
    return "ok"


def _py_licence(name: str) -> tuple[str, str | None]:
    try:
        meta = md.metadata(name)
    except md.PackageNotFoundError:
        return "", None
    expr = meta.get("License-Expression")
    if expr:
        return expr, meta.get("Home-page")
    classifiers = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    classifiers = [c for c in classifiers if c not in ("OSI Approved",)]
    raw = (meta.get("License") or "").strip()
    if classifiers:
        lic = " / ".join(dict.fromkeys(classifiers))
    elif raw and len(raw) < 80 and "\n" not in raw:
        lic = raw
    else:
        lic = raw.splitlines()[0][:80] if raw else ""
    return lic, meta.get("Home-page")


def python_deps(lock: Path = REPO_ROOT / "backend" / "uv.lock") -> list[Lic]:
    if not lock.exists():
        return []
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    out = []
    for p in data.get("package", []):
        if p["name"] == "riskminer":
            continue
        lic, url = _py_licence(p["name"])
        installed = url is not None or bool(lic)
        lic = lic or KNOWN_PY.get(p["name"], "")
        verdict = classify(lic)
        if not installed and verdict == "unknown":
            # only reachable through optional extras (embeddings → torch/CUDA, litellm); not in the default image
            out.append(Lic(name=p["name"], version=p.get("version"), kind="library", ecosystem="python",
                           licence="(opcjonalne extra – nie instalowane)", notes="optional", verdict="optional"))
            continue
        out.append(Lic(name=p["name"], version=p.get("version"), kind="library", ecosystem="python",
                       licence=lic or "UNKNOWN", url=url, verdict=verdict))
    return out


def npm_deps(lock: Path = REPO_ROOT / "frontend" / "package-lock.json") -> list[Lic]:
    if not lock.exists():
        return []
    data = json.loads(lock.read_text(encoding="utf-8"))
    out = []
    for path, p in (data.get("packages") or {}).items():
        if not path:
            continue
        name = path.split("node_modules/")[-1]
        lic = p.get("license") or ""
        if isinstance(lic, dict):
            lic = lic.get("type", "")
        out.append(Lic(name=name, version=p.get("version"), kind="library", ecosystem="npm",
                       licence=lic or "UNKNOWN", notes="dev" if p.get("dev") else None, verdict=classify(lic)))
    return out


def data_sources() -> list[Lic]:
    cfg = get_config()
    return [Lic(name=name, kind="data", licence=lic, url=url or (cfg.connectors.get(code).base_url
                                                                    if cfg.connectors.get(code) else None),
                notes=f"connector: {code}") for code, name, lic, url in DATA_SOURCES]


def models() -> list[Lic]:
    cfg = get_config()
    out = []
    for name, p in cfg.llm.profiles.items():
        low = (p.model or "").lower()
        lic = next((v for k, v in OPEN_MODELS.items() if k in low), MODEL_LICENCES.get(p.provider, "?"))
        out.append(Lic(name=f"{name}: {p.provider}/{p.model or '-'}", kind="model", licence=lic,
                       notes=f"przetwarzanie: {p.data_location}"))
    out.append(Lic(name=cfg.embeddings_model, kind="model", licence="Apache-2.0", notes="embeddingi, lokalnie (opcjonalnie)"))
    return out


# Packages whose metadata lacks a licence field (checked by hand against their repositories).
KNOWN_PY = {
    "psycopg": "LGPL-3.0-only", "psycopg-binary": "LGPL-3.0-only", "pgvector": "MIT",
    "selectolax": "MIT", "pdfplumber": "MIT", "pdfminer-six": "MIT", "pypdfium2": "Apache-2.0 OR BSD-3-Clause",
}


def inventory() -> list[Lic]:
    return data_sources() + models() + python_deps() + npm_deps()


def render_markdown(items: list[Lic]) -> str:
    py = [i for i in items if i.ecosystem == "python"]
    npm = [i for i in items if i.ecosystem == "npm"]
    bad = [i for i in items if i.verdict == "forbidden"]
    notes = [i for i in items if i.verdict == "note"]
    unknown = [i for i in items if i.verdict == "unknown"]
    optional = [i for i in items if i.verdict == "optional"]
    L = ["# Licencje stron trzecich (SBOM)", "",
         "Plik generowany: `cd backend && uv run riskminer licences --check` (źródła: `backend/uv.lock`, "
         "`frontend/package-lock.json`, `config/settings.example.yaml`). Kod projektu: **Apache-2.0**.", "",
         f"- zależności Python: {len(py)}, npm: {len(npm)}",
         f"- **GPL/AGPL: {len(bad)}**" + (" – " + ", ".join(f"{i.name} ({i.licence})" for i in bad) if bad else " ✓"),
         f"- wymagające uwagi (LGPL/MPL): {len(notes)}" + (" – " + ", ".join(f"{i.name} ({i.licence})" for i in notes) if notes else ""),
         f"- bez deklaracji licencji w metadanych: {len(unknown)}" + (" – " + ", ".join(i.name for i in unknown[:30]) if unknown else ""),
         f"- tylko w opcjonalnych dodatkach (`embeddings`, `litellm`; nie instalowane w obrazie): {len(optional)} – "
         "m.in. torch (BSD-3), sentence-transformers (Apache-2.0), transformers (Apache-2.0), biblioteki NVIDIA CUDA "
         "(licencja NVIDIA, redystrybucja dozwolona) – sprawdzić przed włączeniem",
         "",
         "**psycopg (LGPL-3.0)** – sterownik PostgreSQL używany bez modyfikacji, ładowany dynamicznie jako osobny "
         "pakiet; LGPL nie obejmuje kodu aplikacji. Nie używamy PyMuPDF (AGPL), Ghostscript ani ocrmypdf.", "",
         "## Źródła danych", "", "| Źródło | Licencja / podstawa | URL |", "|---|---|---|"]
    L += [f"| {i.name} | {i.licence} | {i.url or ''} |" for i in items if i.kind == "data"]
    L += ["", "## Modele", "", "| Profil / model | Licencja | Uwagi |", "|---|---|---|"]
    L += [f"| {i.name} | {i.licence} | {i.notes or ''} |" for i in items if i.kind == "model"]
    for title, group in (("Python (backend/uv.lock)", py), ("npm (frontend/package-lock.json)", npm)):
        L += ["", f"## {title}", "", "| Pakiet | Wersja | Licencja | Ocena |", "|---|---|---|---|"]
        L += [f"| {i.name} | {i.version or ''} | {i.licence} | {i.verdict}{' (dev)' if i.notes == 'dev' else ''} |"
              for i in sorted(group, key=lambda x: x.name.lower()) if i.verdict != "optional"]
    return "\n".join(L) + "\n"


def as_dicts(items: list[Lic]) -> list[dict]:
    return [asdict(i) for i in items]
