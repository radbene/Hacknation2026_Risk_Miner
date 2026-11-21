"""Quote check: a quote must appear verbatim in the cited section / chunk.

Both sides get the same normalisation (NFKC, NBSP, typographic quotes/dashes, PDF hyphenation,
HTML <br/> line breaks, whitespace, case). An ellipsis ("…" or "...") in the quote splits it into
fragments that must appear in order.
"""

from __future__ import annotations

import re
import unicodedata

_QUOTES = str.maketrans({"„": '"', "”": '"', "“": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "‚": "'",
                         "–": "-", "—": "-", "‑": "-", "\xa0": " ", " ": " ", "­": ""})
_ELLIPSIS = re.compile(r"\s*(?:…|\.\.\.)\s*")


def normalize(text: str | None) -> str:
    s = unicodedata.normalize("NFKC", text or "").translate(_QUOTES)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)  # PDF hyphenation across lines
    s = re.sub(r"\s+", " ", s).strip().casefold()
    return s


def quote_in(quote: str | None, source: str | None) -> bool:
    """True when every ellipsis-separated fragment of `quote` occurs in `source`, in order."""
    if not quote or not source:
        return False
    src = normalize(source)
    pos = 0
    for frag in (normalize(f) for f in _ELLIPSIS.split(quote)):
        if not frag:
            continue
        i = src.find(frag, pos)
        if i < 0:
            return False
        pos = i + len(frag)
    return True


def check_quote(quote: str | None, *sources: str | None) -> bool:
    """Check against any of the cited sources (section value, chunk text, canonical text)."""
    return any(quote_in(quote, s) for s in sources)
