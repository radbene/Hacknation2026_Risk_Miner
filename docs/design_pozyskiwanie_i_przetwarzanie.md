# RISK MINER — how data acquisition and processing work

Status: design as of 2026-11-21, about 13:30. Facts marked **[verified]** were checked today with read-only queries against the organizer mirror and public APIs. Facts marked **[to check]** are hypotheses we confirm during implementation or with the mentors.

---

## 0. Overview

```
 ┌──────────────┐   ┌──────────────────────┐   ┌──────────────────────────┐
 │ INPUTS       │   │ CONNECTORS           │   │ RAW STORE                │
 │ xlsx (22)    │──▶│ files (xlsx/csv/pdf/ │──▶│ every response/file as-is│
 │ PDF/DOCX     │   │  docx), bzp (API),   │   │ + sha256, URL,           │
 │ expert docx  │   │  bzp_zip, vat, ted,  │   │ retrieved_at, retrieved_ │
 │ new-project  │   │  nik, web_doc, krs,  │   │ from, op_log             │
 │ description  │   │  kio, bk2021 …       │   └────────────┬─────────────┘
 └──────────────┘   └──────────────────────┘                │
                                                             ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ PARSING & NORMALISATION                                                │
 │ notice DOM → (section, label, value, offset, part); identifiers        │
 │ (NIP/REGON/BZP/OCID/KPO/TED/TERYT); amounts (net/gross/unknown); dates │
 │ documents → pages/paragraphs → chunks                                  │
 └───────────────────────────────┬────────────────────────────────────────┘
                                 ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ LINKING  project ↔ procedure ↔ notices ↔ contract(s) ↔ changes         │
 │ 1) keys (KPO no. in the notice, BZP no., OCID+NIP, cross-references)   │
 │ 2) candidates with a score and an explanation when there is no key     │
 └───────────────────────────────┬────────────────────────────────────────┘
                                 ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ EVENT & RISK EXTRACTION                                                │
 │ rules on structured fields + causes (rules + LLM) + document fragments │
 │ → R01–R15, cause, effect (days/PLN), mitigation, QUOTE                 │
 └───────────────────────────────┬────────────────────────────────────────┘
                                 ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ CASE BASE (PostgreSQL) — every item: evidence + status (proposed →     │
 │ approved/edited/rejected) + history → expert panel, analysis, export   │
 └────────────────────────────────────────────────────────────────────────┘
```

Rules that apply at every stage:

1. **Nothing without a source.** Every fact, link, event and calculation has an `evidence` record:
   - source and permanent URL;
   - `retrieved_from` (where we actually fetched it, e.g. the mirror);
   - `retrieved_at`;
   - a locator: notice section / PDF page / DOCX paragraph / xlsx sheet-row-column;
   - a verbatim quote.

   A calculation stores, instead of a quote, the ids of its input evidence and its formula.
2. **Everything the machine produces is "proposed".** Only the expert approves, edits or rejects. Links with a key match (confidence 1.0) can be confirmed in bulk with one click, but they still start as proposed.
3. **Idempotency.** Record ids are uuid5 built from natural keys (e.g. `objectId` of a notice, OCID, `RM-id + OCID + part`). Writes use `INSERT … ON CONFLICT`.
   - A second run adds no duplicates.
   - Rows the expert has reviewed are never overwritten. A rerun only proposes a diff.
4. **Everything is logged.** `op_log` records every query (URL, parameters, HTTP status, record count, duration), import, LLM call (model, tokens, cost) and export.
5. **Data minimisation.** For contractors who are natural persons (sole traders), the UI masks the name by default. From the VAT white list we do not store bank accounts or representatives.

---

## 1. Data sources

