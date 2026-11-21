# RISK MINER — implementation plan (HackNation 2026, MFiPR)

## 1. Context

### Why this plan exists
The full brief came out Sat 21.11 at 11:00. Its PDF, the task rules and the starter pack are in
`risk_miner/[Ministerstwo Funduszy i Polityki Regionalnej] Risk Miner/`. Our prep in `setup/prep/risk_miner/`
assumed "early warning from BZP contract outcomes". The real task is an **"inteligentna baza doświadczeń
inwestycji publicznych"** for the water and sewage (wod-kan) pilot sector:

1. **Build the case base automatically.** Start from the organizer's `.xlsx` (22 projects) and public sources:
   BZP is required, plus at least one of TED, BK2021, KPOŚK, BIP, NIK or KIO. Keep the relations: project →
   procedures → notices → contracts → changes → events → costs/dates → documents/sources.
2. **Find risk events.** Identify documented events and risky document fragments per the expert catalog
   **R01–R15**, each with cause, effect (days / PLN), mitigation and how well it worked. **Every event and
   conclusion needs expert approval.** Every record, link and key conclusion needs a source id, link, fetch
   date, page or fragment, approval info and edit history.
3. **Analyse a new investment** from a description or PDF/DOCX. Output:
   - similar completed projects, with the reason they are similar;
   - cost and time deviation ranges, with sample size and uncertainty;
   - an assessment of the budget and schedule;
   - flags, recommended actions and proposed contract clauses.

   Results are stored as records you can filter and export to JSON/CSV. Bonus: monitoring of unfinished
   projects.

### Scoring and tests
**Scoring:** acquisition/linking 20% · documents/events 20% · **new investment 25%** · expert control,
editability, modularity 20% · UX/tech/scalability 15%.

**Jury tests:**
- integration: rerun without manual input, query correctness, how many records are found;
- linking, against a hidden reference set;
- case completeness;
- new investment;
- source check: a result without a source is treated as undocumented;
- expert work: accept, correct or reject an uncertain match;
- assumptions and scalability.

### Deliverables and deadlines
Deliverables:
- live link;
- title and description (≤10 pages, stating what works and what is only designed);
- PDF of at most 10 slides;
- the repository;
- a video of at most 3 minutes;
- technical docs;
- a test report;
- an example export;
- an example config that says where data is processed and under which licence.

**Deadlines:** pick the task in HackTribe by **Sat 20:00**; submit by **Sun 11:00**.

### Your decisions
- FastAPI + React.
- An LLM layer independent of any vendor: Anthropic, OpenAI, Gemini, and any OpenAI-compatible or local model,
  all set in config.
- **Solo, but maximum scope**, through up to **6 parallel Claude Code sessions** in separate worktrees.
- Downloading the organizer's BZP zip is approved.
- I create the GitHub repo.
- Hosting (Vercel or Hetzner) will be bought later. Hetzner is recommended; see §3.

**Decision: GO.** None of the prep's "nie bierzemy" signals apply.

### Verified in this planning session (read-only probes)
**Organizer mirror:**
- `https://bzp.cytr.us/mo-board/api/v1/notice` has the same API as BZP and no rate limit. Data runs up to
  about 2026-11-12, and the mirror exists only "na czas HackNation".
- **Python's default User-Agent gets HTTP 403**, so we always send our own.
- The zip is at `https://bzp.cytr.us/paczka/risk_miner_bzp_kopia.zip` (149 MB).

**API filters:**
- These work: `NoticeType` + `PublicationDateFrom/To` (required), `PageSize` ≤500 with `SearchAfter`,
  `NoticeNumber`, `OrganizationName` (substring match), `CpvCode`.
- **These are silently ignored:** `TenderId`, `OrganizationNationalId`, `OrganizationId`, `BzpNumber`.
- So linking goes: query by organization name → keep rows where `organizationNationalId` = NIP → group by
  `tenderId` (OCID) → follow the notice-number cross-references.
- Change notices are `AgreementUpdateNotice`.

**Permanent evidence links** (the mirror is temporary):
- page: `https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/<objectId>`;
- PDF: `https://ezamowienia.gov.pl/mo-board/api/v1/Board/GetNoticePdfById?noticeId=<objectId>`.

Both return 200. The mirror URL is stored only as `retrieved_from`.

