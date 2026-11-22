"""OCR for scanned PDFs (no text layer): pypdfium2 renders each page, Tesseract reads it.

- Tesseract (Apache-2.0) is called as an external command from `config.ocr.command`, so the same code runs with a
  system binary (`["tesseract"]`, the Docker image installs it) or a container
  (`["docker", "run", "--rm", "-i", "riskminer-ocr"]`); no Python bindings, no AGPL/GPL tooling.
- Output is Tesseract TSV: we rebuild lines/paragraphs from it and keep the mean word confidence per page, so every
  OCR chunk says it came from OCR and how sure the engine was.
- Pages are processed locally; nothing leaves the server.
"""

from __future__ import annotations

import csv
import io
import logging
import shutil
import subprocess
from dataclasses import dataclass

from riskminer.core.config import get_config

log = logging.getLogger("riskminer.extract.ocr")


@dataclass
class OcrPage:
    page: int
    text: str
    confidence: float | None  # mean word confidence 0–100, None when no words


def available() -> bool:
    cfg = get_config().ocr
    return bool(cfg.enabled and cfg.command and shutil.which(cfg.command[0]))


def _tsv_to_text(tsv: str) -> tuple[str, float | None]:
    """Tesseract TSV → text with blank lines between paragraphs, mean confidence of recognised words."""
    lines: dict[tuple[int, int, int], list[str]] = {}
    confs: list[float] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5":
            continue
        word = (row.get("text") or "").strip()
        try:
            conf = float(row.get("conf") or -1)
        except ValueError:
            conf = -1
        if not word or conf < 0:
            continue
        confs.append(conf)
        lines.setdefault((int(row["block_num"]), int(row["par_num"]), int(row["line_num"])), []).append(word)
    out: list[str] = []
    prev: tuple[int, int] | None = None
    for (block, par, _line), words in sorted(lines.items()):
        if prev is not None and (block, par) != prev:
            out.append("")
        out.append(" ".join(words))
        prev = (block, par)
    return "\n".join(out), (round(sum(confs) / len(confs), 1) if confs else None)


def _ocr_image(png: bytes) -> tuple[str, float | None]:
    cfg = get_config().ocr
    cmd = [*cfg.command, "stdin", "stdout", "-l", cfg.lang, "--psm", "3", "tsv"]
    res = subprocess.run(cmd, input=png, capture_output=True, timeout=cfg.timeout_s, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"tesseract exit {res.returncode}: {res.stderr.decode('utf-8', 'replace')[:300]}")
    return _tsv_to_text(res.stdout.decode("utf-8", "replace"))


def ocr_pdf(data: bytes) -> list[OcrPage]:
    """Render and OCR every page (up to `ocr.max_pages`). Raises when the engine is missing or fails."""
    import pypdfium2 as pdfium

    cfg = get_config().ocr
    pdf = pdfium.PdfDocument(data)
    pages: list[OcrPage] = []
    try:
        for i in range(min(len(pdf), cfg.max_pages)):
            img = pdf[i].render(scale=cfg.dpi / 72).to_pil().convert("L")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            text, conf = _ocr_image(buf.getvalue())
            pages.append(OcrPage(page=i + 1, text=text, confidence=conf))
            log.info("OCR page %d: %d chars, confidence %s", i + 1, len(text), conf)
    finally:
        pdf.close()
    return pages