| Source | Access | What we take | Tier | Status |
|---|---|---|---|---|
| Organizer xlsx `Risk_Miner_dane_projekty.xlsx` | file | 22 projects: RM-id, beneficiary NIP, name, voivodeship/TERYT, title, record scope (whole / lot N), BZP or KPO number, notes (KPO value, grant, description) | P0 | [verified] |
| Expert materials (2 × docx) | file | R01–R15 catalog, event → source table, art. 455 bases, 6 subsectors, phases and documents, tips, 9-point water-supply checklist | P0 | [verified] |
| **BZP — organizer mirror** `https://bzp.cytr.us/mo-board/api/v1/notice` | REST, no key, no limit | Notices of 4 types with full `htmlBody` | P0 | [verified] |
| **BZP — snapshot** `risk_miner_bzp_kopia.zip` (149 MB) | one download | Same notices offline, used for the auto tier and resilience | P0 | approved for download |
| BZP — official API `https://ezamowienia.gov.pl/mo-board/api/v1/notice` | REST, 30 requests/min/IP | Fallback when the mirror is down; permanent links | P0 | [verified] |
| **Biała lista VAT** `https://wl-api.mf.gov.pl/api/search/nip/{nip}?date=…` | REST, no key, daily limits | Name, REGON, KRS, VAT status of beneficiaries and contractors | P0 | [verified] |
| **NIK** — wod-kan audit reports (PDF) | fetch by URL | Sector lessons: case → cause → signal → effect → recommendation | P0 (1–2 reports) | [to check] which reports |
| Uploaded documents (SWZ, PFU, OPZ, PPU, contracts, annexes, protocols) | upload / URL | Risk fragments with page or paragraph | P0 | — |
| TED API v3 `POST https://api.ted.europa.eu/v3/notices/search` | REST, no key | Notices for above-threshold procedures; cross-link to TED numbers found in BZP | P1 | [verified]; returns nothing for national procedures |
| KRS API | REST | Status and data of contractor companies | P1 | [to check] |
| KIO `orzeczenia.uzp.gov.pl` | HTML form | Appeal rulings (event "Odwołanie do KIO") | P1 | [verified] HTML page |
| Baza Konkurencyjności 2021 | SPA over a JSON API | Below-threshold procedures under the competitiveness rule | P1 | [verified] the `/api/announcements/search` route exists, parameters still to find |
| KPOŚK/AKPOŚK, BIP, web search | file/URL | Agglomeration context, BIP documents | P2 | [to check] |
| Purchase platforms (platformazakupowa.pl etc.) | — | SWZ/PFU/PPU | — | **[verified] they block anonymous access (SSO, HTTP 429), so no automatic download.** Documents come by upload or URL |

---

## 2. Stage 1 — importing the organizer file

**Input:** `.xlsx`, `.xls` or `.csv`. The organizer's layout (sheet "Projekty" plus sheet "Opis kolumn") is the default mapping profile. For any other layout, the mapping is set in a form (P2).

**Steps:**

1. **Read and record the source.** Store the file's sha256 and import time, and give each cell a locator `sheet!row:column`. Every project attribute gets evidence pointing at its cell.
2. **Validate identifiers.**

   | Identifier | Check | Result for the 22 rows |
   |---|---|---|
   | NIP | 10 digits, weighted checksum (6,5,7,2,3,4,5,6,7) | 22/22 OK [verified] |
   | REGON | 9 or 14 digits, checksum | (from BZP / VAT list) |
   | BZP number | `^\d{4}/BZP \d{8}/\d{2}$`; normalise spaces and case | 15 rows |
   | KPO number | `^KPOD\.\d{2}\.\d{2}-IW\.\d{2}-\d{4}/\d{2}$` | 7 rows |
   | TERYT ↔ voivodeship | Code table | 22/22 consistent [verified] |
   | KPO `IW.nn` ↔ voivodeship | Hypothesis: nn = 12 + TERYT/2 | 7/7 consistent [to check with mentors] |
   | OCID | `^ocds-148610-[0-9a-f-]{36}$` | (from BZP) |

3. **Parse the free-text note** ("Adnotacja instytucji") with regexes:
   - programme (KPO B3.1.1 / PROW 2014–2020);
   - total project value;
   - grant amount;
   - description (in quotes).

   These amounts get `vat_basis = unknown`. **They are never compared directly with contract amounts.**
4. **Read the record scope.** "całe postępowanie" means whole procedure; "część N" sets `part_no = N` and limits linking to that lot.
5. **Store the data-quality issues** (checksum error, inconsistency, missing value) in the data-quality report as items to verify.

