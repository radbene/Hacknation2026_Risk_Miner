"""Rebuild links_gold.csv from the hand-verified list below + metadata from the notices22 fixture.

The *decisions* (which notice belongs to which project/lot, decoys, organizer errors) were made by hand
(S1, 2026-11-21) by reading the notices; this script only fills ids/types/contractors so the CSV is
reproducible.  Run:  uv run python tests/fixtures/gold/build_gold.py
Labels: link (must be linked) | other_part (same procedure, other lot – must NOT be linked at part level)
        | decoy (same beneficiary, similar title – must NOT be linked) | missing_in_bzp (referenced, absent).
"""
from __future__ import annotations

import csv
import json
import lzma
import re
from pathlib import Path

HERE = Path(__file__).parent
FIX = HERE.parent / "projects22" / "notices_by_nip.jsonl.xz"

L, OP, D, M = "link", "other_part", "decoy", "missing_in_bzp"
KPO_FUZZY = "KPO number absent from all notices – found by NIP + title (fuzzy)"
GOLD: dict[str, list[tuple]] = {
    # rm_id: [(notice_number, label, part_no, method_expected, note)]
    "RM-2026-001": [("2022/BZP 00058537/01", L, None, "notice_no", ""), ("2022/BZP 00115288/01", L, None, "ocid", ""),
                    ("2026/BZP 00147223/01", L, None, "ocid", "")],
    "RM-2026-002": [("2026/BZP 00089794/01", L, None, "fuzzy", KPO_FUZZY + "; CP 4.4 value 5350782,65 = KPO project value"),
                    ("2026/BZP 00143366/01", L, None, "ocid", ""),
                    ("2026/BZP 00277648/01", L, None, "ocid", ""),
                    ("2026/BZP 00285691/01", L, None, "ocid", "second ContractPerformingNotice with identical content (re-publication)"),
                    ("2023/BZP 00163924/01", D, None, "", "decoy: 'Budowa oczyszczalni ścieków w Modlikowicach' 2023 (same village)"),
                    ("2023/BZP 00260394/01", D, None, "", "decoy (oczyszczalnia Modlikowice)"),
                    ("2026/BZP 00509330/01", D, None, "", "decoy (oczyszczalnia Modlikowice)")],
    "RM-2026-003": [("2024/BZP 00349631/01", L, None, "notice_no", ""), ("2024/BZP 00418711/01", L, None, "ocid", ""),
                    ("2024/BZP 00554831/01", L, None, "ocid", ""), ("2024/BZP 00618384/01", L, None, "ocid", ""),
                    ("2026/BZP 00276065/01", L, None, "ocid", "")],
    "RM-2026-004": [("2025/BZP 00569258/01", L, None, "notice_no", ""), ("2026/BZP 00061193/01", L, None, "ocid", ""),
                    ("2026/BZP 00514691/01", L, None, "ocid", "")],
    "RM-2026-005": [("2025/BZP 00245492/01", L, None, "fuzzy", KPO_FUZZY + "; title identical"),
                    ("2025/BZP 00342797/01", L, None, "ocid", ""), ("2026/BZP 00021981/01", L, None, "ocid", "")],
    "RM-2026-006": [("2024/BZP 00067908/01", L, None, "notice_no", ""), ("2024/BZP 00245620/01", L, None, "ocid", ""),
                    ("2024/BZP 00404273/01", L, None, "ocid", ""), ("2024/BZP 00452852/01", L, None, "ocid", ""),
                    ("2024/BZP 00572624/01", L, None, "ocid", "")],
    "RM-2026-007": [("2026/BZP 00139226/01", L, None, "kpo_ref", "KPO number present in notice text"),
                    ("2026/BZP 00204390/01", L, None, "kpo_ref", ""), ("2026/BZP 00343684/01", L, None, "kpo_ref", "")],
    "RM-2026-008": [("2026/BZP 00084760/01", L, 1, "notice_no", "ContractNotice for 4 lots (4.1.9 Liczba części: 4)"),
                    ("2026/BZP 00166534/01", L, 1, "ocid", "one TenderResultNotice for all 4 lots; part 1 = Multikop 1952120,53"),
                    ("2026/BZP 00255110/01", L, 1, "lot", "part 1: NIP 7380005265, 4.4 = 8.2 (part 1) 1952120,53, 4.1 = 8.1 2026-03-12"),
                    ("2026/BZP 00255135/01", OP, 2, "", "part 2 (POTOK 7381000991, 1200000,00)"),
                    ("2026/BZP 00255161/01", OP, 3, "", "part 3 (Multikop again, 1113623,55, signed 2026-03-19)"),
                    ("2026/BZP 00255185/01", OP, 4, "", "part 4 (POTOK, 205000,02)")],
    "RM-2026-009": [("2025/BZP 00307948/01", L, 2, "notice_no", "ContractNotice with 2 lots"),
                    ("2025/BZP 00422149/01", L, 2, "ocid", "part 2 = AQUA SEEN 1132855584, 1810533,92"),
                    ("2025/BZP 00568661/01", L, 2, "lot", "part 2 by value/date/contractor. ORGANIZER INCONSISTENCY: part 2 is 'modernizacja SUW w Zakrzewie', "
                     "while the xlsx title ('Budowa sieci wodociągowej') and KPO description (network sections) match part 1"),
                    ("2025/BZP 00568576/01", OP, 1, "", "part 1 (INSBUD-KLWÓW 6010052935, 420935,30) – the water-network lot")],
    "RM-2026-010": [("2025/BZP 00211437/01", L, None, "fuzzy", KPO_FUZZY + "; title identical"),
                    ("2025/BZP 00347687/01", L, None, "ocid", ""), ("2026/BZP 00004536/01", L, None, "ocid", ""),
                    ("2024/BZP 00349336/01", D, None, "", "decoy: 'Rozbudowa sieci wodno-kanalizacyjnych na terenie gminy Grodzisko Dolne' 2024"),
                    ("2024/BZP 00407573/01", D, None, "", "decoy (2024 wod-kan)"), ("2026/BZP 00356848/01", D, None, "", "decoy (2024 wod-kan)"),
                    ("2025/BZP 00234353/01", D, None, "", "decoy: 'Rozbudowa sieci kanalizacji sanitarnej i sieci wodociągowej' 2025"),
                    ("2025/BZP 00303625/01", D, None, "", "decoy (2025 wod-kan)")],
    "RM-2026-011": [("2023/BZP 00271948/01", L, None, "notice_no", ""), ("2023/BZP 00328063/01", L, None, "ocid", ""),
                    ("2024/BZP 00016072/01", L, None, "ocid", "")],
    "RM-2026-012": [("2025/BZP 00119683/01", L, None, "notice_no", ""), ("2025/BZP 00245411/01", L, None, "ocid", ""),
                    ("2026/BZP 00025187/01", L, None, "ocid", "")],
    "RM-2026-013": [("2023/BZP 00206497/01", L, None, "notice_no", ""), ("2023/BZP 00261764/01", L, None, "ocid", ""),
                    ("2024/BZP 00637524/01", L, None, "ocid", "")],
    "RM-2026-014": [("2026/BZP 00130634/01", L, None, "notice_no", ""), ("2026/BZP 00195507/01", L, None, "ocid", ""),
                    ("2026/BZP 00331672/01", L, None, "ocid", "")],
    "RM-2026-015": [("2023/BZP 00135041/01", L, None, "notice_no", ""), ("2023/BZP 00198087/01", L, None, "ocid", ""),
                    ("2025/BZP 00228324/01", L, None, "ocid", ""), ("2025/BZP 00388035/01", L, None, "ocid", ""),
                    ("2025/BZP 00494163/01", L, None, "ocid", "")],
    "RM-2026-016": [("2022/BZP 00308854/01", L, None, "notice_no", ""), ("2022/BZP 00377000/01", L, None, "ocid", ""),
                    ("2025/BZP 00183165/01", L, None, "ocid", "")],
    "RM-2026-017": [("2025/BZP 00358528/01", L, None, "fuzzy", KPO_FUZZY + "; title identical (query by seat 'Kleszczewo', not village)"),
                    ("2026/BZP 00000230/01", L, None, "ocid", ""), ("2026/BZP 00325837/01", L, None, "ocid", "")],
    "RM-2026-018": [("2025/BZP 00620692/01", L, None, "fuzzy", KPO_FUZZY + "; title identical incl. 'etap II'"),
                    ("2026/BZP 00194260/01", L, None, "ocid", ""), ("2026/BZP 00324517/01", L, None, "ocid", ""),
                    ("2023/BZP 00207561/01", D, None, "", "decoy: earlier Baszków procedure 2023 (same contractor 6210006578)"),
                    ("2023/BZP 00363084/01", D, None, "", "decoy (Baszków 2023)"), ("2025/BZP 00018283/01", D, None, "", "decoy (Baszków 2023)")],
    "RM-2026-019": [("2024/BZP 00354928/01", L, None, "notice_no", ""), ("2024/BZP 00451447/01", L, None, "ocid", ""),
                    ("2025/BZP 00626318/01", L, None, "ocid", "")],
    "RM-2026-020": [("2025/BZP 00113651/01", L, None, "fuzzy", KPO_FUZZY + "; title identical"),
                    ("2025/BZP 00206455/01", L, None, "ocid", ""),
                    ("2025/BZP 00558908/01", L, None, "ocid", "change: art. 455 ust. 1 pkt 4 – służebność przesyłu (R03)"),
                    ("2026/BZP 00280220/01", L, None, "ocid", "change: art. 455 ust. 1 pkt 4 – warunki gruntowe (R02)"),
                    ("2026/BZP 00291637/01", L, None, "ocid", "")],
    "RM-2026-021": [("2025/BZP 00364116/01", L, None, "notice_no", ""), ("2025/BZP 00434530/01", L, None, "ocid", ""),
                    ("2026/BZP 00498398/01", L, None, "ocid", ""), ("2026/BZP 00498447/01", L, None, "ocid", "")],
    "RM-2026-022": [("2023/BZP 00110672/01", M, None, "", "ORGANIZER ERROR: xlsx BZP number not in BZP (snapshot nor API); "
                     "referenced only in 3.2.1 of the two ContractPerformingNotices"),
                    ("2023/BZP 00178669/01", M, None, "", "TenderResultNotice referenced in 4.5 / 3.1.1, absent from snapshot"),
                    ("2023/BZP 00396503/01", L, None, "xref", "AgreementUpdate (art. 455 ust. 1 pkt 3, roboty dodatkowe); contract 1 NIP 6690503086"),
                    ("2023/BZP 00580488/01", L, None, "xref", "contract 1: NIP 6690503086, 2230851,00, on time; 3.2.1 → 2023/BZP 00110672"),
                    ("2024/BZP 00621519/01", L, None, "xref", "contract 2: NIP 8570210827, 7098002,82, late; same OCID"),
                    ("2023/BZP 00232972/01", D, None, "", "decoy: 'BUDOWA SIECI WODOCIĄGOWYCH W GMINIE WOLIN,' (other OCID, 2023)"),
                    ("2023/BZP 00464559/01", D, None, "", "decoy (wodociągi Wolin 2023)")],
}
COLS = ["rm_id", "label", "notice_number", "notice_type", "object_id", "ocid", "part_no", "contractor_id",
        "contractor_id_type", "published_at", "method_expected", "note", "hand_verified"]
