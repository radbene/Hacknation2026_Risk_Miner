"""BZP notice `htmlBody` → numbered fields (section, label, value, offset, part_no) + canonical text.

Why a DOM parser: `htmlBody` is a flat sequence of headings – `<h3>2.4.) Identyfikator postępowania:
<span class="normal">ocds-…</span></h3>` or an `<h3>` label followed by `<p>`/bare text – and lot blocks
("<h3>Część N</h3>", "SEKCJA V … (dla części N)"). Section numbers repeat per lot and mean different things in
different notice types, so consumers match on the *label* and keep the number only as an anchor.

Canonical text: one line per field, ``"{section}.) {label}: {value}"`` (values may span lines – `<br>`/`<p>`
become newlines). `offset` is the start of `value` in canonical_text, so a quote can be located and
verified exactly (`canonical_text[offset:offset+len(value)] == value`).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from selectolax.lexbor import LexborHTMLParser as HTMLParser

PARSER_VERSION = "dom-1"

_SPLIT_RE = re.compile(r"(?=<h[123][\s>])", re.I)
_SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\)\s*(.*)$", re.S)
_SECTION_NOPAREN_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\.\s+(.*)$", re.S)
_PART_H3_RE = re.compile(r"^\s*Część\s+(\d+)\s*$", re.I)
_PART_H2_RE = re.compile(r"\(dla części\s+(\d+)\)", re.I)


@dataclass
class Field:
    section: str  # "2.4" ("" for un-numbered headings like "Kryterium 1")
    label: str
    value: str
    offset: int
    part_no: int | None
    block: str | None = None  # current "SEKCJA …" heading


@dataclass
class ParsedDom:
    title: str
    fields: list[Field]
    canonical_text: str
    n_parts_seen: int

    def sections(self) -> list[dict]:
        return [asdict(f) for f in self.fields]


def _norm_lines(text: str) -> str:
    lines = [re.sub(r"[ \t\r\f\v ]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def _prep(html: str) -> str:
    i = html.find("<main")
    if i >= 0:
        j = html.find("</main>", i)
        html = html[i: j if j > 0 else None]
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</p\s*>", "</p>\n", html, flags=re.I)
    html = re.sub(r"<p[\s>]", lambda m: "\n" + m.group(0), html, flags=re.I)
    return html


def _node_text(node) -> str:
    return node.text(deep=True, separator="") if node is not None else ""


def parse_dom(html: str | None) -> ParsedDom:
    html = _prep(html or "")
    out: list[str] = []
    pos = 0
    fields: list[Field] = []
    part: int | None = None
    block: str | None = None
    title = ""
    parts_seen: set[int] = set()

    def emit(line: str) -> int:
        nonlocal pos
        start = pos
        out.append(line)
        pos += len(line) + 1
        return start

    for seg in _SPLIT_RE.split(html):
        if not seg.strip():
            continue
        tree = HTMLParser(f"<div id='rmseg'>{seg}</div>")
        root = tree.css_first("#rmseg")
        if root is None:
            continue
        head = root.css_first("h1, h2, h3")
        if head is None:
            continue
        tag = head.tag
        # heading: label = own text nodes, value = span.normal / nested p
        label_parts: list[str] = []
        value_parts: list[str] = []
        for child in head.iter(include_text=True):
            if child.tag == "-text":
                label_parts.append(child.text_content or "")
            else:
                value_parts.append(_node_text(child))
        head_text = _norm_lines(_node_text(head))
        head.decompose()
        tail = _norm_lines(_node_text(root))

        if tag == "h1":
            title = _norm_lines(head_text)
            emit(title)
            if tail:
                emit(tail)
            continue
        if tag == "h2":
            block = re.sub(r"\s+", " ", head_text).strip()
            m = _PART_H2_RE.search(block)
            part = int(m.group(1)) if m else None
            if part:
                parts_seen.add(part)
            emit("")
            emit(block)
            if tail:
                emit(tail)
            continue
        # h3
        label_raw = _norm_lines(" ".join(label_parts)).replace("\n", " ")
        m_part = _PART_H3_RE.match(head_text)
        if m_part and not value_parts:
            part = int(m_part.group(1))
            parts_seen.add(part)
            emit(f"Część {part}")
            if tail:
                emit(tail)
            continue
        m = _SECTION_RE.match(label_raw) or _SECTION_NOPAREN_RE.match(label_raw)
        section, label = (m.group(1), m.group(2)) if m else ("", label_raw)
        label = label.strip().rstrip(":").strip()
        value = _norm_lines("\n".join([*value_parts, tail]))
        prefix = f"{section}.) {label}: " if section else f"{label}: "
        if not section and not value:
            emit(label)  # sub-heading such as "Wykonawca", "Kryterium 1"
            fields.append(Field(section="", label=label, value="", offset=pos - 1, part_no=part, block=block))
            continue
        line_start = emit(prefix + value)
        fields.append(Field(section=section, label=label, value=value, offset=line_start + len(prefix),
                            part_no=part, block=block))
    return ParsedDom(title=title, fields=fields, canonical_text="\n".join(out), n_parts_seen=len(parts_seen))