**The xlsx:**
- 15 rows carry a BZP number and 7 carry only a KPO number.
- Every NIP passes the checksum.
- Two rows are lots: Biecz "część 1" and Zakrzew "część 2".
- Czernikowo and Nowogard have two projects each.
- In all 7 KPO rows, `IW.nn` = 12 + TERYT/2. That gives a free consistency check; confirm it with the mentors.
- 14 of the 15 BZP numbers resolve, and their NIP and TERYT match.

**Known traps:**
- **RM-2026-022 (Wolin, 2023/BZP 00110672/01) does not exist in BZP.** Its procedure can still be found through
  AgreementUpdate 2023/BZP 00396503/01 and two ContractPerforming notices with the same title. There is also a
  decoy with a near-identical title.
- The KPO-only rows all have a clear candidate, but each has a decoy to rule out:
  - Zduny: an earlier Baszków procedure.
  - Grodzisko Dolne: 3 wod-kan procedures.
  - Kamionka: other gminas share the name, so the NIP filter is essential.
  - Kleszczewo: search by the beneficiary's seat, not by the village.

**Notice structure:**
- **`htmlBody` uses numbered sections** shaped like `<h3>label<span>value</span>` (or h3 + `<p>`).
- Section numbers repeat for each lot and change their meaning across notice types. **We parse the DOM into
  (section, label, value, offset).**
- The prep's `html_to_text` glues fields together ("wniosków: 26.1.1.)"), which would break quotes.

**Lots (Biecz):**
- ContractNotice: "Liczba części: 4".
- One TenderResultNotice covers all 4 lots.
- There are 4 ContractPerforming notices, each titled "… Umowa dla części nr N".

**Showcase (RM-2026-020, Nowogard, KPO-only):** two changes under art. 455 ust. 1 pkt 4, with verbatim reasons:
- "konieczność ustanowienia służebności przesyłu na działce nr 3/39" → R03, new deadline 30.11.2025;
- "ujawniono niekorzystne warunki gruntowe … wysoki poziom wód gruntowych" → R02, new deadline 31.12.2025.

**Extra sources answer without auth:**
- **Biała lista VAT** (`/api/search/nip/{nip}`) returns name, REGON and status. For Oława the REGON matches the
  BZP body. Bank accounts and representatives are dropped.
- **TED v3** search works, but returns nothing for national procedures.
- **BK2021** is a SPA over a JSON API.
- **KIO** (`orzeczenia.uzp.gov.pl`) is a server-rendered search.

**Tender documents:**
- SWZ/PFU/PPU sit on purchase platforms. platformazakupowa.pl blocks anonymous access (SSO, HTTP 429).
- So documents arrive by upload, by URL fetch, or from the organizer.

**Data location:** the first-party Claude API processes data **outside the EU** (`inference_geo` is `global`
or `us`).

## 2. Strategy

**Two jury paths drive everything:**
- **(A) Import and auto-enrichment:** file → linked case (relations, events, evidence) → expert review →
  export.
- **(B) New investment:** text or documents → explained neighbours → ranges with n → budget and schedule
  assessment → flags and checklist → actions and clauses → saved records → export.

**Every fact, link, event, calculation and conclusion carries:**
- **evidence**: source, permanent URL, `retrieved_from`, `retrieved_at`, a locator (notice section / PDF page
  / DOCX paragraph / xlsx sheet-row-column) and a verbatim quote, or for calculations the input evidence ids
  plus the formula;
- a **status**. Everything system-generated starts as *proposed*, links with confidence 1.0 included; those can
  be **bulk-confirmed** in one click. Final status is approved / edited / rejected, with history.

**Deterministic parsing and rules are the core.** The LLM is pluggable; its output is schema- and
quote-checked, labeled "wniosek modelu", and always has a rules-only fallback.

**Two data tiers:**
- **Deep:** the 22 projects plus any added.
- **Auto:** every wod-kan procedure harvested from the zip or mirror for 2021–2026, using rule events and batch
  LLM cause labels. This gives real n and a "stale zasilana baza" story.

**Priority tiers order the work; nothing is cut up front:**

| Tier | Scope |
|---|---|
| **P0** | Everything a jury test touches (§7) |
| **P1** | Embeddings, NIK lessons, re-analysis diff, DOCX report, monitoring, TED/KRS/KIO/BK2021 connectors, mitigation effectiveness |
| **P2** | OCR, .doc/.odt, KPOŚK, OCDS export, MCP server, the drogi sector stub, a Monte Carlo refit on the wod-kan tier, rule suggestions, cost page |

## 3. Architecture and stack

All dependencies use permissive licences. The winner must transfer copyright, so: **no GPL/AGPL**, no PyMuPDF,
no Ghostscript/ocrmypdf.

