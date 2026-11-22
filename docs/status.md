# Status (działa / zaprojektowane / problemy)

Updated by each session; merged by the main session at checkpoints.

## Phase 0 – foundation (main session, 21.11 ~16:15)
**Działa**
- Repo scaffold, docker compose (db/api/worker/web/caddy), Makefile, CI, `.env.example`, `config/settings.example.yaml`.
- Full Postgres schema (30 tables) + migration 0001 (pgvector, pg_trgm, unaccent).
- API contract: 70 endpoints (Pydantic schemas + router stubs returning 501 until implemented); `/api/settings/llm`, `/api/evidence`, `/api/jobs` implemented.
- Shared infra: uuid5 ids, NIP/REGON/BZP/KPO validators, `upsert_reviewable` (expert data never overwritten), evidence helpers, op_log, DB job queue + worker.
- LLM layer: `complete(task, messages, schema)` with per-task fallback chain, cache (live/cache/replay), repair retry, llm_call log, `wrap_untrusted`, PII strip; provider `none`. Other providers: stubs (S5).
- Knowledge import: `riskminer knowledge import <docx>` → 11 YAML tables (R01–R15, 6 subsectors, 8 phases, 25 doc types, event→source, art. 455, porady, 9-point checklist …) + team drafts in `extra/`.
- Frontend scaffold: layout with 5 navigation areas (Polish), typed client from OpenAPI, 501→mock fallback, data-location banner.
- Fixtures: 988 real notices of the 20 beneficiaries (from the organizer zip); prep notices/gold/holdout reason sets.

**Open (user)**: HackTribe task selection (by 20:00) · mentor questions (`docs/pytania_do_mentorow.md`) · API keys in `.env` · host (Hetzner) · GitHub repo (no `gh` CLI on this machine).

## Checkpoint 19:00 (main session, 21.11 ~19:00)
All six branches merged into `main` (sessions stopped at 17:48 on the usage limit; their uncommitted WIP was
committed on their branches first). Main session wired the missing CLI/jobs/routers.

**Działa (sprawdzone na bazie `riskminer`)**
- Ścieżka A od końca do końca: `riskminer import-xlsx` → `riskminer enrich` (na żywo: 156 zapytań do lustra BZP,
  952 ogłoszenia, 371 postępowań; zapas: kopia organizatora per NIP) → powiązania 22/22, złoty zbiór
  P = R = 1,0 (76/76 ogłoszeń, 0 wabików) → `riskminer extract` (83 zdarzenia z reguł, kompletność, problemy danych)
  → `riskminer links-csv` (`exports/links.csv`).
- API ścieżki A (wcześniej 501): projekty (lista z filtrami i statusem powiązania, karta, edycja z audytem, oś czasu
  plan vs wykonanie, graf relacji, postępowania, umowy ze zmianami, ogłoszenia z sekcjami), powiązania (lista,
  links.csv, kandydaci z rozbiciem, ręczne przepięcie z regułą override i pobraniem ogłoszenia), import xlsx,
  zlecenia `enrich`/`harvest`, zdarzenia (lista, edycja z audytem), problemy danych, kompletność, `extract` (zlecenie),
  ponowna analiza jako diff (nowe / potwierdzone / zmienione / zamknięte), kategorie ryzyka, lekcje, dokumenty
  (upload, z URL, fragmenty, plik dla PDF.js, wyszukiwanie pełnotekstowe).
- Ścieżka B: klasyfikacja bazy przypadków (`riskminer classify`), czerwone flagi z uzasadnieniem (historia zdarzeń
  sąsiadów, zakresy, ocena budżetu/harmonogramu, sygnały i braki w opisie, lista kontrolna eksperta), działania
  (klauzule K-R01…K-R15 – projekt zespołu do zatwierdzenia, lekcje NIK, wzorcowe zdarzenia), zapis analizy jako
  elementy do akceptacji (decyzje eksperta przeżywają przeliczenie, wykluczenie sąsiada → przeliczenie),
  eksport karty analizy JSON/CSV/DOCX, eksport dowolnego zbioru JSON/CSV i paczka `bundle.zip`
  (`riskminer export` → `exports/przyklad/`). `riskminer analyse <plik>` na fixture 01: 12 sąsiadów, 16 flag.