CONTR_RE = re.compile(r"(?:4\.3\.2|7\.3\.2)\.?\)\s*Krajowy Numer Identyfikacyjny:\s*(.*?)(?=\s+\d+(?:\.\d+)+\.?\)|\s+SEKCJA|$)")


def contractor(rec: dict, part: int | None) -> tuple[str, str]:
    ids = [m.group(1) for m in CONTR_RE.finditer(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", rec.get("htmlBody") or "")))]
    if not ids:
        ids = [c.get("contractorNationalId") for c in rec.get("contractors") or [] if c.get("contractorNationalId")]
    if not ids:
        return "", ""
    raw = ids[(part - 1) if part and len(ids) >= part else 0]
    digits = re.sub(r"\D", "", raw.split(",")[0])
    kind = "NIP" if len(digits) == 10 else ("REGON" if len(digits) in (9, 14) else "?")
    return digits, kind


def main() -> None:
    with lzma.open(FIX, "rt", encoding="utf-8") as f:
        by_no = {r["noticeNumber"]: r for r in map(json.loads, f)}
    out = []
    for rm, rows in GOLD.items():
        for no, label, part, method, note in rows:
            r = by_no.get(no)
            if r is None and label != M:
                raise SystemExit(f"{rm}: {no} not in fixture")
            cid, ckind = contractor(r, part) if r and r["noticeType"] != "ContractNotice" else ("", "")
            out.append(dict(rm_id=rm, label=label, notice_number=no, notice_type=r["noticeType"] if r else "",
                            object_id=r["objectId"] if r else "", ocid=r["tenderId"] if r else "",
                            part_no=part or "", contractor_id=cid, contractor_id_type=ckind,
                            published_at=(r["publicationDate"][:10] if r else ""), method_expected=method,
                            note=note, hand_verified="yes"))
    with (HERE / "links_gold.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} rows")


if __name__ == "__main__":
    main()
