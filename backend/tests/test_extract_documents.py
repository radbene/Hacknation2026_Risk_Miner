"""Document ingest: locators (PDF page / DOCX paragraph / sheet row), doc type & phase, fragments, search."""

from __future__ import annotations

import io

from sqlalchemy import select

from riskminer.models import Chunk, DataIssue, Event, Evidence, Project


def make_pdf(pages: list[str]) -> bytes:
    """Minimal valid PDF (Helvetica, one text line per page)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for t in pages:
        stream = f"BT /F1 11 Tf 40 780 Td ({t}) Tj ET".encode()
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream.decode()}\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {len(objs)} 0 R "
                    "/Resources << /Font << /F1 3 0 R >> >> >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out, offs = io.BytesIO(), []
    out.write(b"%PDF-1.4\n")
    for i, o in enumerate(objs, start=1):
        offs.append(out.tell())
        out.write(f"{i} 0 obj\n{o}\nendobj\n".encode())
    x = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for o in offs:
        out.write(f"{o:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode())
    return out.getvalue()


def make_docx(paras: list[str]) -> bytes:
    import docx

    d = docx.Document()
    for p in paras:
        d.add_paragraph(p)
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


def _project(db, code):
    from riskminer.ids import make_id

    pid = make_id("project", code)
    if db.get(Project, pid) is None:
        db.add(Project(id=pid, code=code, title="Test", tier="deep"))
        db.flush()
    return pid


def test_pdf_page_locator_and_fragment(db, tmp_path, monkeypatch):
    from riskminer.core import config
    from riskminer.extract.documents import ingest_bytes

    monkeypatch.setattr(config.get_config(), "upload_dir", str(tmp_path))
    pid = _project(db, "RM-TEST-DOC1")
    data = make_pdf(["Program funkcjonalno uzytkowy - wymagania ogolne.",
                     "Trasa sieci przebiega w obszarze kolizji z gazociagiem wysokiego cisnienia."])
    doc = ingest_bytes(db, data, "PFU_kanalizacja.pdf", project_id=pid)
    assert doc.doc_type == "PFU" and doc.pages == 2 and doc.text_status == "ok" and doc.phase
    chunks = db.execute(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.ord)).scalars().all()
    assert [c.page for c in chunks] == [1, 2]
    frag = db.execute(select(Event).where(Event.document_id == doc.id, Event.event_type == "doc_fragment")).scalars().all()
    r03 = [e for e in frag if e.risk_codes == ["R03"]]
    assert r03 and "kolizji" in r03[0].signal and r03[0].mitigation and r03[0].effect
    ev = db.get(Evidence, __import__("uuid").UUID(r03[0].evidence_ids[0]))
    assert ev.locator["page"] == 2 and ev.quote_verified and ev.kind == "pdf_page"
    # idempotent re-upload, search via tsvector
    assert ingest_bytes(db, data, "PFU_kanalizacja.pdf", project_id=pid).id == doc.id
    from riskminer.extract.documents import search

    hits = search(db, "gazociagiem", project_id=pid)
    assert hits and hits[0][0].page == 2


def test_docx_paragraphs_and_ppu_substitute(db, tmp_path, monkeypatch):
    from riskminer.core import config
    from riskminer.extract.documents import SUBSTITUTE_LABEL, ingest_bytes

    monkeypatch.setattr(config.get_config(), "upload_dir", str(tmp_path))
    pid = _project(db, "RM-TEST-DOC2")
    data = make_docx(["Projektowane postanowienia umowy", "§ 5 Termin wykonania",
                      "Wykonawca ustanowi służebność przesyłu na działkach prywatnych.",
                      "Zamawiający dopuszcza zmianę terminu w przypadku niekorzystnych warunków atmosferycznych."])
    doc = ingest_bytes(db, data, "zalacznik_7.docx", project_id=pid)
    assert doc.doc_type == "PPU"
    frags = db.execute(select(Event).where(Event.document_id == doc.id)).scalars().all()
    codes = {c for e in frags for c in e.risk_codes}
    assert {"R03", "R06"} <= codes
    ev = db.get(Evidence, __import__("uuid").UUID(next(e for e in frags if "R03" in e.risk_codes).evidence_ids[0]))
    assert ev.locator["paragraph"] == 3 and ev.kind == "docx_paragraph"
    issue = db.execute(select(DataIssue).where(DataIssue.project_id == pid, DataIssue.kind == "substitute")).scalars().one()
    assert SUBSTITUTE_LABEL in issue.message


def test_xlsx_csv_html_units():
    import openpyxl

    from riskminer.extract.documents import detect_kind, extract_units

    wb = openpyxl.Workbook()
    wb.active.append(["Pozycja", "Ilość"])
    wb.active.append(["Rurociąg PE 160", 120])
    b = io.BytesIO()
    wb.save(b)
    units, _, st = extract_units(detect_kind("x.xlsx", None, b.getvalue()), b.getvalue())
    assert st == "ok" and units[1].locator == {"sheet": "Sheet", "row": 2}
    units, _, _ = extract_units("csv", b"a;b\nprzedmiar;10\n")
    assert units[1].text == "przedmiar | 10"
    units, _, _ = extract_units("html", "<html><body><p>Odbiór końcowy i rozruch</p><script>x</script></body></html>".encode())
    assert units[0].text == "Odbiór końcowy i rozruch"