- Frontend: lista „Baza przypadków” działa na prawdziwym API.

**Warstwa automatyczna (21.11 ~19:50)**
- `riskminer harvest`: 113 276 ogłoszeń z kopii BZP organizatora (strumieniowo z .xz, bez rozpakowania), 45 069 postępowań,
  34 399 projektów automatycznych (postępowania z umową lub unieważnieniem); 16,7 min; 2 uszkodzone rekordy pominięte
  (data w polu liczbowym, znak \u0000). Baza ~4 GB. Harvest pomija NIP-y warstwy pogłębionej (te ogłoszenia pobiera `enrich`
  na żywo – zachowanie pochodzenia „BZP API”).
- `riskminer classify`: podsektor / rodzaj robót / formuła / skala z tytułu i opisu (reguły), CPV jako zapas.

**Lokalny Bielik (21.11 ~21:00)**
- Model lokalny jest pierwszym wyborem dla wszystkich zadań LLM (`[local_bielik, claude, rules]`): dokumenty nie opuszczają
  serwera; baner „Przetwarzanie LLM: lokalnie”. Model `riskminer-bielik` = Bielik 11B v3.0 Q4_K_M + kontekst 8k
  (`deploy/ollama/Modelfile`), Ollama na GPU; `docker compose --profile bielik` / `deploy.sh --bielik` na serwerze z GPU.
- Sprawdzone na żywo (RTX 4060 8 GB, 70% na GPU, ~15 tok/s): przyczyny zdarzeń ~12–14 s/zdarzenie (Nowogard: R03 i R02
  zgodne z regułami, cytaty dosłowne); cechy inwestycji ~1–1,5 min (wartości tylko z cytatem; przy niezgodności z regułami
  zostają reguły + notatka); podsumowanie analizy i 5 działań ~1 min – wszystkie liczby zgodne z obliczeniami.
- `riskminer extract --llm` na warstwie pogłębionej: 42 wywołania Bielika, 0 błędów (~15 s/zdarzenie); 36 zdarzeń z
  klasyfikacją modelu (dowód: model, wersja promptu, zweryfikowany cytat), 6 zostało przy regułach (bramka cytatu).
- Hosting: `docs/hosting.md` (rekomendacja: Scaleway L4 w Warszawie na czas oceny; zapas: Hetzner CX + pamięć odpowiedzi).

**Frontend (21.11 ~20:00)** – wszystkie obszary na prawdziwym API:
- Karta projektu: przegląd z komórkami xlsx, oś czasu plan vs wykonanie, powiązania (składowe ze źródłami, alternatywy,
  kandydaci, „Wskaż inne postępowanie”), umowy i zmiany, zdarzenia z cytatami i decyzją eksperta, ogłoszenia z sekcjami,
  dokumenty (upload / URL), braki i sprzeczności (4 stany eksperta), graf relacji, historia, ponowna analiza (diff).
- Kolejka eksperta (typy, najmniej pewne na górze, zatwierdzanie hurtowe), wiedza ekspercka (edycja, wersje, przywracanie).
- Nowa inwestycja → analiza: cechy ze źródłem i pytaniem netto/brutto, podsumowanie (n, CI), flagi z uzasadnieniem,
  działania i klauzule, budżet i harmonogram, zakresy, sąsiedzi z rozbiciem + wykluczenie i przeliczenie, eksport DOCX/JSON/CSV.
- Start (liczniki), Źródła i operacje (konektory, dziennik zapytań, jakość dopasowania, routing LLM, monitorowanie,
  licencje, eksport ZIP), „Jak testować” (scenariusze dla jury wg kryteriów).