**Output:** `project` and `entity` (beneficiary) records with evidence, plus a list of issues.

---

## 3. Stage 2 — fetching notices from BZP

### 3.1 API behaviour [verified]

- **Endpoint:** `GET {BZP_API_BASE}/mo-board/api/v1/notice`, where `BZP_API_BASE` comes from config (mirror or official).
- **Required parameters:** `NoticeType`, `PublicationDateFrom`, `PublicationDateTo`.
- **Paging:** `PageSize` up to 500. Get the next page with `SearchAfter=<objectId of the last record>`. Page numbers are ignored.
- **Working filters:** `NoticeNumber` (with dates), `OrganizationName` (substring match, e.g. "Oława" → "Gmina Oława", "Gmina Miasto Oława"), `CpvCode`, `OrderType`.
- **Ignored filters — they return everything:** `TenderId`, `OrganizationNationalId`, `OrganizationId`, `BzpNumber`.
- **Notice types we use:**

  | Type | Meaning |
  |---|---|
  | `ContractNotice` | contract notice |
  | `TenderResultNotice` | result of the procedure |
  | `AgreementUpdateNotice` | contract change (`ContractModificationNotice` does not exist) |
  | `ContractPerformingNotice` | contract performance |

  Also `NoticeUpdateNotice`, a change to a notice, for corrections.
- **Fields of a record:**

  ```
  objectId, noticeNumber, bzpNumber, noticeType, publicationDate, tenderId (OCID),
  organizationName, organizationNationalId (NIP), organizationProvince (PLxx), organizationCity,
  orderObject, cpvCode, orderType, procedureResult, isTenderAmountBelowEU,
  contractors[{contractorName, contractorNationalId, contractorCity, …}], htmlBody
  ```

- **The mirror returns HTTP 403 for Python's default User-Agent.** The client always sends its own header, `RiskMiner-prototype/x.y`.
- **Permanent evidence links:**
  - page: `https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/<objectId>`;
  - PDF: `https://ezamowienia.gov.pl/mo-board/api/v1/Board/GetNoticePdfById?noticeId=<objectId>`.

  The mirror works only during the hackathon, so it goes into `retrieved_from`.

### 3.2 Connector (`connectors/bzp.py`)

- Adapted from the prep `bzp_fetch.py` (`_get`, `fetch_day`).
- **Retries:** after HTTP 403 or 429 it waits 65 s; for 5xx and timeouts it backs off exponentially.
- **Minimum interval between calls** is configurable: 0 for the mirror, 2.1 s for the official API.
- **Raw store:** every record is kept unchanged, keyed by `objectId`, deduplicated, with `retrieved_at` and `retrieved_from`.
- **op_log:** one entry per query: URL, parameters, status, record count, duration.

### 3.3 Fetching for one project (deep tier)

1. **Name variants.** Built from the beneficiary's name and seat: "Gmina Oława", "Oława", and the name without "Urząd Miejski"/"Gmina". [verified] For Kleszczewo we have to search by the seat ("Kleszczewo"), not the village ("Tanibórz").
2. **Fetch all four types** with each name variant in the window [publication date − 2 years, today]. Without a BZP number the window is 2021 → today.
3. **Filter locally** by `organizationNationalId == NIP`. [verified] Required, because "Kamionka" also returns other gminas.
4. **Group by `tenderId` (OCID)** and follow the cross-references (section 5).

### 3.4 Bulk harvest (auto tier — "baza stale zasilana")

- **Source:** the zip snapshot loaded into the same raw store. The live-API path stays available for the jury's integration test.
- **Wod-kan filter:**
  - CPV: 45231300, 45232400, 45232410, 45232420/421, 45232430, 45232440, 45232150, 45232130, 45252100/126/127 and related codes;
  - plus title keywords: wodociąg, kanalizac, oczyszczal, SUW, uzdatn, przepompown, deszczow, retencj, tłoczn.
- **Subsector classification:** rules from the expert config (CPV + keywords → one of the 6 MFiPR subsectors; work type: construction/extension vs rebuild/renovation). Rules are editable in the UI.
- **Result:** thousands of procedures with outcomes. They give the sample size n for the new-investment ranges and are the ground the monitoring module watches.

