"""OCR fallback for scanned PDFs: TSV parsing, status/meta/locators, re-OCR of stored scans (engine mocked)."""

from __future__ import annotations

from sqlalchemy import select

from riskminer.extract import documents, ocr
from riskminer.models import Chunk, Project
from tests.test_extract_documents import make_pdf

TSV = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
       "1\t1\t0\t0\t0\t0\t0\t0\t10\t10\t-1\t\n"
       "5\t1\t1\t1\t1\t1\t0\t0\t1\t1\t96.0\tWniosek\n"
       "5\t1\t1\t1\t1\t2\t0\t0\t1\t1\t90.0\to\n"
       "5\t1\t1\t1\t2\t1\t0\t0\t1\t1\t94.0\twydłużenie\n"
       "5\t1\t2\t1\t1\t1\t0\t0\t1\t1\t80.0\tterminu.\n")

SCAN_TEXT = ("Gmina wnioskuje o wydłużenie terminu realizacji projektu do 31.12.2025 r. Budowa sieci na obszarze "
             "zamieszkanym wymaga dodatkowych uzgodnień z mieszkańcami i modyfikowania tras.")


def test_tsv_to_text_lines_paragraphs_confidence():
    text, conf = ocr._tsv_to_text(TSV)
    assert text == "Wniosek o\nwydłużenie\n\nterminu."
    assert conf == 90.0


def _fake_engine(monkeypatch, text=SCAN_TEXT):
    monkeypatch.setattr(ocr, "available", lambda: True)
    monkeypatch.setattr(ocr, "ocr_pdf", lambda data: [ocr.OcrPage(page=1, text=text, confidence=93.5)])


def _tmp_uploads(monkeypatch, tmp_path):
    from riskminer.core import config

    monkeypatch.setattr(config.get_config(), "upload_dir", str(tmp_path))


def test_scan_without_engine_stays_marked(db, monkeypatch):
    monkeypatch.setattr(ocr, "available", lambda: False)
    units, pages, status = documents.extract_units("pdf", make_pdf([""]))
    assert status == "no_text_layer" and pages == 1


def test_scan_is_ocred_with_locator_and_meta(db, tmp_path, monkeypatch):
    _tmp_uploads(monkeypatch, tmp_path)
    _fake_engine(monkeypatch)
    pid = db.scalar(select(Project.id).limit(1))
    doc = documents.ingest_bytes(db, make_pdf([""]), "pismo_skan.pdf", project_id=pid)
    assert doc.text_status == "ocr" and "ocr_needed" not in doc.meta
    assert doc.meta["ocr"]["engine"] == "tesseract" and doc.meta["ocr"]["mean_confidence"] == 93.5
    ch = db.execute(select(Chunk).where(Chunk.document_id == doc.id)).scalars().first()
    assert ch.page == 1 and ch.locator["ocr"] is True and ch.locator["ocr_confidence"] == 93.5
    assert "wydłużenie terminu" in ch.text


def test_ocr_pending_reads_stored_scan(db, tmp_path, monkeypatch):
    _tmp_uploads(monkeypatch, tmp_path)
    monkeypatch.setattr(ocr, "available", lambda: False)
    doc = documents.ingest_bytes(db, make_pdf([""]), "skan_bez_tekstu.pdf")
    assert doc.text_status == "no_text_layer" and doc.meta["ocr_needed"]
    _fake_engine(monkeypatch)
    rows = documents.ocr_pending(db, [doc.id])
    assert rows[0]["text_status"] == "ocr" and rows[0]["chunks"] >= 1
    assert doc.text_status == "ocr" and "ocr_needed" not in doc.meta
    assert documents.ocr_pending(db, [doc.id]) == []  # idempotent