### Backend
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic.
- **PostgreSQL 16 + pgvector + pg_trgm + unaccent.**
- Deterministic uuid5 ids built from natural keys, with `ON CONFLICT` upserts.
- Background work uses a DB `job` table and a worker process, with APScheduler for monitoring. Long jobs never
  run in a request.
- Libraries: selectolax (notice DOM), httpx, rapidfuzz, scikit-learn TF-IDF, sentence-transformers (local
  multilingual embeddings), pdfplumber/pypdf, python-docx, openpyxl/xlrd, python-docx reports. P2: pytesseract
  + pypdfium2 for OCR, LibreOffice headless.

### Frontend
- React 18 + TypeScript + Vite, Tailwind + shadcn/ui, TanStack Query/Table/Router.
- API client generated from OpenAPI.
- React Flow for the relations graph, Recharts for ranges and timelines, PDF.js viewer with quote
  highlighting.
- The UI is in Polish.

### LLM layer (`riskminer/llm/`)
**Interface:** one call, `complete(task, messages, schema=PydanticModel)`, returns `LLMResult(data, usage, cost,
provider, model, latency, cached)`. `embed()` handles embeddings.

**Providers,** each through its official SDK:

| Provider | Notes |
|---|---|
| `anthropic` | `output_config.format` JSON schema; effort set explicitly; beta `server-side-fallback-2026-07-01` + `fallbacks:"default"` (not on Vertex); catalog prompt cached; no `temperature` |
| `openai` | Structured outputs. Also covers **any OpenAI-compatible endpoint**: Ollama/vLLM/LM Studio with **local PLLuM/Bielik**, Azure OpenAI in EU regions, Mistral, OpenRouter |
| `gemini` | `google-genai`; AI Studio, or Vertex with an EU `location` |
| `litellm` | Optional, for any other vendor |
| `none` | Rules only |

**Config** (`config/settings.yaml`):
- `llm.profiles.<name>` = provider, model, base_url, api_key_env, **data_location**, max_tokens, effort.
- `llm.tasks.<task>` = an ordered list of profiles, used as fallbacks.
- The task list: causes, doc_fragments, features, recommendations, clauses, category_proposal, embeddings.
- Admins can switch profiles in the UI. A banner shows the active data location: local, EU or outside the EU.

**Safeguards:**
- Cache keyed on (provider, model, prompt version, input hash), giving stable reruns. Modes: live, cache,
  replay.
- Every call logged with its cost.
- `wrap_untrusted` plus the prep injection suite.
- Personal data stripped; only the top-k chunks go to the model.
- Pydantic validation with one repair retry.

**Defaults:**
- Claude: `claude-opus-5-5`.
- OpenAI and Gemini: you enter the current model ids.
- Local: Ollama.

Each provider is called at least once with a real key; any provider not called is marked "zaprojektowane" in
the docs.

### Deployment
`docker compose` brings up db, api, worker, web and Caddy (auto-HTTPS).

**Recommended host: Hetzner**, CX32/CPX31 class (≥4 vCPU, 8 GB), in DE or FI:
- everything runs in the EU;
- it is the only option that runs the worker, the embeddings, PDF processing and Postgres together.

**Vercel can host only the static React build.** Its functions can't run the worker, local embeddings,
LibreOffice/OCR or Postgres. So Vercel would mean "frontend on Vercel + API, worker and DB on Hetzner" anyway.

Use a domain or `<ip>.sslip.io`. Buy the host **by about 15:00**, because the first test deploy checks
outbound access to the mirror and the official API, plus persistence. Until then we test with local docker.

GitHub Actions run lint, tests and build.

### Repository
`/home/radek/workspace/hacknation/risk_miner/risk-miner/` is created by `gh repo create` as private
`hacknation-2026-solutions/risk-miner`. It becomes public at submission, with your OK.