---

## 4. Stage 3 — parsing notices

### 4.1 Why the DOM, not plain text

[verified] `htmlBody` is HTML with numbered sections in the form `<h3>2.4.) Identyfikator postępowania: <span>ocds-…</span></h3>` or a heading followed by `<p>`.

The prep's `html_to_text` glues fields together ("wniosków: 26.1.1.)", "REGON 5906483621.7.)"). That breaks quotes and section anchors.

**The new parser (`parse/bzp_dom.py`):**

1. Walks the DOM (selectolax) and builds a list of `(section_no, label, value, char_offset, part_no)`.
2. Builds a canonical text in which each field is a separate line `section) label: value`. Offsets refer to this text, so a quote can be shown and checked exactly.
3. **Splits by lot first.** [verified] Section numbers repeat for each lot (Biecz: "Liczba części: 4", and the result notice has blocks "Część 1 … Część 4").
4. **Matches on the label text, not the section number.** [verified] Numbers mean different things in different types: in a performance notice "4.4.)" can be the contractor's voivodeship. The number is kept only as an anchor.

### 4.2 What we extract from each type

Prep regexes from `bzp_parse.py` are reused on the DOM labels.

**ContractNotice (new parser):**

| Section | Field |
|---|---|
| 1.3/1.4 | REGON / NIP |
| 2.3 | title |
| 2.4 | OCID |
| 2.5 | number |
| 2.9 | procurement plan number |
| 2.14 | EU project (+ name/number) |
| 2.16 | procedure type |
| 3.1 | procedure website (purchase platform) |
| 4.1.x | parts (4.1.9 "Liczba części") |
| 4.2.x | object, CPV, description |
| 4.2.10 | completion period ("12 miesiące", "160 dni", "do 2026-04-27") |
| — | award criteria (price / warranty / time) |
| — | estimated value, if published |

**TenderResultNotice, per lot:**

| Section | Field |
|---|---|
| 2.4 | OCID |
| 2.11 | EU |
| 2.14 | previous notice |
| 3.1 | procedure type |
| 4.3 | contract value (net) |
| 5.1 | outcome: award or cancellation |
| 5.2 / 5.2.1 | cancellation basis and reason, e.g. art. 255 pkt 3 (price above budget) |
| 6.1.x | number of offers, offers from SMEs, rejected offers, abnormally low offers |
| 6.2 / 6.3 / 6.4 | lowest, highest and winning price |
| 7.x | contractor (NIP, size, consortium, subcontracting) |
| 8.1 | contract date |
| 8.2 | contract value |
| 8.3 | period |

**AgreementUpdateNotice** [verified on Nowogard]:

| Section | Field |
|---|---|
| 2.2 | OCID |
| 3.1.1 | previous notice |
| 4.1 / 4.2 / 4.4 / 4.5 | contract date, period, value, result notice number |
| 5.1 | change date |
| 5.2 | legal basis (art. 455 ust. 1 pkt 1–4 / ust. 2) |
| 5.3 | **reasons for the change** |
| 5.4 | short description, e.g. a new deadline |
| 5.5.x | change value / price increase |
| 5.6 / 5.7 | earlier changes and their notice numbers |

**ContractPerformingNotice:**

| Section | Field |
|---|---|
| 2.1 | OCID |
| 3.2.1 | previous notice (can be a TED number, e.g. "37125-2026") |
| 3.3 / 3.4 | EU project + project name or number. **This is where a KPO number can appear** |
| 3.9 / 3.10 | main and additional CPV |
| 4.1 | contract date |
| 4.2 | period |
| 4.4 | value |
| 4.5 | result notice number |
| 5.1 | performed? |
| 5.2 | completion date [to check: actual completion date?] |
| 5.3 | **on the original deadline?** |
| 5.4.1 | number of changes |
| 5.4.2–5.4.8 | per change: number, basis, reasons, description, value, price increase |
| 5.5 | **total paid** |
| 5.6 | performed properly? |
| title | **"Umowa dla części nr N"**, which maps the notice to a lot [verified on Biecz] |

