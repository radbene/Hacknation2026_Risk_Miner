"""Document ingest: PDF (text layer), DOCX, XLS/XLSX, CSV, HTML, TXT → `document` + `chunk` rows.

- every chunk keeps a locator (PDF page / DOCX paragraph / sheet+row / HTML block) and offsets;
- tsvector ('simple') for full-text search; sha256 + version per (scope, file name);
- doc type and phase from the expert tables (documents.yaml, phases.yaml);
- risk fragments in the expert format "warunek/sygnał → możliwe zdarzenie → możliwy wpływ → środki zaradcze"
  become `event_type=doc_fragment` (rules; LLM "doc_fragments" when configured, quote-checked);
- PPU/SWU-substitute rule: contract terms reconstructed from PPU/SWU when no signed contract is in the package.
Text sent to an LLM is always `strip_personal_data` + `wrap_untrusted`.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import logging
import mimetypes
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from riskminer.core.config import get_config, repo_path
from riskminer.core.evidence import add_evidence
from riskminer.core.oplog import logged_op
from riskminer.core.upsert import upsert_reviewable
from riskminer.extract.common import knowledge_rows, risk_names
from riskminer.extract.reasons import classify_signals, sentence_around
from riskminer.extract.validate import check_quote
from riskminer.ids import make_id
from riskminer.models import Chunk, Contract, DataIssue, Document, Event, ProjectProcedure

log = logging.getLogger("riskminer.extract.documents")
CHUNK_CHARS = 1200
MAX_FRAGMENTS = 80
SUBSTITUTE_LABEL = "warunki kontraktowe odtworzone; brak podpisanego egzemplarza umowy"


@dataclass
class Unit:
    text: str
    page: int | None = None
    paragraph: int | None = None
    section: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- text extraction


def _pdf_units(data: bytes) -> tuple[list[Unit], int]:
    units: list[Unit] = []
    pages = 0
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages, start=1):
                units += _split_page(page.extract_text() or "", i)
    except Exception:  # noqa: BLE001 – fall back to pypdf
        log.info("pdfplumber failed, trying pypdf", exc_info=True)
        units = []
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = len(reader.pages)
        for i, page in enumerate(reader.pages, start=1):
            units += _split_page(page.extract_text() or "", i)
    return units, pages


def _split_page(page_text: str, page: int) -> list[Unit]:
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", page_text)  # de-hyphenate line breaks
    paras = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.:;])\n(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9§•\-])", t) if p.strip()]
    return [Unit(re.sub(r"\s*\n\s*", " ", p), page=page, paragraph=j, locator={"page": page, "paragraph": j})
            for j, p in enumerate(paras, start=1)]


def _docx_units(data: bytes) -> list[Unit]:
    import docx

    d = docx.Document(io.BytesIO(data))
    units, section, n = [], None, 0
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        n += 1
        if (p.style is not None and (p.style.name or "").lower().startswith(("heading", "nagłówek"))) or re.match(r"^§\s*\d+", t):
            section = t[:32]
        units.append(Unit(t, paragraph=n, section=section, locator={"paragraph": n, "section": section}))
    for ti, table in enumerate(d.tables, start=1):
        for ri, row in enumerate(table.rows, start=1):
            cells = list(dict.fromkeys(c.text.strip() for c in row.cells if c.text.strip()))
            if cells:
                units.append(Unit(" | ".join(cells), section=f"tabela {ti}", locator={"table": ti, "row": ri}))
    return units


def _xlsx_units(data: bytes) -> list[Unit]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    units = []
    for ws in wb.worksheets:
        for ri, row in enumerate(ws.iter_rows(values_only=True), start=1):
            cells = [str(v).strip() for v in row if v not in (None, "")]
            if cells:
                units.append(Unit(" | ".join(cells), section=ws.title[:32], locator={"sheet": ws.title, "row": ri}))
    return units


def _xls_units(data: bytes) -> list[Unit]:
    import xlrd

    wb = xlrd.open_workbook(file_contents=data)
    units = []
    for sh in wb.sheets():
        for ri in range(sh.nrows):
            cells = [str(v).strip() for v in sh.row_values(ri) if str(v).strip()]
            if cells:
                units.append(Unit(" | ".join(cells), section=sh.name[:32], locator={"sheet": sh.name, "row": ri + 1}))
    return units


def _csv_units(data: bytes) -> list[Unit]:
    raw = data.decode("utf-8-sig", errors="replace")
    dialect = csv.Sniffer().sniff(raw[:4000], delimiters=",;\t|") if raw.strip() else csv.excel
    return [Unit(" | ".join(c.strip() for c in row if c.strip()), locator={"row": i})
            for i, row in enumerate(csv.reader(io.StringIO(raw), dialect), start=1) if any(c.strip() for c in row)]


def _html_units(data: bytes) -> list[Unit]:
    from selectolax.lexbor import LexborHTMLParser as HTMLParser

    tree = HTMLParser(data.decode("utf-8", errors="replace"))
    for bad in tree.css("script, style, nav, footer"):
        bad.decompose()
    units, n = [], 0
    for node in tree.css("h1, h2, h3, h4, h5, h6, p, li, td, th, pre, blockquote"):
        t = re.sub(r"\s+", " ", node.text(separator=" ")).strip()
        if len(t) < 3:
            continue
        n += 1
        units.append(Unit(t, paragraph=n, locator={"block": n, "tag": node.tag}))
    if not units:
        t = re.sub(r"\s+", " ", (tree.body.text(separator=" ") if tree.body else "")).strip()
        units = [Unit(t, paragraph=1, locator={"block": 1})] if t else []
    return units


def _txt_units(data: bytes) -> list[Unit]:
    t = data.decode("utf-8", errors="replace")
    return [Unit(p.strip(), paragraph=i, locator={"paragraph": i})
            for i, p in enumerate((p for p in re.split(r"\n\s*\n", t) if p.strip()), start=1)]


def detect_kind(file_name: str, mime: str | None, data: bytes) -> str:
    ext = Path(file_name or "").suffix.lower()
    if data[:5] == b"%PDF-" or ext == ".pdf":
        return "pdf"
    if ext == ".docx" or (data[:2] == b"PK" and b"word/" in data[:4000]):
        return "docx"
    if ext in (".xlsx", ".xlsm") or (data[:2] == b"PK" and b"xl/" in data[:4000]):
        return "xlsx"
    if ext == ".xls" or data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "xls" if ext != ".doc" else "doc"
    if ext in (".csv", ".tsv"):
        return "csv"
    if ext in (".html", ".htm") or (mime or "").startswith("text/html") or data.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
        return "html"
    return "txt"


TEXT_OK = ("ok", "ocr")  # text_status values whose chunks feed fragments/effects


def _ocr_units(data: bytes) -> tuple[list[Unit], dict[str, Any]] | None:
    """OCR fallback for a PDF without a text layer. None when OCR is off/unavailable or reads nothing."""
    from riskminer.extract import ocr

    if not ocr.available():
        return None
    try:
        pages = ocr.ocr_pdf(data)
    except Exception as e:  # noqa: BLE001 – keep the document, mark it for OCR
        log.warning("OCR failed: %s", e)
        return None
    units: list[Unit] = []
    for p in pages:
        for u in _split_page(p.text, p.page):
            u.locator.update(ocr=True, ocr_confidence=p.confidence)
            units.append(u)
    if sum(len(u.text) for u in units) <= 50:
        return None
    confs = [p.confidence for p in pages if p.confidence is not None]
    cfg = get_config().ocr
    return units, {"engine": "tesseract", "lang": cfg.lang, "dpi": cfg.dpi, "pages": len(pages),
                   "mean_confidence": round(sum(confs) / len(confs), 1) if confs else None,
                   "page_confidence": {p.page: p.confidence for p in pages}}


def extract_units(kind: str, data: bytes, meta: dict[str, Any] | None = None) -> tuple[list[Unit], int | None, str]:
    """Returns (units, pages, text_status). Scanned PDFs go through OCR (`ocr` status, details in `meta["ocr"]`)."""
    try:
        if kind == "pdf":
            units, pages = _pdf_units(data)
            if sum(len(u.text) for u in units) > 50:
                return units, pages, "ok"
            got = _ocr_units(data)
            if got is None:
                return units, pages, "no_text_layer"
            if meta is not None:
                meta["ocr"] = got[1]
            return got[0], pages, "ocr"
        fn = {"docx": _docx_units, "xlsx": _xlsx_units, "xls": _xls_units, "csv": _csv_units, "html": _html_units,
              "txt": _txt_units}.get(kind)
        if fn is None:
            return [], None, "unsupported"
        units = fn(data)
        return units, None, "ok" if units else "empty"
    except Exception as e:  # noqa: BLE001
        log.warning("text extraction failed: %s", e, exc_info=True)
        return [], None, "error"


def make_chunks(units: list[Unit]) -> list[Unit]:
    """Merge consecutive units (same page / section) up to CHUNK_CHARS; locator keeps the paragraph range."""
    out: list[Unit] = []
    cur: Unit | None = None
    for u in units:
        same = cur is not None and cur.page == u.page and cur.section == u.section and "sheet" not in u.locator
        if same and len(cur.text) + len(u.text) + 1 <= CHUNK_CHARS:
            cur.text += "\n" + u.text
            cur.locator["paragraph_to"] = u.paragraph
            continue
        if cur is not None:
            out.append(cur)
        cur = Unit(u.text, u.page, u.paragraph, u.section, {**u.locator, "paragraph_to": u.paragraph})
    if cur is not None:
        out.append(cur)
    return out


# ---------------------------------------------------------------- type & phase

DOC_TYPES: list[tuple[str, str, str]] = [  # (doc_type, regex on name+head, documents.yaml name prefix)
    ("NIK", r"najwyższ\w+ izb\w+ kontroli|wystąpieni\w+ pokontroln|informacj\w+ o wynikach kontroli|\bNIK\b", "Informacja o wynikach kontroli NIK"),
    ("KIO", r"krajow\w+ izb\w+ odwoławcz|sygn\.\s*akt:?\s*KIO|\bKIO\b", "Orzeczenie KIO"),
    ("aneks", r"\baneks\w*\s+nr|\baneks\b", "Aneks do umowy"),
    ("PPU", r"projektowan\w+ postanowie\w+ umow|wz[oó]r umowy|istotn\w+ postanowie\w+ umow|\bPPU\b|\bIPU\b", "PPU – Projektowane Postanowienia Umowy"),
    ("SWU", r"szczegól\w+ warunk\w+ umow|\bSWU\b", "SWU – Szczególne Warunki Umowy"),
    ("STWiORB", r"specyfikacj\w+ techniczn\w+ wykonania i odbioru|STWiORB|\bSST\b", "STWiORB"),
    ("PFU", r"program\w* funkcjonalno|\bPFU\b", "PFU – Program Funkcjonalno-Użytkowy"),
    ("OPZ", r"opis\w* przedmiotu zamówienia|\bOPZ\b", "OPZ – Opis Przedmiotu Zamówienia"),
    ("SWZ", r"specyfikacj\w+ warunków zamówienia|\bSWZ\b|\bSIWZ\b", "SWZ – Specyfikacja Warunków Zamówienia"),
    ("przedmiar", r"przedmiar|kosztorys", "Przedmiar robót / kosztorys ofertowy"),
    ("decyzja", r"pozwoleni\w+ na budowę|decyzj\w+ (?:o środowiskow|o pozwoleni)|warunki techniczne", "Decyzje, pozwolenia, warunki i uzgodnienia"),
    ("protokół", r"protokół (?:konieczności|odbioru|z narady)", "Dokumenty realizacyjne i odbiorowe"),
    ("umowa", r"umowa nr|zawart\w+ w dniu .{0,80} pomiędzy|\bumowa\b", "Podpisana umowa"),
    ("studium", r"studium wykonalności|analiz\w+ wariant", "Studium wykonalności"),
]
PHASE_HINT = {"NIK": "Zamknięcie i gwarancja", "KIO": "Postępowanie zakupowe", "aneks": "Realizacja",
              "protokół": "Realizacja", "umowa": "Zawarcie i uruchomienie umowy", "studium": "Planowanie",
              "decyzja": "Przygotowanie", "przedmiar": "Przygotowanie", "STWiORB": "Przygotowanie"}


def detect_doc_type(file_name: str, head: str) -> str | None:
    name = re.sub(r"[_\-.]+", " ", file_name or "")
    for dtype, rx, _ in DOC_TYPES:  # file name first – most reliable
        if re.search(rx, name, re.I):
            return dtype
    for dtype, rx, _ in DOC_TYPES:
        if re.search(rx, head[:3000], re.I):
            return dtype
    return None


def detect_phase(doc_type: str | None, session: Session | None = None) -> str | None:
    if not doc_type:
        return None
    key = doc_type.lower()
    for row in knowledge_rows("phases", session):
        if any(key in str(d).lower() for d in row.get("documents") or []):
            return row.get("phase")
    return PHASE_HINT.get(doc_type)


# ---------------------------------------------------------------- ingest


def _store(data: bytes, sha: str, file_name: str) -> Path:
    base = repo_path(get_config().upload_dir)
    path = base / sha[:2] / f"{sha}{Path(file_name or '').suffix.lower()[:8]}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return path


def ingest_bytes(session: Session, data: bytes, file_name: str, *, mime: str | None = None,
                 project_id: uuid.UUID | None = None, analysis_id: uuid.UUID | None = None,
                 procedure_id: uuid.UUID | None = None, doc_type: str | None = None, url: str | None = None,
                 source_code: str = "upload", uploaded_by: str | None = None, fragments: bool = True,
                 use_llm: bool = False) -> Document:
    sha = hashlib.sha256(data).hexdigest()
    scope = str(project_id or analysis_id or procedure_id or "global")
    doc_id = make_id("document", scope, sha)
    existing = session.get(Document, doc_id)
    if existing is not None:
        return existing
    kind = detect_kind(file_name, mime, data)
    extra_meta: dict[str, Any] = {}
    units, pages, status = extract_units(kind, data, extra_meta)
    chunks = make_chunks(units)
    head = "\n".join(u.text for u in units[:40])
    dtype = doc_type or detect_doc_type(file_name, head)
    prev = session.execute(select(func.max(Document.version)).where(
        Document.file_name == file_name, Document.project_id == project_id if project_id else Document.project_id.is_(None),
        Document.analysis_id == analysis_id if analysis_id else Document.analysis_id.is_(None))).scalar()
    path = _store(data, sha, file_name)
    title = next((u.text[:200] for u in units if len(u.text) > 10), file_name)
    doc = Document(id=doc_id, project_id=project_id, analysis_id=analysis_id, procedure_id=procedure_id,
                   doc_type=dtype, phase=detect_phase(dtype, session), title=title, url=url, file_path=str(path),
                   file_name=file_name, mime=mime or mimetypes.guess_type(file_name or "")[0], sha256=sha,
                   version=(prev or 0) + 1, pages=pages, source_code=source_code,
                   retrieved_at=dt.datetime.now(dt.UTC), uploaded_by=uploaded_by, text_status=status,
                   method="rule", status="proposed",
                   meta={"kind": kind, "n_units": len(units), "n_chunks": len(chunks),
                         "doc_type_detected": dtype if not doc_type else None,
                         **extra_meta, **({"ocr_needed": True} if status == "no_text_layer" else {})})
    session.add(doc)
    session.flush()
    _index_chunks(session, doc, chunks, status, fragments=fragments, use_llm=use_llm)
    return doc


def _index_chunks(session: Session, doc: Document, chunks: list[Unit], status: str, *, fragments: bool = True,
                  use_llm: bool = False) -> None:
    doc_id = doc.id
    for i, c in enumerate(chunks):
        session.add(Chunk(id=make_id("chunk", doc_id, i), document_id=doc_id, ord=i, page=c.page,
                          paragraph=c.paragraph, section=(c.section or None) and c.section[:32], start=0,
                          end=len(c.text), locator=c.locator, text=c.text))
    session.flush()
    session.execute(text("UPDATE chunk SET tsv = to_tsvector('simple', text) WHERE document_id = :d"), {"d": doc_id})
    if fragments and status in TEXT_OK:
        extract_fragments(session, doc, use_llm=use_llm)
        extract_document_effects(session, doc)
    apply_substitute_rule(session, doc)
    session.flush()


def ocr_pending(session: Session, doc_ids: list[uuid.UUID] | None = None, use_llm: bool = False) -> list[dict[str, Any]]:
    """Re-read stored scans (`no_text_layer`) with OCR: chunks, fragments, effects. Idempotent per document."""
    q = select(Document).where(Document.text_status == "no_text_layer")
    if doc_ids:
        q = q.where(Document.id.in_(doc_ids))
    out: list[dict[str, Any]] = []
    for doc in session.execute(q).scalars():
        data = Path(doc.file_path).read_bytes() if doc.file_path and Path(doc.file_path).exists() else None
        if data is None:
            out.append({"id": str(doc.id), "file_name": doc.file_name, "text_status": doc.text_status,
                        "error": "file missing"})
            continue
        meta: dict[str, Any] = {}
        units, _pages, status = extract_units((doc.meta or {}).get("kind") or "pdf", data, meta)
        if status != "ocr":
            out.append({"id": str(doc.id), "file_name": doc.file_name, "text_status": status,
                        "error": "OCR unavailable or empty"})
            continue
        chunks = make_chunks(units)
        session.query(Chunk).filter(Chunk.document_id == doc.id).delete()
        doc.text_status = status
        doc.meta = {**{k: v for k, v in (doc.meta or {}).items() if k != "ocr_needed"}, **meta,
                    "n_units": len(units), "n_chunks": len(chunks)}
        if not doc.title or doc.title == doc.file_name:
            doc.title = next((u.text[:200] for u in units if len(u.text) > 10), doc.file_name)
        dtype = detect_doc_type(doc.file_name or "", "\n".join(u.text for u in units[:40]))
        if dtype and not doc.doc_type:
            doc.doc_type, doc.phase = dtype, detect_phase(dtype, session)
        session.flush()
        _index_chunks(session, doc, chunks, status, use_llm=use_llm)
        out.append({"id": str(doc.id), "file_name": doc.file_name, "text_status": status, "chunks": len(chunks),
                    "mean_confidence": meta["ocr"]["mean_confidence"]})
    return out


def fetch_url(session: Session, url: str, **kw: Any) -> Document:
    """Fetch a public document by URL (logged in op_log) and ingest it."""
    import httpx

    cfg = get_config()
    with logged_op("documents", "fetch", url=url, params={"doc_type": kw.get("doc_type")}) as op:
        r = httpx.get(url, headers={"User-Agent": cfg.user_agent}, timeout=120, follow_redirects=True)
        op["status_code"], op["bytes"] = r.status_code, len(r.content)
        r.raise_for_status()
    name = Path(httpx.URL(url).path).name or "dokument"
    mime = r.headers.get("content-type", "").split(";")[0] or None
    if "." not in name and mime:
        name += mimetypes.guess_extension(mime) or ""
    return ingest_bytes(session, r.content, name, mime=mime, url=url, source_code=kw.pop("source_code", "url"), **kw)


# ---------------------------------------------------------------- fragments


class FragmentOut(BaseModel):
    risk_code: str
    signal_quote: str = Field(description="Dosłowny cytat z fragmentu (warunek/sygnał)")
    possible_event: str
    possible_impact: str
    mitigation: str
    confidence: float = Field(ge=0, le=1)


class FragmentsOut(BaseModel):
    fragments: list[FragmentOut] = Field(default_factory=list)


def _evidence_kind(doc: Document) -> str:
    k = (doc.meta or {}).get("kind")
    return {"pdf": "pdf_page", "docx": "docx_paragraph", "xlsx": "xlsx_cell", "xls": "xlsx_cell"}.get(k, "document")


def quote_locator(ch: Chunk, quote: str) -> dict[str, Any]:
    """Chunk locator narrowed to the paragraph (or row) that holds the quote, plus offsets in the chunk."""
    loc = dict(ch.locator or {})
    i = ch.text.find(quote[:80])
    if i >= 0:
        loc.update(start=i, end=i + len(quote))
        k = ch.text[:i].count("\n")
        if ch.paragraph is not None:
            loc["paragraph"] = ch.paragraph + k
        loc.pop("paragraph_to", None)
    return loc


def chunk_evidence(session: Session, doc: Document, ch: Chunk, quote: str) -> uuid.UUID:
    eid = add_evidence(session, source_code=doc.source_code or "upload", kind=_evidence_kind(doc),
                       key=(str(doc.id), ch.ord, quote[:200]), url=doc.url, retrieved_at=doc.retrieved_at,
                       locator={**quote_locator(ch, quote), "file_name": doc.file_name, "doc_type": doc.doc_type,
                                "version": doc.version}, quote=quote, document_id=doc.id, chunk_id=ch.id,
                       import_sha256=doc.sha256)
    from riskminer.models import Evidence

    ev = session.get(Evidence, eid)
    if ev is not None:
        ev.quote_verified = check_quote(quote, ch.text)
    return eid


def extract_fragments(session: Session, doc: Document, use_llm: bool = False) -> int:
    templates = {r["code"]: r for r in knowledge_rows("doc_fragments", session)}
    risks = risk_names(session)
    chunks = session.execute(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ord)).scalars().all()
    n = 0
    llm_chunks: list[Chunk] = []
    for ch in chunks:
        hits = [h for h in classify_signals(ch.text, session) if h.code.startswith("R")]
        if hits:
            llm_chunks.append(ch)
        for h in hits[:3]:
            if n >= MAX_FRAGMENTS:
                break
            quote = sentence_around(ch.text, h.start, h.end)
            tpl, risk = templates.get(h.code, {}), risks.get(h.code, {})
            _fragment_event(session, doc, ch, code=h.code, quote=quote, event=tpl.get("event") or risk.get("name"),
                            impact=risk.get("effects"), mitigation=tpl.get("mitigation"), method="rule",
                            confidence=0.4, label=None, matched=h.match)
            n += 1
    if use_llm and llm_chunks:
        n += _llm_fragments(session, doc, llm_chunks[:8])
    session.flush()
    return n


def _fragment_event(session, doc, ch, *, code, quote, event, impact, mitigation, method, confidence, label, matched=None):
    ev = chunk_evidence(session, doc, ch, quote)
    project_id = doc.project_id
    eid = make_id("event", "doc_fragment", doc.id, ch.ord, code, method)
    loc = ch.locator or {}
    where = f"str. {loc['page']}" if loc.get("page") else (f"akapit {loc['paragraph']}" if loc.get("paragraph") else
                                                          f"wiersz {loc.get('row')}")
    upsert_reviewable(session, Event, dict(
        id=eid, project_id=project_id, procedure_id=doc.procedure_id, document_id=doc.id, event_type="doc_fragment",
        risk_codes=[code], title=f"{doc.doc_type or 'Dokument'} ({where}): {code} {event or ''}".strip()[:300],
        signal=quote, cause=event, effect=impact, mitigation=mitigation, quote=quote, method=method,
        model_label=label, confidence=confidence, evidence_ids=[str(ev)], tier="deep"))
    return eid


def _llm_fragments(session: Session, doc: Document, chunks: list[Chunk]) -> int:
    from riskminer.llm import complete, strip_personal_data, wrap_untrusted

    risks = risk_names(session)
    catalog = "\n".join(f"{c}: {r.get('name')}" for c, r in sorted(risks.items()))
    n = 0
    for ch in chunks:
        msg = (f"Katalog ryzyk:\n{catalog}\n\nZ fragmentu dokumentu ({doc.doc_type or 'dokument'}) wypisz sygnały ryzyka "
               "w formacie: warunek/sygnał (dosłowny cytat) → możliwe zdarzenie → możliwy wpływ → środki zaradcze.\n\n"
               + wrap_untrusted(strip_personal_data(ch.text), source=doc.file_name or "dokument"))
        res = complete("doc_fragments", [{"role": "user", "content": msg}], FragmentsOut, prompt_version="frag-v1")
        if res.data is None:
            return n
        for f in res.data.fragments[:4]:
            if f.risk_code not in risks or not check_quote(f.signal_quote, ch.text):
                continue
            _fragment_event(session, doc, ch, code=f.risk_code, quote=f.signal_quote, event=f.possible_event,
                            impact=f.possible_impact, mitigation=f.mitigation, method="llm",
                            confidence=f.confidence, label=res.label)
            n += 1
    return n


# ---------------------------------------------------------------- realised effects (protocols, annexes)

_DATE = r"(\d{1,2})\.(\d{1,2})\.(\d{4})"
_OLD_TERM = re.compile(r"(?:dotychczasow\w*|pierwotn\w*|obecn\w*)\s+termin[^\n]{0,80}?" + _DATE, re.I)
_NEW_TERM = re.compile(r"now\w*\s+termin[^\n]{0,80}?" + _DATE, re.I)
_EXTEND = re.compile(r"(?:przedłużeni\w*|wydłużeni\w*|przesunięci\w*)\s+terminu[^.]{0,90}?\so\s+(?:okres\s+)?(\d+|jed\w+)\s+(miesi\w+|dni|tygod\w+)", re.I)
_COST = re.compile(r"(?:kwot\w*|koszt\w*|wartoś\w*|wynagrodzeni\w*)[^.\n]{0,60}?(\d{1,3}(?:[  .]\d{3})*(?:,\d{2})?)\s*zł", re.I)
_CAUSE_HEAD = re.compile(r"(?:uzasadnieni\w*|opis\s+okoliczności\w*|przyczyn\w+ zmian\w*)[^:\n]{0,60}[:\n]", re.I)
_DOC_DATE = re.compile(r"dni(?:a|u)\s+" + _DATE, re.I)
EFFECT_DOC_TYPES = {"protokół", "aneks"}


def _date(m: re.Match, off: int = 1) -> dt.date | None:
    try:
        return dt.date(int(m.group(off + 2)), int(m.group(off + 1)), int(m.group(off)))
    except ValueError:
        return None


def _pln(s: str) -> float:
    return float(s.replace(" ", "").replace(" ", "").replace(".", "").replace(",", "."))


def extract_document_effects(session: Session, doc: Document) -> uuid.UUID | None:
    """A protocol / annex states what actually happened: new deadline, extension, extra cost, and why.
    Rules only, every number quoted verbatim from the chunk it was read from → one reviewable event."""
    chunks = session.execute(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ord)).scalars().all()
    if not chunks:
        return None
    found: dict[str, tuple[Chunk, re.Match]] = {}
    for ch in chunks:
        for key, rx in (("old", _OLD_TERM), ("new", _NEW_TERM), ("extend", _EXTEND), ("cost", _COST), ("cause", _CAUSE_HEAD), ("date", _DOC_DATE)):
            if key not in found and (m := rx.search(ch.text)):
                found[key] = (ch, m)
    days: int | None = None
    parts: list[str] = []
    quotes: list[tuple[Chunk, str]] = []
    if "old" in found and "new" in found:
        a, b = _date(found["old"][1]), _date(found["new"][1])
        if a and b and b > a:
            days = (b - a).days
            parts.append(f"termin z {a:%d.%m.%Y} na {b:%d.%m.%Y} (+{days} dni)")
            quotes += [(found["old"][0], found["old"][1].group(0)), (found["new"][0], found["new"][1].group(0))]
    if days is None and "extend" in found:
        ch, m = found["extend"]
        n = 1 if m.group(1).lower().startswith("jed") else int(m.group(1))
        unit = m.group(2).lower()
        days = n * (30 if unit.startswith("miesi") else 7 if unit.startswith("tygod") else 1)
        short = "mies." if unit.startswith("miesi") else "tyg." if unit.startswith("tygod") else "dni"
        parts.append(f"termin wydłużony o {n} {short} (ok. {days} dni)")
        quotes.append((ch, m.group(0)))
    pln: float | None = None
    if "cost" in found and (doc.doc_type in EFFECT_DOC_TYPES or days is not None):
        ch, m = found["cost"]
        pln = _pln(m.group(1))
        parts.append(f"koszt {m.group(1)} zł{' brutto' if 'brutto' in ch.text[m.end():m.end() + 12].lower() else ''}")
        quotes.append((ch, m.group(0)))
    if not parts or (doc.doc_type not in EFFECT_DOC_TYPES and days is None):
        return None
    cause, codes = None, []
    if "cause" in found:
        ch, m = found["cause"]
        tail = ch.text[m.end():]
        cut = tail[:400]
        end = max(cut.rfind("\n"), cut.rfind(". ") + 1)
        cause = (cut[:end] if end > 80 else cut).strip(" \n,;–-")
        if cause:
            quotes.insert(0, (ch, cause))
            codes = [h.code for h in classify_signals(ch.text[m.start():m.end() + 1200], session) if h.code.startswith("R")][:3]
    evidence = [str(chunk_evidence(session, doc, ch, q)) for ch, q in quotes if q]
    when = _date(found["date"][1]) if "date" in found else None
    eid = make_id("event", "doc_effect", doc.id)
    kind = "change_deadline" if days is not None else "change_value"
    label = {"protokół": "Protokół konieczności", "aneks": "Aneks"}.get(doc.doc_type or "", "Dokument")
    upsert_reviewable(session, Event, dict(
        id=eid, project_id=doc.project_id, procedure_id=doc.procedure_id, document_id=doc.id, event_type=kind,
        event_date=when, risk_codes=codes, title=f"{label}: {', '.join(parts)}"[:300], cause=cause, effect="; ".join(parts),
        effect_days=days, effect_pln=pln, quote=cause or quotes[0][1], method="rule", confidence=0.7,
        evidence_ids=evidence, tier="deep"))
    session.flush()
    return eid


# ---------------------------------------------------------------- PPU/SWU substitute rule


def apply_substitute_rule(session: Session, doc: Document) -> None:
    """Signed contract missing but PPU/SWU present → contract terms reconstructed from PPU/SWU (labelled)."""
    if not doc.project_id:
        return
    types = set(session.execute(select(Document.doc_type).where(Document.project_id == doc.project_id)).scalars())
    issue_id = make_id("data_issue", doc.project_id, "substitute", "umowa")
    if "umowa" in types or not (types & {"PPU", "SWU"}):
        existing = session.get(DataIssue, issue_id)
        if existing is not None and existing.status == "proposed" and "umowa" in types:
            existing.state, existing.message = "potwierdzone", "Podpisana umowa jest w paczce dokumentów."
        return
    src = "PPU" if "PPU" in types else "SWU"
    upsert_reviewable(session, DataIssue, dict(
        id=issue_id, project_id=doc.project_id, kind="substitute", field="umowa", state="nie_ma_w_paczce",
        message=f"{SUBSTITUTE_LABEL} (źródło: {src} + ogłoszenie o wyniku postępowania).",
        what_to_add="Podpisana umowa z załącznikami i aneksami (BIP / rejestr umów / wniosek o informację publiczną).",
        impact="Warunki umowy (terminy, kary, klauzule zmian) przyjęto z projektu umowy – mogły zostać zmienione "
               "przed podpisaniem; wnioski o klauzulach mają obniżoną pewność.",
        method="rule", confidence=0.7))
    pids = session.execute(select(ProjectProcedure.procedure_id).where(ProjectProcedure.project_id == doc.project_id)).scalars().all()
    for c in session.execute(select(Contract).where(Contract.procedure_id.in_(pids))).scalars() if pids else []:
        if c.status == "proposed" and not c.terms_source:
            c.terms_source = src
            c.meta = {**(c.meta or {}), "terms_label": SUBSTITUTE_LABEL}


# ---------------------------------------------------------------- search


def search(session: Session, q: str, project_id: uuid.UUID | None = None, limit: int = 20):
    sql = """
      SELECT c.id, ts_rank(c.tsv, query) AS score,
             ts_headline('simple', c.text, query, 'MaxFragments=2, MaxWords=25, MinWords=8') AS hl
      FROM chunk c JOIN document d ON d.id = c.document_id, websearch_to_tsquery('simple', :q) query
      WHERE c.tsv @@ query AND (CAST(:p AS uuid) IS NULL OR d.project_id = CAST(:p AS uuid))
      ORDER BY score DESC LIMIT :n"""
    rows = session.execute(text(sql), {"q": q, "p": str(project_id) if project_id else None, "n": limit}).all()
    return [(session.get(Chunk, r.id), float(r.score), r.hl) for r in rows]