**Znane problemy / do zrobienia**
- Przypadki pogłębione nie mają podsektora do czasu `riskminer classify`; P(zmiana) na samych 22 projektach jest
  zawyżone (próba organizatora) – po załadowaniu warstwy automatycznej zakresy liczone z ~20 tys. umów.
- Źródła publiczne poza BZP (22.11): KPOŚK (dane.gov.pl, 19/22 projektów dopasowanych do aglomeracji), TED API v3 (22 zapytania, 73 ogłoszenia robót tych samych zamawiających), Biała lista VAT (41 podmiotów) i KRS (12 odpisów) – `riskminer sources`, zadanie `sources`, karta projektu → „Inne źródła publiczne”, `GET /api/projects/{id}/public-sources`. KIO, Baza Konkurencyjności 2021 i raporty NIK – zaprojektowane, nie wdrożone (KIO: wyniki tylko przez formularz JS; BK2021: API wymaga logowania).

## Przed zamrożeniem (22.11 ~02:00)
**Działa**
- Dokumenty organizatora wgrane do projektów: protokół konieczności Zagrodno (RM-2026-002, +1 mies.: kolizja z siecią,
  wody gruntowe) i Zławieś (RM-2026-005, termin 30.10 → 05.12.2025, roboty dodatkowe 151 481,54 zł); z protokołów i
  aneksów reguły odczytują nowy termin, koszt i przyczynę z cytatem (`extract_document_effects`).
- Decyzje eksperta przez API (historia w `review`): 15 powiązań po identyfikatorze zatwierdzonych hurtowo (7 dopasowanych
  po podobieństwie czeka na jury), 5 zdarzeń zatwierdzonych, 4 wzorcowe (używane w działaniach analizy), 3 poprawione
  kody ryzyka, 8 szumowych sygnałów z dokumentów odrzuconych z uzasadnieniem.
- `riskminer report`: ocena wzorcem tylko dla 22 projektów organizatora (P = R = 1,0), sekcja zdarzeń i dokumentów,
  czytelne wyniki analiz; README i opis rozwiązania bez pól `{{…}}`.

**Znane problemy**
- ~~Pismo Grodzisko bez OCR~~ – rozwiązane 22.11 ~07:00, zob. niżej.
- Reguły sygnałów z dokumentów dają szum (nagłówki, dane stron umowy); ekspert je odrzuca, filtr w regułach do zrobienia.

## OCR skanów (22.11 ~07:00)
**Działa**
- PDF bez warstwy tekstowej → pypdfium2 renderuje strony (300 dpi) → Tesseract 5 (`pol`) → akapity ze stroną;
  każdy fragment ma w lokatorze `ocr: true` i pewność rozpoznania, dokument `text_status = ocr` i `meta.ocr`
  (silnik, język, dpi, średnia i per strona). Dalej to samo co dla PDF z tekstem: sygnały ryzyka, skutki, wyszukiwanie.
- Silnik jako zewnętrzne polecenie z `ocr.command` (obraz backendu ma `tesseract-ocr-pol`; na hoście bez binarki
  obraz `deploy/ocr/Dockerfile` → `[docker, run, --rm, -i, riskminer-ocr]`). Bez silnika: jak wcześniej, `ocr_needed`.
- `riskminer ocr` czyta zapisane skany. Grodzisko (RM-2026-010): 1 strona, 2,6 s, pewność 94,9%, 2 sygnały do eksperta (R04, R01).

**Znane problemy**
- Cytat z OCR nie jest podświetlany na obrazie skanu (PDF.js nie ma warstwy tekstu) – otwiera się właściwa strona.
- Upload przez API korzysta z OCR dopiero po restarcie API i workera (nowy kod).

## Embeddingi w podobieństwie (22.11 ~07:30)
**Działa**
- `analysis/embeddings.py`: paraphrase-multilingual-MiniLM-L12-v2 przez fastembed (ONNX, CPU, Apache-2.0), model w
  `data/models/`; wektory 18 068 przypadków wodno-kanalizacyjnych w `data/models/vectors-*.npz` (6,5 min raz; potem tylko nowe/zmienione,
  do 300 inline). W czasie zapytania model ładowany tylko z plików lokalnych (bez pobierania).