### 4.3 Normalising values

- **Amounts:** "1952120,53" → Decimal. Each amount gets a basis: `net` (estimated value, 4.3), `gross` (offers, contract, payment) or `unknown` (KPO value).
  - Compare only amounts of the same basis.
  - When a conversion is needed (net → gross at 23% VAT), it is shown as a calculation with the assumption stated.
- **Periods:** "N miesiące" → calendar months from the contract date (not ×30); "N dni"; "do RRRR-MM-DD"; "od A do B".
- **Dates:** ISO; the API's `publicationDate` in UTC.
- **Identifiers:**
  - BZP number with or without the version suffix (`/01`);
  - TED number `NNNNN-RRRR`;
  - plan number `…/P`;
  - case reference (e.g. "OPZ.271.74.2026").
- **Natural persons:** a contractor without a legal-form marker (sp. z o.o., S.A., spółka …) whose name looks like "first name + surname" gets `natural_person_flag = true` and is masked in the UI.

---

## 5. Stage 4 — linking records

The goal is a graph: **project → procedure(s) (+ sibling procedures) → lot → notices → contract(s) → changes → performance.**

### 5.1 Path 1: keys, in order of confidence

1. **KPO number inside the notice.** For KPO rows, search sections 3.3/3.4 of performance and change notices (and 2.14 of contract notices) for that KPO number. The prep regex `EU_PROJECT_RE` already matches the format. This is an exact match by public identifier.
2. **BZP number from the xlsx.**
   - Query `NoticeNumber` with the year as the date window → ContractNotice → OCID, NIP, REGON.
   - Check: notice NIP == xlsx NIP; title similar; TERYT ↔ `organizationProvince`.
3. **OCID + NIP.** All notices with the same `tenderId` and NIP (from 3.3) belong to the procedure.
4. **Cross-references between notices:**
   - 4.5 (performance/change → result notice; the logic of the prep `bzp_join.py`);
   - 2.14 / 3.1.1 / 3.2.1 (→ previous notice);
   - 5.7 (→ earlier change).

   This also catches TED links.
5. **Lot.** For a "część N" row, link only the contract and notices of part N, matched by:
   - the title "Umowa dla części nr N";
   - contractor NIP (7.x in the result notice ↔ `contractors` of the performance notice);
   - value (8.2 ≈ 4.4);
   - date (8.1 ≈ 4.1).

A key match gets confidence 1.0 and status *proposed*. The expert can confirm all key links at once.

### 5.2 Path 2: scored candidates (no key, or keys disagree)

When it applies: the BZP number does not exist (e.g. **RM-2026-022 Wolin, 2023/BZP 00110672/01 [verified missing]**); a KPO row has no KPO number in any notice; the lot does not match.

1. **Candidates:** procedures of the same NIP, wod-kan CPV, from the date window (soft).
2. **Score components**, each with evidence:

   | Component | How it is measured | Weight (default, editable) |
   |---|---|---|
   | Title similarity | rapidfuzz token-set + TF-IDF char-ngram + embeddings, after normalisation (quotes, dashes, double spaces, case) | 0.40 |
   | Location / object names | Shared place names and street names from the description | 0.15 |
   | CPV / subsector | Same subsector | 0.10 |
   | Date | KPO suffix `/24`, `/25` → expected 2024–2026; soft score | 0.10 |
   | Value | Ratio of contract value to project value, without VAT assumptions | 0.10 |
   | Scope | km, number of connections, pumping stations from the description vs the notice | 0.10 |
   | Consistency with the xlsx | Status, lot | 0.05 |

3. **Explanation:**
   - in prose, e.g. "Tytuł zgodny w 97% (różnica: myślnik/spacje), ten sam NIP 9860164852, CPV 45232410, data 2023 zgodna z numerem ogłoszenia";
   - plus **alternatives (decoys)** with their scores.

   Examples [verified]:
   - Wolin: "BUDOWA SIECI WODOCIĄGOWYCH W GMINIE WOLIN";
   - Zduny: an earlier "Baszków" procedure;
   - Grodzisko Dolne: 3 wod-kan procedures.