```
risk-miner/  docker-compose.yml Caddyfile Makefile .env.example config/settings.example.yaml README.md LICENSE(Apache-2.0)
  knowledge/wodkan/   # GENERATED by `riskminer knowledge import <docx>` from the 2 MFiPR docx (tables → YAML), then expert-editable:
                      # R01–R15+effects, event→source table, art.455 bases, 6 subsectors(+CPV/keyword rules), phases & doc types,
                      # "porady", 9-point water checklist (→ R-codes); clause drafts (status draft). knowledge/drogi/ = P2 stub
  backend/riskminer/  core/ models/ schemas/ api/routers/<domain>.py ids.py
    connectors/ (registry: bzp, bzp_zip, vat_whitelist, nik, web_doc, files, ted, krs, kio, bk2021, kposk)
    parse/ bzp_dom.py bzp_notices.py documents.py   link/ matcher.py chain.py
    extract/ rules.py reasons.py llm_extract.py validate.py reanalyze.py completeness.py mitigation.py
    analysis/ features.py similarity.py embeddings.py ranges.py assess.py flags.py recommend.py clauses.py
    review/ audit.py learning.py   monitor/   export/ (json_csv, docx_report, ocds)   llm/   cli.py
  backend/alembic/ backend/tests/ (fixtures: real notices of the 22 projects, prep fixture, gold sets)
  frontend/src/   docs/ (architektura, ERD, źródła i dopasowanie, uruchomienie, licencje/SBOM, status.md, raport z testu, opis)
```

### UI: 5 navigation areas
1. **Start.** Pulpit with counts, last runs, alerts and the data-location banner, plus **"Jak testować"**: one
   click-through per jury test.
2. **Baza przypadków** and **Karta projektu.**
   - Przebieg: timeline from budget → offers → contract → changes → paid, planned vs actual.
   - Powiązania: graph with method and confidence.
   - Zdarzenia i ryzyka.
   - Dokumenty i źródła: viewer with the quote highlighted.
   - Braki danych: the expert's 4 states.
   - Sprzeczności.
   - Historia.
3. **Kolejka eksperta** and **Wiedza ekspercka.**
   - The queue lists uncertain items first.
   - Actions: accept, edit, reject, relink, mark exemplary, bulk-confirm.
   - The versioned table editor covers the catalog, rules, checklists, similarity weights, thresholds, clauses
     and LLM routing.
4. **Nowa inwestycja** and **Analizy.** Every block is labeled [Dane źródłowe], [Obliczenia] or [Wniosek
   modelu]. Saved analyses can be filtered and exported.
5. **Źródła i operacje:** op log, connector health, licences, LLM usage; plus **Jakość** (gold-set metrics) and
   **Monitoring**.

## 4. Data model (Postgres)

All ids are uuid5 from natural keys. Rows an expert has reviewed are never overwritten; a rerun proposes a
diff instead.

| Table | Key fields |
|---|---|
| project | id (RM-…), title, description, beneficiary_id, teryt/voivodeship, subsector_main/extra, work_type, formula, status, funding, project_value, grant, public_id_type/value, record_scope (całe / część N), tier (deep/auto), sector |
| entity | name, nip, regon, krs, role, province, verified_by (BZP/VAT/KRS), natural_person_flag (masked in UI) |
| procedure | ocid, bzp_number, title, cpv_main/extra, mode, buyer_id, est_value_net, planned_period, parts, eu_funded, eu_project_ref, platform_url, ted_refs, related_procedure_ids (cancelled/repeated siblings) |
| project_procedure | project_id, procedure_id, part_no, method (kpo_ref / notice_no / ocid / xref / fuzzy / expert), confidence, components (each with evidence), status |
| notice | object_id, notice_number, type, procedure_id, published_at, url (permanent), retrieved_from, raw_ref, canonical_text, sections (section, label, value, offset, part_no), xrefs |
| contract | procedure_id, part_no, contractor_id, signed_at, value_gross, planned_end, actual_end, paid, on_time, proper, n_changes, terms_source |
| contract_change | contract_id, notice_id, change_no, date, legal_basis, reason, description, value_delta, new_end |
| fact | subject, fact_type, value, unit, **vat_basis (net/gross/unknown)**, evidence_id \| derivation (input evidence ids + formula) |
| document, chunk | doc_type, phase, url/file, sha256, version; chunk locator (page or paragraph), offsets, tsvector, embedding |
| evidence, source | locator, quote, url, retrieved_from, retrieved_at, import_file sha256 / sheet / row / column; source licence |
| risk_category, lesson, clause | R-codes (+ proposed); lessons (case → cause → signal → effect → recommendation); clauses (R-code, trigger, legal basis / Pzp art., text, evidence, status) |
| event | ids, event_type, risk_codes, cause, effect_days/pln/pct, mitigation, mitigation_effect (+ rule used), method, confidence, status, exemplary |
| review | object, action, before, after, comment, reviewer, at |
| rule, setting, sector_profile | versioned |
| analysis, analysis_item | Items: neighbours with breakdown, ranges (n, CI, fallback level), assessments, flags, actions, clauses. Each item has its own accept/reject and "exclude neighbour" triggers a recompute |
| alert, job, op_log, user | — |