- Komponent `embedding` (waga 0,10 z `similarity_weights`) w `find_neighbours`; bez modelu wypada z wyniku (wagi się
  normalizują), powód w `embeddings.note`. Przykład „kanalizacja sanitarna”: 11/12 sąsiadów bez zmian, +0,6 s.
- `riskminer embed` (pobiera model przy pierwszym uruchomieniu i liczy wektory).

**Znane problemy**
- Działające API korzysta z embeddingów dopiero po restarcie. Na serwerze trzeba raz uruchomić `riskminer embed`.

## S1 Acquisition & linking
## S2 Extraction & documents
## S3 Analysis
## S4 Frontend
## S5 Expert, knowledge, LLM
## S6 Ops & deliverables
**Działa**
- Stos produkcyjny docker compose (db, api z `alembic upgrade head`, worker z APScheduler, web, Caddy z auto-HTTPS); healthchecki; porty konfigurowalne (test lokalny `deploy/local-prod-test.sh`, projekt `rmtest`, :8088); dane trwałe w `pgdata`, `data/`, `exports/`.
- Skrypty wdrożenia na Hetzner: `deploy/deploy.sh user@host [--bootstrap --with-data --demo]` (docker, ufw, `.env` z losowymi sekretami, `<ip>.sslip.io`, test dymny), `make deploy`.
- Router `ops`: dashboard (liczby wg tabel i poziomów, ostatnie zadania, alerty, miejsca przetwarzania), dziennik zapytań z filtrami, stan konektorów (działa/zaprojektowane), zużycie LLM, licencje, alerty (+ oznacz jako przeczytany), obserwacja i uruchomienie monitoringu; `/quality` wywołuje `riskminer.link.quality` (S1), bez niego 501.
- Monitoring: obserwowane postępowania, przebieg live (okno dni z lustra BZP, filtr OCID po stronie klienta) i odtworzenie `as_of` z bazy; alerty nowe ogłoszenie / przekroczony termin / jakość danych („Zakończone” bez ogłoszenia o wykonaniu); zlecenie `reanalyze` (S2), jeśli zarejestrowane; alerty idempotentne (uuid5).
- `riskminer demo` (kroki pozostałych sesji wywoływane po nazwie i pomijane, gdy ich brak; kontrola duplikatów względem poprzedniego przebiegu; zapasowy eksport; raport; złoty zrzut), `riskminer report` → `docs/raport_z_testu.md`, `riskminer snapshot save|restore` (COPY, bez pg_dump – do resetu piaskownicy S5), `riskminer licences --check` (0 GPL/AGPL; psycopg LGPL opisany), `riskminer docs-gen` (ERD mermaid z `tables.py`), `riskminer monitor probe` (dostęp do lustra i ezamowienia.gov.pl: HTTP 200 z własnym UA, sprawdzone z hosta).
- Dokumenty: `uruchomienie.md`, `architektura.md`, `erd.md`, `zrodla_i_dopasowanie.md`, szkielet `opis_rozwiazania.md`, `prezentacja_plan.md`, `wideo_scenariusz.md`, README wg szablonu hn-zgloszenie, `LICENSES-THIRD-PARTY.md`.
- CI: job `docker` (build obrazów backend/web, walidacja compose) + sprawdzenie licencji.

**Zaprojektowane**
- Ponowna analiza jako diff (zależy od S2 `reanalyze`); metryki `/quality` od S1.
- Wpisanie liczb z raportu do README / opisu przy zamrożeniu (pola `{{…}}`).

**Znane problemy**
- Test pełnego stosu prod w dockerze nie został ukończony: dysk główny hosta zapełnił się podczas budowania (21.11 ~17:40); czeka na zwolnienie miejsca.
- `riskminer demo` uruchomione na pustej bazie S6 – kroki S1–S5 pominięte, bo ich polecenia nie są jeszcze scalone.