4. **Status** is "do weryfikacji". The expert accepts, picks a different candidate, enters an OCID or notice number by hand (a "relink", which starts a fetch), or rejects.
5. **Expert decisions are remembered.** Rejected candidates are not proposed again; a relink is an override that survives a rebuild.

### 5.3 Sibling procedures

Procedures of the same NIP that were **cancelled or repeated** with a similar title (e.g. "(II postępowanie)") are attached as related to the project. They produce the events "Unieważnienie postępowania" and "Powtórzenie postępowania".

### 5.4 Checking link quality

- **Our gold set** is built by hand and checked by people, not by the algorithm. One row per notice of each of the 22 projects: RM-id, notice number, type, OCID, lot, contractor NIP, plus the errors found in the organizer's data.
- **Metrics:** precision, recall, share of uncertain links, list of wrong links. They appear on the "Jakość" page and in the test report.
- **Export `links.csv`:** project, level, target id, method, confidence, components, status, evidence.

---

## 6. Stage 5 — importing other sources

| Connector | Query | Use |
|---|---|---|
| `vat_whitelist` | `GET /api/search/nip/{nip}?date=YYYY-MM-DD` | Check NIP → name, REGON, KRS, VAT status for beneficiaries and contractors. **Cross-source check:** for Oława, REGON 931934868 from the VAT list = REGON in section 1.4 of the BZP notice [verified]. Differences become a "Sprzeczność" (contradiction) |
| `ted` | `POST /v3/notices/search` with query `buyer-name~… AND classification-cpv=4523* AND buyer-country=POL AND publication-date>=…` | Above-threshold procedures; follow TED numbers found in BZP. For national procedures it records "sprawdzono: brak" (checked: none), which is also a verifiable result |
| `nik` | URL of a report (PDF) | The document is processed as in section 7; the LLM extracts "lessons" with quotes, for expert approval |
| `web_doc` | Any URL (BIP, gmina news) given by the user | Fetch (respecting robots.txt), detect type, process as a document |
| `krs`, `kio`, `bk2021`, `kposk` | (P1/P2) | Contractor status, appeals, competitiveness-rule procedures, agglomerations |

Every connector implements the same interface (`search`, `fetch`, `normalize`), writes to the raw store and to `op_log`, and is switched on in config. **A new source means a new connector class, with no change to the rest of the system.**

---

## 7. Stage 6 — processing documents (PDF, DOCX, XLS, CSV, HTML)

1. **Input:** an uploaded file or a URL. Store sha256 (duplicate detection) and the version.
2. **Text extraction:**
   - PDF with a text layer: pdfplumber/pypdf, page by page, with tables;
   - DOCX: python-docx, paragraph by paragraph, with tables;
   - XLS/XLSX/CSV: openpyxl/xlrd;
   - HTML: selectolax;
   - P2: OCR of scans (Tesseract + pypdfium2) and .doc/.odt through LibreOffice.
3. **Locators:** PDF → page; DOCX → paragraph number (DOCX has no pages); spreadsheet → sheet!row:column.
4. **Document type and phase** per the expert table:
   - types: SWZ, PFU, OPZ, PPU/SWU, STWiORB, przedmiar/kosztorys, umowa, aneks, protokół, decyzja, odpowiedzi na pytania, informacja z otwarcia ofert, NIK, KIO …;
   - phases: planowanie → przygotowanie → postępowanie → umowa → projektowanie → realizacja → odbiór → zamknięcie.

   Rules on the title and contents first, the LLM as fallback.
5. **PPU as a stand-in for a contract.** If there is no signed contract but we have the PPU/SWU, plus contractor, price, deadline and procedure id from the notices, we create "warunki kontraktowe odtworzone; brak podpisanego egzemplarza umowy" (contract terms reconstructed; no signed copy).
6. **Chunking:** chunks of ~1–2 thousand characters with locator and offsets, a `tsvector` (full-text search) and an embedding (pgvector).
7. **Risk fragments** (section 8.3).

---

## 8. Stage 7 — events and risks