## 5. Functional design

### 5.1 Acquisition and linking (20%)
1. **Import xlsx/csv.** The organizer's layout is the default profile; a P2 mapping form covers other layouts.
   - Every row gets evidence: sha256, sheet, row, column, import time.
   - Validate NIP/REGON checksums, the BZP number `^\d{4}/BZP \d{8}/\d{2}$`, KPO/CST/OCID/TED formats, TERYT ↔
     voivodeship, and KPO `IW.nn`.
   - Problems become data-quality issues.
2. **Get the raw notices.**
   - BZP connector: base URL comes from config, with our own UA, `SearchAfter` paging and a raw store, logged
     in op_log.
   - `bzp_zip` loads the 149 MB snapshot into the same raw store. The jury's integration test runs the live
     query path.
3. **Parse.** The DOM parser yields (section, label, value, offset) plus canonical text. It splits by lot
   first, and handles all 4 types, adding a new ContractNotice parser. Prep regexes are reused on labels.
4. **Link with keys first.** In order:
   1. For KPO rows, search notice sections 3.3/3.4 for the KPO number (prep `EU_PROJECT_RE`).
   2. Look up the BZP number → ContractNotice → OCID, then check the NIP.
   3. Fetch all 4 types by `OrganizationName` variants, filtered by NIP, grouped by OCID.
   4. **Chain notices through cross-references** 2.14 / 3.1.1 / 3.2.1 / 4.5, extending the 4.5 join from
      `bzp_join.py`.
   5. Match lots by "Umowa dla części nr N", contractor NIP, value (8.2 ≈ 4.4) and date (8.1 ≈ 4.1).
5. **Score candidates when keys fail.** Applies to an unknown number, no KPO reference, or a lot mismatch.
   - Score same-NIP procedures on title (rapidfuzz, TF-IDF, embeddings), wod-kan CPV, a **soft** date window,
     value proximity and location tokens.
   - Each score component cites its evidence. Decoys are listed as alternatives.
   - Include sibling procedures (cancelled or repeated).
6. **Extra sources.**

   | Source | Use | Tier |
   |---|---|---|
   | **Biała lista VAT** | NIP ↔ name/REGON/status for beneficiaries and contractors | **P0** |
   | **1–2 NIK wod-kan reports** | Fetched by URL → lessons | **P0** |
   | TED | Reported as "sprawdzono: brak" for national procedures | P1 |
   | KRS, KIO, BK2021 | — | P1 |
   | KPOŚK, web-search discovery | — | P2 |

7. **Reruns.** `riskminer enrich --all` and the UI button do the same thing: idempotent, with a run report
   (queries, found, linked, uncertain, errors).

### 5.2 Events, documents, re-analysis (20%)
**Rule events from structured sections.** Each cites its section and quote:
- late (5.3, plus calendar-month date difference);
- paid above value (5.5 vs 4.4);
- each change (5.4.2–5.4.8 / AgreementUpdate 5.x; art. 455 basis → type);
- not performed / terminated;
- improper performance;
- cancellation (art. 255 pkt 3 → R13);
- repeated procedure;
- single offer (R11);
- offers above budget (R13);
- contractor change;
- KIO appeal (P1).

**Causes:**
1. Rule pre-labeler: adapted `classify_reasons.py` with wod-kan patterns, mapped to R-codes.
2. LLM to `{risk_codes, cause, effect, mitigation, quote, confidence}`, with few-shot examples taken from
   exemplary approved items.
3. **Quote check** against the cited section or chunk, with the same normalisation on both sides: NFKC, NBSP,
   quotation marks, PDF hyphenation.
4. Batch run for the auto tier.

**Documents** (PDF with a text layer, DOCX, XLS/XLSX, CSV, HTML):
- detect type and phase per the expert table;
- locate by PDF page or DOCX paragraph;
- extract fragments in the expert format "warunek/sygnał → możliwe zdarzenie → możliwy wpływ → środki
  zaradcze";
- apply the PPU-substitute rule (label "warunki kontraktowe odtworzone");
- wrap the document text as untrusted.

**Catalog, completeness, re-analysis:**
- Open catalog: anything that fits no category becomes a proposed category, queued for the expert.
- Completeness: the 4 states, what to add, and how the gap limits the analysis.
- Re-analysis after a new document or notice (P1): a diff marked new / confirmed / changed / closed.

**Mitigation effectiveness rules (P1).**
- Was the work finished by the amended date?
- Were there repeated extensions?
- Was it performed properly (5.6)?
- Is paid ≤ value + the sum of changes?

