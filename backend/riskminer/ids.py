"""Deterministic ids (uuid5 from natural keys).

Every row id is derived from a *kind* and its natural key parts, so reruns
produce the same ids and upserts (`ON CONFLICT (id)`) are idempotent.

    make_id("notice", object_id)
    make_id("procedure", ocid)
    make_id("project", "RM-2026-001")
    make_id("project_procedure", project_id, procedure_id, part_no)
"""

from __future__ import annotations

import re
import unicodedata
import uuid

NAMESPACE = uuid.UUID("6f1c2a52-6d0e-4b0e-9a57-52a1c6a0f001")  # riskminer, fixed forever


def norm_key(part: object) -> str:
    """Normalise one natural-key part: str, NFKC, collapsed whitespace, casefold."""
    if part is None:
        return ""
    s = unicodedata.normalize("NFKC", str(part)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


def make_id(kind: str, *parts: object) -> uuid.UUID:
    key = kind + "|" + "|".join(norm_key(p) for p in parts)
    return uuid.uuid5(NAMESPACE, key)


def norm_nip(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def nip_valid(nip: str | None) -> bool:
    nip = norm_nip(nip)
    if not nip or len(nip) != 10:
        return False
    w = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    return sum(int(nip[i]) * w[i] for i in range(9)) % 11 == int(nip[9])


def regon_valid(regon: str | None) -> bool:
    r = norm_nip(regon)
    if not r or len(r) not in (9, 14):
        return False
    if len(r) == 9:
        w = (8, 9, 2, 3, 4, 5, 6, 7)
    else:
        w = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)
    c = sum(int(r[i]) * w[i] for i in range(len(w))) % 11 % 10
    return c == int(r[-1])


BZP_NUMBER_RE = re.compile(r"^\d{4}/BZP \d{8}/\d{2}$")
KPO_NUMBER_RE = re.compile(r"^KPO[A-Z]\.\d{2}\.\d{2}-IW\.(\d{2})-\d{4}/\d{2}$")
OCID_RE = re.compile(r"^ocds-148610-[0-9a-f-]{36}$")