### 8.1 Rule events, from structured fields (high precision)

| Event (MFiPR table) | Rule | Effect | Default code |
|---|---|---|---|
| Performed after the original deadline | Performance 5.3 = "Nie" | days = actual date (5.2) − planned date (4.1 + 4.2) | R06 + cause |
| Payment above the original value | 5.5 > 4.4 × 1.01 | PLN and % | R07/R13 by cause |
| Change of deadline / fee / scope | Each AgreementUpdate and each 5.4.x | Change in days / PLN | by cause |
| Additional or replacement works | art. 455 ust. 1 pkt 3, or "dodatkowe/zamienne" in the description | PLN | R07 |
| Improper performance / penalty | 5.6 = "Nie", "kar umownych" in the text | — | R12 |
| Not performed / terminated / withdrawn | 5.1 = "Nie" | — | R12 |
| Procedure cancelled | TenderResult 5.1 + 5.2.1; art. 255 pkt 3 → price above budget | delay until the repeat | R13 / R11 |
| Repeated procedure | Sibling procedure with a similar title | days between procedures | R11 |
| Single offer | 6.1 = 1 | — | R11 (signal) |
| Offers above budget | Lowest offer > amount for financing | % | R13 |
| Change of contractor | art. 455 ust. 1 pkt 2 / different NIP | — | R12 |
| KIO appeal (P1) | Ruling from the KIO connector | days | R11 |

Every event gets evidence: notice, section, verbatim quote, permanent link.

### 8.2 Causes of changes (rules + LLM)

Input: the texts in 5.3 (AgreementUpdate) and 5.4.4 (performance notice).

1. **Rule pre-labeling:** an adapted `classify_reasons.py` with wod-kan patterns:

   | Pattern | Code |
   |---|---|
   | służebność, zgoda właściciela | R03 |
   | warunki gruntowe, wody gruntowe | R02 |
   | kolizja, niezinwentaryzowan | R02/R03 |
   | decyzja, uzgodnienie, gestor | R04 |
   | błąd projektu | R01/R09 |
   | dostawy pomp/urządzeń | R12 |
   | finansowanie | R13 |
   | pogoda | R06 |

2. **LLM** (vendor chosen in config) with the output schema `{risk_codes, cause, effect, mitigation, quote, confidence}`, plus few-shot examples from items the expert marked as exemplary.
3. **Quote check:** the quote must occur verbatim in the cited section, with the same normalisation on both sides (NFKC, NBSP, quote marks, hyphenation). If it does not, the result is rejected or its confidence lowered.
4. **No code fits** → the system proposes a new category to the expert ("propozycja kategorii").

[verified] Example: Nowogard (RM-2026-020).
- "konieczność ustanowienia służebności przesyłu na działce nr 3/39" → R03, deadline +1 month.
- "ujawniono niekorzystne warunki gruntowe oraz … wysoki poziom wód gruntowych" → R02, deadline +1 month.

### 8.3 Risk fragments in documents

The LLM receives only the relevant chunks (top-k by retrieval), wrapped as untrusted data (prompt-injection defence). It returns fragments in the expert's form:

**condition or signal → possible event → possible impact → possible mitigations**, with R-code, page or paragraph, quote and confidence.

Examples of signals: a lump-sum fee with an incomplete PFU (R08); no geotechnical surveys (R02); route over private land without easements (R03); environmental decision still pending (R04); no tests or commissioning in the STWiORB (R10); no price-indexation clause (R13).

### 8.4 Completeness and contradictions

- **Data gaps:** the list of documents expected per phase is compared with what we have. Each is marked in one of the 4 expert states: "nie ma w paczce" / "dokument nie wspomina" / "brak potwierdzenia" / "potwierdzono, że nie wykonano". Each gap shows what to add and how it limits the analysis. *A missing file ≠ a document that does not exist.*
- **Contradictions:** the same fact from different sources with different values, e.g.:
  - xlsx title vs notice title;
  - xlsx status "Zakończone" vs no performance notice;
  - contract value in 8.2 vs 4.4;
  - REGON from the VAT list vs the notice.

  The expert decides which value is right.