Otherwise "brak danych". Always show n.

### 5.3 Expert control (20%)
- **Proposed-first queue, uncertain items on top.** Actions: accept, edit, reject, relink (pick a candidate or
  give an OCID / notice number, which triggers a fetch), mark exemplary, bulk-confirm.
- **Edit every input record.**
- **Knowledge comes from automatic docx import,** then a versioned table editor with no code. This also shows
  that a new sector is just new files.
- **Learning loop:**
  - exemplary items → few-shot examples;
  - rejections → blacklist;
  - relinks → overrides that survive rebuilds;
  - approved clauses and lessons → recommendations.
- **Demo users with roles** for the approval trail. Jurors get a sandbox copy of the golden DB, with a
  "Przywróć stan demo" reset.

### 5.4 New-investment analysis (25%)
1. **Features.**
   - Extracted by an LLM schema with a regex fallback: subsectors, work type, formula, km, connections, pump
     stations, RLM/m³ per day, value (**ask net or gross**), duration, location, funding, cues about land,
     permits, environment and the operator.
   - Confirmed in an editable form.
   - **Measure the km and RLM regex coverage on the 22 cases early.**
2. **Neighbours** from the deep and auto tiers.
   - Score = editable weights × structured similarity + TF-IDF + embeddings.
   - Show the breakdown, shared terms or passages, differences and missing features.
3. **Ranges: empirical quantiles over the named neighbours** with `_shrink()` toward subsector / wod-kan /
   works priors. Report the fallback level used, plus:
   - P(late) with a Wilson confidence interval;
   - delay days P50/P80;
   - paid/value P50/P80/P95;
   - P(change);
   - share cancelled.

   Every number shows n and period, and links to its cases. No Monte Carlo on general-works parameters.
4. **Budget and schedule assessment.**
   - Where the user's budget and duration fall among the neighbours, as a percentile.
   - Winning offer vs estimate (VAT-aware; `unknown` is never compared).
   - Cost per km / RLM, with n.
   - Share cancelled under art. 255 pkt 3.
5. **Flags.**
   - Gaps against the 9-point checklist (mapped to R-codes, scored with the 4 states).
   - R-signals in the text or documents.
   - Outliers.
   - Applicable lessons.
6. **Actions and clauses.**
   - Each clause has an R-code, a trigger, a legal basis (Pzp article), evidence from the neighbours and a
     status.
   - Use the **distribution of change bases among neighbours**. If most changes went under art. 455 ust. 1
     pkt 4 rather than pkt 1, recommend clauses that foresee those changes.
   - LLM tailoring is labeled and needs approval.
7. **Saved records.** Items can be accepted or rejected, and neighbours excluded with a recompute. Export to
   JSON, CSV or a DOCX "Karta analizy inwestycji".

### 5.5 Monitoring (P1)
- The scheduler re-queries watched OCIDs.
- A new notice raises an alert and triggers a re-analysis diff.
- Demo with `as_of` replay. Use it on any "Zakończone" rows without a performance notice (for example,
  Bobrowniki) as data-quality findings.

## 6. Reuse from prep

| Prep asset (under `setup/prep/`) | Action | Target |
|---|---|---|
| `risk_miner/.claude/skills/riskminer-dane-i-zrodla/scripts/bzp_fetch.py` (`_get`, `fetch_day`) | Adapt: windows, org query, UA, raw store, op_log | `connectors/bzp.py` |
| `…/bzp_parse.py` (`period_to_days`, `EU_PROJECT_RE`, regexes of `parse_performing/result/change`) | Reuse the label regexes on the DOM output. Replace `html_to_text`. Add ContractNotice, per-change rows, all lots, CPV 3.10 | `parse/` |
| `…/bzp_join.py` (join on 4.5 result-notice number, `add_features`) | Keep and extend to lots and all cross-references | `link/chain.py` |
| `…/riskminer-klasa-referencyjna/scripts/refclass_build.py` `cell()`, `refclass_forecast.py` `_shrink()` | Adapt: neighbours + empirical quantiles. Monte Carlo/copula only as a P2 refit on wod-kan | `analysis/ranges.py` |
| `…/riskminer-czerwone-flagi/scripts/flags.py` (flag object, levels, S1/S2) | Adapt to R01–R15 | `analysis/flags.py`, `monitor/` |
| `…/riskminer-ekstrakcja-przyczyn/scripts/classify_reasons.py`, `validate_extraction.py`, `references/prompty.md`, `schemat-ryzyka.json` | Adapt: wod-kan patterns and R-codes; check quotes against the chunk, not the whole doc | `extract/` |
| `risk_miner/data-samples/bzp/notices_fixture_4.json`, gold and holdout reason sets | Fixtures, relabeled to R-codes | `tests/fixtures/` |
| `_wspolne/.claude/skills/hn-llm-w-produkcie/scripts/llm_client.py`, `injection_suite.py` | Reuse the design (modes, log, `wrap_untrusted`) and the test | `llm/`, `tests/` |
| `_wspolne/.claude/skills/hn-zgloszenie/` (`preflight.py`, README template, `video_check.sh --max 175`), `hn-pitch-final` | Use at submission | — |
| `_wspolne/install.sh <repo> risk_miner --gitignore` | Install the 12 skills; list them under "Ujawnienie" | — |
| `baseline.py`, `synth.py`, `sample_to_full.py`, the 500-row sample | Drop | — |

