"""NIK lessons: public NIK reports (fetched by URL, config `connectors.nik.extra.reports`) → `lesson` rows
case → cause → signal → effect → recommendation, with R-codes and page quotes (evidence).

Rules first (finding sentences with R-signals, the nearest effect sentence, the matching recommendation
from the report's "wnioski"); optional LLM task "lessons" on the top pages, quote-checked against the page.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from riskminer.core.config import get_config
from riskminer.core.upsert import upsert_reviewable
from riskminer.extract.common import knowledge_rows, risk_names
from riskminer.extract.documents import chunk_evidence, fetch_url
from riskminer.extract.reasons import classify_signals
from riskminer.extract.validate import check_quote
from riskminer.ids import make_id
from riskminer.models import Chunk, Document, Lesson

log = logging.getLogger("riskminer.extract.lessons")
MAX_LESSONS = 30

_SENT = re.compile(r"(?<=[.;!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9„(–-])")
FINDING = re.compile(r"stwierdz\w*|nieprawidłowoś\w*|nierzeteln\w*|nie (?:zabezpieczon|uzyskan|egzekwow|naliczon|dochowan)\w*"
                     r"|opóźni\w*|przekrocz\w*|niezgodn\w*|z naruszeniem|bez (?:wymagan|pozwoleni|zgłoszeni)\w*", re.I)
EFFECT = re.compile(r"skutk\w*|w wyniku|spowodował\w*|w konsekwencji|co (?:skutkowało|spowodowało|doprowadziło)"
                    r"|wzrost\w* koszt|wydłuż\w*|utrat\w* dofinansow|zwrot\w* dotacji|kar\w* umown", re.I)
RECOMMEND = re.compile(r"NIK (?:wnosi|wnioskuje|zaleca|rekomenduje)|wnosi o|należy|powinn\w+|wniosk\w+ (?:pokontroln|o)", re.I)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(re.sub(r"\s*\n\s*", " ", text or "")) if len(s.strip()) > 25]


class LessonDraft(BaseModel):
    case: str = Field(description="Kogo/jakiej inwestycji dotyczy (gmina, zadanie)")
    cause: str
    signal: str = Field(description="Dosłowny cytat z tekstu – sygnał ostrzegawczy")
    effect: str
    recommendation: str
    risk_codes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class LessonsOut(BaseModel):
    lessons: list[LessonDraft] = Field(default_factory=list)


def _recommendations(chunks: list[Chunk], session: Session) -> list[tuple[Chunk, str, set[str]]]:
    out = []
    for ch in chunks:
        for s in sentences(ch.text):
            if RECOMMEND.search(s):
                out.append((ch, s, {h.code for h in classify_signals(s, session) if h.code.startswith("R")}))
    return out


def extract_lessons(session: Session, doc: Document, use_llm: bool = False) -> int:
    chunks = session.execute(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ord)).scalars().all()
    recs = _recommendations(chunks, session)
    tpl = {r["code"]: r for r in knowledge_rows("doc_fragments", session)}
    cands: list[tuple[float, Chunk, str, list[str], str | None]] = []
    for ch in chunks:
        sents = sentences(ch.text)
        for i, s in enumerate(sents):
            if not FINDING.search(s) or RECOMMEND.search(s):
                continue
            codes = [h.code for h in classify_signals(s, session) if h.code.startswith("R")]
            if not codes:
                continue
            eff = s if EFFECT.search(s) else next((x for x in sents[i + 1:i + 3] if EFFECT.search(x)), None)
            score = len(codes) + (1.5 if eff else 0) + (0.5 if re.search(r"\d", s) else 0)
            cands.append((score, ch, s, codes, eff))
    cands.sort(key=lambda c: -c[0])
    n, seen = 0, set()
    for score, ch, s, codes, eff in cands:
        key = s[:80]
        if key in seen or n >= MAX_LESSONS:
            continue
        seen.add(key)
        rec = next((r for r in recs if set(codes) & r[2]), None)
        evs = [chunk_evidence(session, doc, ch, s)]
        if eff and eff != s:
            evs.append(chunk_evidence(session, doc, ch, eff))
        if rec:
            evs.append(chunk_evidence(session, doc, rec[0], rec[1]))
        recommendation = rec[1] if rec else (tpl.get(codes[0], {}).get("mitigation"))
        case = re.search(r"\b(?:w|we|przez)\s+((?:Gmin\w+|Urzęd\w+|Miast\w+|Spół\w+|Zakład\w+|Przedsiębiorstw\w+)"
                         r"(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\-]+){0,3})", s)
        page = (ch.locator or {}).get("page")
        upsert_reviewable(session, Lesson, dict(
            id=make_id("lesson", doc.id, key), sector=get_config().sector, document_id=doc.id, source_kind="NIK",
            title=(f"{doc.title or 'NIK'} – str. {page}" + (f" – {case.group(1)}" if case else ""))[:300],
            cause=s, signal=s, effect=eff, recommendation=recommendation, risk_codes=codes, subsectors=[],
            method="rule", confidence=round(min(0.8, 0.3 + 0.1 * score), 2), evidence_ids=[str(e) for e in evs]))
        n += 1
    if use_llm:
        n += _llm_lessons(session, doc, [c[1] for c in cands[:6]])
    session.flush()
    return n


def _llm_lessons(session: Session, doc: Document, chunks: list[Chunk]) -> int:
    from riskminer.llm import complete, strip_personal_data, wrap_untrusted

    risks = risk_names(session)
    catalog = "\n".join(f"{c}: {r.get('name')}" for c, r in sorted(risks.items()))
    n = 0
    for ch in dict.fromkeys(chunks):
        msg = (f"Katalog ryzyk:\n{catalog}\n\nZ fragmentu raportu NIK wypisz wnioski w formacie: przypadek → przyczyna → "
               "sygnał (dosłowny cytat) → skutek → rekomendacja.\n\n"
               + wrap_untrusted(strip_personal_data(ch.text), source=doc.file_name or "raport NIK"))
        res = complete("lessons", [{"role": "user", "content": msg}], LessonsOut, prompt_version="lessons-v1")
        if res.data is None:
            return n
        for d in res.data.lessons[:3]:
            if not check_quote(d.signal, ch.text):
                continue
            ev = chunk_evidence(session, doc, ch, d.signal)
            upsert_reviewable(session, Lesson, dict(
                id=make_id("lesson", doc.id, "llm", d.signal[:80]), sector=get_config().sector, document_id=doc.id,
                source_kind="NIK", title=f"{d.case} (Wniosek modelu: {res.label})"[:300], cause=d.cause,
                signal=d.signal, effect=d.effect, recommendation=d.recommendation,
                risk_codes=[c for c in d.risk_codes if c in risks], method="llm", confidence=d.confidence,
                evidence_ids=[str(ev)]))
            n += 1
    return n


def report_urls() -> list[str]:
    nik = get_config().connectors.get("nik")
    return list(((nik.extra if nik else {}) or {}).get("reports") or [])


def import_reports(session: Session, urls: list[str] | None = None, use_llm: bool = False) -> dict[str, Any]:
    """Fetch every configured NIK report (op_log) and extract lessons. Idempotent (sha256 per document)."""
    out: dict[str, Any] = {"reports": 0, "lessons": 0, "errors": []}
    for u in urls or report_urls():
        try:
            doc = fetch_url(session, u, doc_type="NIK", source_code="nik", fragments=False)
            out["reports"] += 1
            out["lessons"] += extract_lessons(session, doc, use_llm=use_llm)
            session.commit()
        except Exception as e:  # noqa: BLE001
            session.rollback()
            out["errors"].append(f"{u}: {type(e).__name__}: {e}"[:300])
            log.warning("NIK report %s failed", u, exc_info=True)
    return out


def ingest_local_report(session: Session, path: str, url: str, use_llm: bool = False) -> tuple[uuid.UUID, int]:
    """Same as import_reports for an already-downloaded PDF (tests / offline demo)."""
    from pathlib import Path

    from riskminer.extract.documents import ingest_bytes

    doc = ingest_bytes(session, Path(path).read_bytes(), Path(path).name, url=url, doc_type="NIK", source_code="nik",
                       fragments=False)
    return doc.id, extract_lessons(session, doc, use_llm=use_llm)