### 8.5 Re-analysis (new document or notice)

The extraction reruns for the project. The diff marks each fact, event, contradiction and conclusion as **new / confirmed / changed / closed**. The diff goes to the expert queue and to the history.

---

## 9. Stage 8 — the expert's role in processing

- **Queue, uncertain items first:** links with confidence < 1, LLM events, proposed categories, contradictions.
- **Actions:** accept, edit, reject, relink, mark exemplary, bulk-confirm. Each is written to `review` (before/after, who, when, comment).
- **Knowledge:** the catalog, rules, checklists, similarity weights and clauses are generated from the expert docx by an importer, then edited in a table editor in the UI, with versioning.
- **Learning:** exemplary items → LLM examples; rejections → blacklist; relinks → overrides; approved lessons and clauses → recommendations.

---

## 10. Stage 9 — how the data feeds new-investment analysis (summary)

1. **Features** of the new investment (LLM + regex): subsector, work type, formula, km, connections, pumping stations, RLM, value (net or gross?), period, location, funding, signals about land, decisions and the operator.
2. **Neighbours** from the deep tier (22 + added) and the auto tier (BZP harvest): weighted similarity of features + text (TF-IDF + embeddings), with per-component explanations.
3. **Ranges:** empirical quantiles over the named neighbours with shrinkage toward the broader class:
   - P(delay) with a Wilson interval;
   - delay days P50/P80;
   - payment/value P50/P80/P95;
   - P(change);
   - cancellation share.

   Always show n, the period and links to the cases.
4. **Budget and schedule assessment:** the project's percentile among neighbours, cost per km/RLM, winning offer vs estimate (taking VAT into account), cancellations under art. 255 pkt 3.
5. **Flags, actions and clauses:** checklist gaps, R-signals, lessons, and the legal bases of changes among neighbours. Each clause has an R-code, a trigger, a Pzp article, evidence and a status.
6. **Record and export:** the result is saved as `analysis` records and exported to JSON, CSV and DOCX.

---

## 11. Monitoring (bonus)

- The scheduler runs a BZP query every day for watched OCIDs: procedures without a performance notice, or with status other than "Zakończone".
- A new notice (change / performance) → alert → re-analysis diff → updated forecast.
- **Demo:** `as_of` mode hides notices after a given date, then advances the date. The new notices "appear" and the system reacts.

---

## 12. Running and repeatability

```bash
riskminer import data/organizer/Risk_Miner_dane_projekty.xlsx   # stage 1
riskminer harvest --zip data/raw/risk_miner_bzp_kopia.zip        # auto tier (stage 2, bulk)
riskminer enrich --all                                           # stages 2–6 for the deep tier (live API)
riskminer extract --all                                          # stage 7
riskminer report --out docs/raport_z_testu.md                    # gold-set metrics + issues
riskminer export --format json,csv --out exports/
```

- The same operations are available as UI buttons; they run as background jobs and their progress is visible.
- A second run adds no duplicates and does not overwrite the expert's decisions. It only proposes diffs.
- `LLM_MODE=replay` plus the raw store: the full pipeline runs offline and without keys. Every LLM step has a rules-only fallback (`provider: none`).

---

## 13. What has been verified and what is still to verify

**Verified on 2026-11-21:**
- the mirror's behaviour and filters;
- 403 for the default User-Agent;
- notice types;
- 14/15 BZP numbers resolve, NIP/TERYT consistent;
- Wolin's number is missing, and a decoy exists;
- KPO candidates for all 7 rows;
- lot structure (Biecz);
- Nowogard's changes;
- permanent ezamowienia links;
- the VAT list (REGON consistent);
- TED search;
- BK2021 and KIO pages exist;
- purchase platforms block anonymous access.

**To verify:**
- what section 5.2 of the performance notice means;
- whether `CpvCode` also matches additional CPVs;
- whether KPO numbers really appear in 3.3/3.4;
- the BK2021 API parameters;
- what the zip contains (time range, notice types);
- the VAT-list limits;
- the rule `IW.nn` = 12 + TERYT/2;
- coverage of km/RLM extraction from descriptions.