## 7. Execution (solo, with up to 6 parallel sessions)

**P0, what every jury test touches:**
- import and validation;
- connector + zip + op_log;
- the DOM parser for all 4 types;
- the linker: keys, cross-references, lots, decoys, explanations;
- evidence, status and history, with a highlighting viewer;
- rule events + causes with quotes;
- the review queue + table editor + knowledge import;
- PDF/DOCX ingest;
- path B end to end (features → neighbours → ranges → assessment → flags → clauses → records);
- exports;
- config with all providers + `none`;
- Biała lista + NIK;
- the gold set + test report;
- the "Jak testować" page;
- deploy.

### Phase 0, this session (13:15–14:45)
Build the foundation every stream depends on:
- the repo (`gh repo create`, private) and `install.sh`;
- docker compose;
- the FastAPI skeleton, the **full schema plus the first migration**, and Pydantic/OpenAPI **contract stubs
  for every router**;
- the LLM interface;
- the `knowledge import` docx parser, then generate `knowledge/wodkan/`;
- the frontend scaffold with the generated client;
- Makefile, `.env.example`, `settings.example.yaml`, CI;
- download the zip into `data/` (gitignored);
- save the real notices of the 22 projects as fixtures;
- start `docs/status.md`.

**You, meanwhile:**
- **Create the HackTribe project and choose RISK MINER now** (deadline 20:00).
- Ask the mentors the §11 questions.
- Put the API keys into `.env`.
- Buy the host by about 15:00.

### Phase 1, from 14:45: six worktree sessions
Each session owns its modules and writes its own tests.

| Session | Owns | P0 deliverable | Next: P1/P2 |
|---|---|---|---|
| S1 Acquisition and linking | connectors, parse, ids, link | **Gold set by 17:00:** one row per notice for the 22 projects (RM id, notice no., OCID, part, contractor NIP, hand-verified, including the organizer data errors). All 22 linked or queued. `links.csv`; reruns idempotent | Auto-tier harvest from the zip; TED, KRS, KIO, BK2021 |
| S2 Extraction and documents | extract, documents | Rule events; causes with quotes; PDF/DOCX fragments; completeness | NIK lessons (P0 part: 1–2 reports); re-analysis diff; mitigation rules; batch causes; OCR (P2) |
| S3 Analysis | analysis, export | **New-investment fixtures by 19:00** (3 descriptions + 1 PDF). Features, neighbours with breakdown, ranges, assessment, flags, clauses, records, JSON/CSV | Embeddings; DOCX report; legal-basis insight; P2 Monte Carlo refit |
| S4 Frontend | frontend | Areas 2, 3 and 4 on the contract, with mocks first | Areas 1 and 5; graph; PDF highlight; polish |
| S5 Expert, knowledge, LLM | review, knowledge API, llm providers | Review + audit + table editor + learning loop; anthropic, openai, gemini and ollama providers + cache | Routing UI; roles; sandbox/reset |
| S6 Ops and deliverables | docker, monitor, docs, CI | **Test deploy at 15:00** (local docker if no host yet); live URL by 18:30 | Monitoring + as_of replay; OCDS/MCP; docs, test-report generator, slide and video script |

### Checkpoints
At each one, this session merges with your OK, redeploys and updates `docs/status.md`.

| Time | Gate |
|---|---|
| **19:00** | Path A end to end, live |
| **00:00** | Path B end to end; auto tier loaded |
| **05:00** | P1 done |
| **07:00** | Feature freeze; `make demo` from scratch; replay cache filled |

### Submission (07:00–10:30)
- Docs, PDF (≤10 slides), **you record the video at 08:00** (≤3 min).
- README with the criteria table and the disclosure (prep material, skills, Claude Code).
- **Code freeze 09:30.**
- Then preflight, `video_check.sh --max 175` and an incognito test; make the repo public (with your OK) and
  **submit at 10:30**.

### Parallel-work rules
- Only Phase 0 changes the schema. Later changes are a single migration made through this session.
- Each domain has its own router file.
- The frontend works against the contract only.
- `make test` must pass before a session reports done.

## 8. Criteria and tests → what we show

| Test / criterion | Shown by |
|---|---|
| Integration (20%) | Live "Wzbogać" run, op log of real queries, counts, rerun with no duplicates |
| Linking | `links.csv` (method, confidence, components with evidence, status) + precision/recall on our gold set in Jakość |
| Completeness | Oława chain; Biecz lot 1; Nowogard with 2 changes (R03, R02) |
| Documents and events (20%) | Click an event → highlighted section, page or paragraph; NIK lessons; proposed category |
| Source test | Evidence chip on every item, including calculations (inputs + formula) and xlsx cells |
| Expert work (20%) | Fix Wolin RM-2026-022 live; bulk-confirm; history; knowledge editor |
| New investment (25%) | The jury's own description: neighbours with breakdown → ranges with n/CI → budget/schedule percentiles → flags → clauses → DOCX/JSON |
| Scalability (15%) | Auto tier of thousands of procedures; knowledge import from docx (new sector = new files); connector registry; LLM routing |

## 9. Deliverables checklist
- Live URL with demo accounts.
- README (hn-zgloszenie template).
- `docs/opis_rozwiazania.pdf` (≤10 pages, "działa" vs "zaprojektowane").
- Tech docs with a mermaid architecture diagram and ERD.
- Generated `docs/raport_z_testu.md`: correct / uncertain / wrong links, the organizer data errors found, and the
  new-project analysis.
- `exports/przyklad/`.
- `.env.example` + `settings.example.yaml` (data location per profile, licence).
- `LICENSES-THIRD-PARTY.md`.
- PDF of at most 10 slides.
- Video (≤3 min, open link).
- Disclosure section.

## 10. Verification
- **`make test`:**
  - ids;
  - the DOM parser on the 22 projects' real notices (lots, changes, cross-references);
  - matcher precision and recall against the gold set;
  - event rules;
  - quote check;
  - similarity and ranges determinism;
  - providers in replay;
  - the injection suite;
  - API contract tests.
- **Frontend:** typecheck and build, plus a Playwright smoke test of both paths.
- **`make demo`:** fresh DB → import → enrich → zip harvest (sample) → extract → analyse the fixtures →
  export → report. Counts must match the gold set; a second run creates no duplicates, and expert decisions
  survive the rebuild.
- **Offline:** `LLM_MODE=replay` with the raw store. Each LLM step falls back to `none`.
- **Before submitting:**
  - `python3 setup/prep/_wspolne/.claude/skills/hn-zgloszenie/scripts/preflight.py <repo> --check-links`;
  - `video_check.sh --max 175`;
  - an incognito test from another device.

## 11. Mentor questions (first hour)
1. Which levels and identifiers make up the link reference set? Will KPO-only rows be tested?
2. Will the test investment come as a description or as documents, and for which subsector? Can we get a
   sample?
3. Is the mirror OK for the integration test? (The base URL is configurable.)
4. Is the rule `IW.nn` = 12 + TERYT/2 correct?
5. Will CST2021 numbers or documents (SWZ/PFU/PPU/aneksy) for the 22 projects be provided? If not, may we
   upload ones we download ourselves?
6. Where is the FAQ? May the expert docx files go into our public repo?
7. Is LLM processing outside the EU acceptable for public data?

## 12. Main risks

| Risk | Mitigation |
|---|---|
| Scope is 45–60 h of work | 6 sessions; P0 gate at 19:00/00:00; P1/P2 only after the gates pass |
| Merge conflicts | Schema and contract frozen in Phase 0; module ownership; merges only in this session |
| Mirror outage or end of event | Zip + raw store; permanent ezamowienia URLs; fallback to the official API at 30/min |
| LLM cost or outage | Per-task fallback profiles; `none`; replay cache |
| Jurors editing shared data | Sandbox copy + reset |
| Host bought late | Local docker test; Hetzner by 15:00; deploy redone at every checkpoint |
| Natural-person contractors | Masked by default (research/05) |
