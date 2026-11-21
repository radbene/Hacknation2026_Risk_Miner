# RISK MINER: notatki techniczne o źródłach danych (stan na 2026-11-16)

Autor: inżynier danych (agent). Hackathon HackNation 2026: 21-22.11.2026.

## 0. Jak czytać ten plik (WAŻNE)

**Z tej maszyny nie było dostępu do internetu poza GitHubem i PyPI, więc NIE widziałem żadnej surowej odpowiedzi żadnego API.** Wszystko poniżej pochodzi z (a) stron dokumentacji otwartych przez WebFetch, (b) fragmentów kodu i dokumentów w repozytoriach GitHub, znalezionych przez `gh search code` (czytałem tylko fragmenty z wyników wyszukiwania, bo próba dołączenia repozytoriów przez `add_repo` nie została zatwierdzona), (c) wyników WebSearch.

Znaczniki:
- **[✔]** widziałem w dokumentacji/stronie, którą otworzyłem (WebFetch) w tej sesji.
- **[~]** źródło wtórne (repozytorium, blog, opis aktora Apify): podaję link/repo. Nie uruchamiałem cudzego kodu.
- **[?]** z pamięci, niepotwierdzone.

Statusy źródeł (zgodnie z Twoją skalą): "widziałem prawdziwą odpowiedź" nie dotyczy żadnego źródła. Używam: **tylko dokumentacja** (jest spec/strona, nie ma odpowiedzi) albo **niepotwierdzone**.

Pierwsza rzecz do zrobienia w sobotę (albo wcześniej, z maszyny z internetem): po jednym zapytaniu `curl` do każdego z kluczowych endpointów (BZP, TED, KRS, WL) i zapisanie surowych odpowiedzi do `samples/`. Komendy są w sekcji 9.

Uwaga o repozytoriach-źródłach: kilka z nich to prywatne projekty osób trzecich (np. `jjkiljanski/procurement-watchdog-lakehouse`, `GISBoost/mapy-analizy`, `neeti250826/Tender-Tool`, `michaleiatrak-star/Lex-Machina`). Traktuję je jako świadectwo wtórne, nie jako dokumentację. Część ich twierdzeń jest datowana na 2026-09/10 i dotyczy zachowania API w tamtym dniu.

---

## 1. e-Zamówienia / BZP (UZP)

### 1.1 Dwa różne "API", nie mieszać

| Co | URL | Dla kogo | Status |
|---|---|---|---|
| Publiczny odczyt ogłoszeń BZP ("mo-board") | `https://ezamowienia.gov.pl/mo-board/api/v1/notice` | każdy, bez klucza | [~] tylko dokumentacja wtórna |
| Ten sam backend co lista na stronie ("Board/Search") | `https://ezamowienia.gov.pl/mo-board/api/v1/Board/Search` | każdy, bez klucza | [~] |
| Oficjalny "BZP Webservice" (publikacja, OAuth 2.0) | `https://ezamowienia.gov.pl/mo-client-board/api/notices/` | tylko właściciele portali/systemów dziedzinowych po wniosku | [✔] Regulamin: https://media.ezamowienia.gov.pl/pod/2023/01/Regulamin-korzystania-z-API.pdf |

Dla nas liczy się wiersze 1-2. Wiersz 3 to API do **publikowania**, wymaga OAuth Client Credentials i zgody administratora, nie nadaje się na hackathon [✔].

Strona integracyjna UZP: `https://ezamowienia.gov.pl/pl/integracja/` (cytowana przez repozytoria; WebFetch jej nie otworzył: URL spoza listy dozwolonych). Cytat z niej w dokumencie `Twista-hub/jarvis` `docs/polen.md`: "Odczyt ogłoszeń ... nie wymaga przejścia procedury integracyjnej", limit 30/min [~] (patrz 1.5).

### 1.2 Endpoint `GET /mo-board/api/v1/notice` [~]

Przykład pełnego wywołania (złożony z parametrów potwierdzonych w trzech niezależnych miejscach, patrz źródła niżej; **nie wykonany**):

```
curl -sS "https://ezamowienia.gov.pl/mo-board/api/v1/notice?NoticeType=ContractPerformingNotice&PublicationDateFrom=2026-10-01T00:00:00&PublicationDateTo=2026-10-02T00:00:00&PageSize=500"
```

Parametry zapytania:
- `NoticeType` [~] (wymagany; jeden typ na zapytanie), `PublicationDateFrom`, `PublicationDateTo` (oba wymagane; bez `PublicationDateTo` HTTP 400) [~ GISBoost/mapy-analizy `remonty/zrodla_zdit_bzp_ted.md`]. Format czasu użyty w kodzie: `2026-10-01T00:00:00` [~ GISBoost `remonty/bzp_fetch.py`].
- `PageSize`: w OpenAPI `maximum: 500, minimum: 0` [~ `jjkiljanski/procurement-watchdog-lakehouse` `refs/bzp_api/bzp.external.API.yaml`]. Ten sam klient używa `PAGE_SIZE = 500` (`src/procurement/fetch/bzp_api.py`).
- `SearchAfter` (string): kursor stronicowania [~ ta sama spec YAML i `bzp_api.py`].
- `CpvCode`, `OrganizationName` (dopasowanie **podciągu**, nie równość), `NoticeNumber` [~ spec YAML]; `OrganizationCity` [~ GISBoost]; `SearchText` [~ `qa10devteam/behive` `src/behive/engine/hive_api_sources.json`].
- Filtr po NIP: **API ignoruje NIP**, trzeba filtrować lokalnie [~ GISBoost `remonty/PROCES.md`].

Typy ogłoszeń (`NoticeType`), nazwy dosłownie, potwierdzone w kodzie klientów [~]:
`ContractNotice`, `TenderResultNotice`, `ContractPerformingNotice` ("Ogłoszenie o wykonaniu umowy"), `AgreementUpdateNotice` ("Ogłoszenie o zmianie umowy"), `NoticeUpdateNotice` (zmiana treści ogłoszenia), `AgreementIntentionNotice`, `SmallContractNotice`, `CompetitionNotice`, `ConcessionNotice`, `CircumstancesFulfillmentNotice`. Repozytorium `jjkiljanski/...` mówi o 14 typach (`scripts/pipeline/build_silver_range.py`), pełna lista DO WERYFIKACJI w enumie Swaggera (nie znalazłem fragmentu z enumem).
Źródła nazw: `wiktorKycia/BidBot` `etl/scrapers/ezamowienia/models.py` (polskie nazwy typów), `jjkiljanski/...` `src/procurement/bronze/models.py`, `GISBoost/mapy-analizy` `remonty/bzp_fetch.py`.

### 1.3 Endpoint `GET /mo-board/api/v1/Board/Search` [~]

Używany przez stronę. Parametry (nazwy z kodu): `noticeType`, `isTenderAmountBelowEU` (true/false), `PageNumber`, `PageSize`, `SortingColumnName` (np. `PublicationDate`), `SortingDirection` (`ASC`/`DESC`) [~ `neeti250826/Tender-Tool` `poland-ezamowienia/README.md`, `ezamowienia_scraper.py`]. Opis aktora Apify: "at most 10 notices per page" i że **nie zwraca** `htmlBody` [~ https://apify.com/mrarcode/bzp-scraper.md]. Do analizy używać `/notice` (ma `htmlBody`). PDF ogłoszenia: `GET /mo-board/api/v1/Board/GetNoticePdfById?noticeId=<GUID>` [~ Tender-Tool].

### 1.4 Format odpowiedzi i pola (dosłownie)

JSON. Pola poziomu ogłoszenia: `objectId`, `noticeType`, `noticeNumber`, `bzpNumber`, `publicationDate`, `isTenderAmountBelowEU`, `orderObject`, `orderType`, `tenderType`, `tenderId`, `cpvCode`, `clientType`, `organizationName`, `organizationCity`, `organizationProvince`, `organizationCountry`, `organizationNationalId`, `organizationId`, `submittingOffersDate`, `procedureResult`, `contractors[]`, `htmlBody` [~ `jjkiljanski/...` `docs/data_model/data_profile.md`, `build_bronze.py`; GISBoost `bzp_fetch.py`].
Elementy `contractors[]`: `contractorName`, `contractorCity`, `contractorProvince`, `contractorCountry`, `contractorNationalId` [~ `src/procurement/bronze/models.py`; opisy "Krajowy numer identyfikacyjny wykonawcy" w spec YAML].
Opisy z OpenAPI (polskie): `tenderId` = "Identyfikator postępowania", `bzpNumber` = "Numer BZP", `organizationNationalId` = "Krajowy numer identyfikacyjny zamawiającego" [~ spec YAML]. Uwaga: "krajowy numer identyfikacyjny" to nie zawsze NIP (może być REGON; u osób fizycznych PESEL), patrz sekcja 10.
`cpvCode` to tekst z opisem, np. "45233140-2 Roboty drogowe" [~ GISBoost].
Odpowiedź w klientach GISBoost jest traktowana jako **lista** obiektów (iteracja po `d`, ostrzeżenie gdy `len(d) >= 500`), a klient `jjkiljanski` używa `SearchAfter`. Skąd wziąć wartość kursora: DO WERYFIKACJI (pierwsze wywołanie z `PageSize=2`). Sprawdzony w praktyce wzorzec zastępczy: okna czasowe (dzień/godzina) i dzielenie okna, gdy wynik ma 500 pozycji [~ GISBoost `bzp_fetch.py`: okna miesięczne, ostrzeżenie o obcięciu].

### 1.5 Limity, uwierzytelnianie, licencja

- Klucz: **nie** [~ kilka repozytoriów; `Twista-hub/jarvis` `docs/polen.md`: "ohne Anmeldung"].
- Limit: `Twista-hub/jarvis` `docs/polen.md` podaje "30 Abrufe pro Minute und IP (seit 06.10.2026)" oraz "ab 11.01.2027 höchstens 100 Datensätze pro Seite", z adnotacją "live geprüft 02.11.2026: Integrationsseite ... Limit 30/min" [~, jedno źródło wtórne, nie zweryfikowałem na stronie UZP]. Inne źródło: "The BZP API has no published rate limit" (`jjkiljanski/...` `docs/runbooks/OPERATING_MODES.md`) [~], więc dokumentacje się rozjeżdżają w czasie. **Zakładaj 30 zapytań/min/IP (ok. 1 zapytanie na 2 s) i PageSize 500 do końca 2026, potem 100.** Przy 2 osobach na jednym łączu limit dzielicie.
- Warunki: oficjalny Regulamin API (PDF powyżej) dotyczy usług z OAuth; zawiera zakaz anonimowego użycia usług (§5 ust. 1) i bezpłatność Webservice [✔]. Czy odnosi się do anonimowego odczytu `/mo-board/api/v1/notice` nie jest rozstrzygnięte (DO WERYFIKACJI). Rekomendacja: ustawić `User-Agent` z nazwą zespołu, nie przekraczać limitu, podawać źródło.
- Ponowne wykorzystanie: `Twista-hub/jarvis` `docs/polen.md` wnioskuje, że wykorzystanie komercyjne jest dopuszczalne na podstawie ustawy o otwartych danych [~]. Nie jest to licencja CC; brak oficjalnego tekstu, który bym otworzył.
- Swagger/OpenAPI: spec istnieje (kopia w `jjkiljanski/procurement-watchdog-lakehouse` `refs/bzp_api/bzp.external.API.yaml` [~]); oficjalny adres Swaggera DO WERYFIKACJI (zacznij od `https://ezamowienia.gov.pl/pl/integracja/`).

### 1.6 Zakres dat, aktualność, wolumen

- Nowa BZP (e-Zamówienia) działa od 2021. Próba 2018 zwróciła `[]`; dla 2018-2020 potrzebna stara BZP `bzp.uzp.gov.pl` [~ GISBoost `zrodla_zdit_bzp_ted.md`]. Stara BZP jest w gorszym stanie (ok. 20% żądań 404) [~ Lex-Machina `shared/DOSTEP-MASZYNOWY-API.md`].
- Wolumen od 2024 do 2026-06-03 (liczby ogłoszeń, nie unikalnych postępowań): `ContractNotice` 322 142, `TenderResultNotice` 337 962, `ContractPerformingNotice` 591 101 [~ `neeti250826/Tender-Tool` `Poland/docs/ezamowienia-gov-pl_notes.md`]. Szacunek "ok. 520 ogłoszeń na dzień roboczy" [~ jarvis].
- Pułapka: `htmlBody` bywa wielomegabajtowy; ogłoszenia o wykonaniu umowy mogą pojawić się wielokrotnie dla jednego postępowania (część/umowa).

### 1.7 HTML i wyciąganie wartości, ofert, terminów

Wszystkie szczegóły (wartość, oferty, terminy, zmiany) siedzą w `htmlBody`, nie w polach JSON. Parsowanie jest rzeczą do zrobienia samemu. Przykład wyrażenia wartości w HTML: `<span class="normal">184430,40 PLN</span>` (przecinek jako separator dziesiętny, spacje twarde) [~ `jjkiljanski/...` `docs/data_model/html_structure.md`]. Szacunkowa wartość podana tylko w ok. 13% ogłoszeń o zamówieniu [~ ta sama dokumentacja].

Gotowa mapa sekcji (nagłówki dosłownie, numeracja sekcji zależy od typu ogłoszenia) z projektu `jjkiljanski/procurement-watchdog-lakehouse` `src/procurement/silver/notice_schemas/*_profile.json` [~]:

**ContractPerformingNotice** (ogłoszenie o wykonaniu umowy):
- 4.1 "Data zawarcia umowy"
- 4.4 "Wartość umowy"
- 5.1 "Czy umowa została wykonana"
- 5.2 "Termin wykonania umowy"
- 5.3 "Czy umowę wykonano w pierwotnie określonym terminie" (przykładowa wartość: "Tak")
- 5.4.1 "Liczba zmian"
- 5.4.4 "Przyczyny dokonania zmian" (tekst swobodny, np. "Konieczność wykonania robót dodatkowych ... (roboty dotyczą lub wynikają z elementów zakrytych)")
- 5.4.6 "Wartość zmiany"
- 5.5 "Łączna wartość wynagrodzenia wypłacona z tytułu zrealizowanej umowy" (przykład: "278100 PLN")
- osobne wiersze `change_matter` ("Numer zmiany", "Podstawa prawna zmiany", ...), 1 wiersz na zmianę.
Wg ich README parser ekstrahuje 4.4 i 5.5 w 100% (to skuteczność parsera, nie kompletność danych) .

**AgreementUpdateNotice** (ogłoszenie o zmianie umowy):
- 2.1 "Ogłoszenie dotyczy zmiany"
- 4.3 "Dane wykonawcy, z którym zawarto umowę/umowę ramową"
- 4.4 "Wartość umowy/umowy ramowej"
- 5.3 "Przyczyny dokonania zmian umowy/umowy ramowej" (przykład: "Wydłużenie terminu realizacji prac")
- 5.5.1 "Wartość zmiany"
Reszta nagłówków (nowy termin, wartość po zmianie) DO WERYFIKACJI w pliku `agreement_update_notice_profile.json`. W ich próbie 1 247 takich ogłoszeń na ok. 97 tys. ogłoszeń (1,3%), czyli rzadkie [~ `data_profile.md`, okno dat tej próby nieznane].

**TenderResultNotice**: 4.3 "Wartość zamówienia", 4.3.1 "Wartość zamówienia stanowiącego przedmiot tego postępowania (bez VAT)", 6.1.x liczby ofert (np. 6.1.2 "Liczba ofert dodatkowych", 6.1.4 "Liczba ofert wykonawców z siedzibą w państwach EOG innych niż państwo zamawiającego"), 8.1 "Data zawarcia umowy" (sekcje częściowe). Nagłówek łącznej liczby ofert (do liczenia "jedna oferta" jako czerwonej flagi): DO WERYFIKACJI.

**ContractNotice**: 4.1.6 "Wartość zamówienia stanowiącego przedmiot tego postępowania (bez VAT)" (przykład: "438165,04 PLN"). Termin składania ofert jest też w polu JSON `submittingOffersDate`.

### 1.8 Co z tego jest etykietą opóźnienia/przekroczenia kosztów

To jest najlepszy kandydat, jaki znalazłem. Ogłoszenie o wykonaniu umowy daje (w tekście): pierwotną wartość (4.4), łączną zapłaconą kwotę (5.5), czy wykonano w pierwotnym terminie (5.3), liczbę i przyczyny zmian (5.4.x) i faktyczny termin wykonania (5.2).

Etykiety do zbudowania:
- opóźnienie: `5.3 == "Nie"` (etykieta samodeklarowana przez zamawiającego), dodatkowo `5.2` vs termin z `ContractNotice`/umowy;
- przekroczenie kosztów: `5.5 / 4.4 - 1` (uwaga na VAT/brutto/netto: nie wszędzie jednolicie, DO WERYFIKACJI na próbce 50 ogłoszeń) lub suma `5.4.6`.
Łączenie ogłoszeń: po `tenderId` ([~] GISBoost `remonty/pipeline/e5_bzp_match.py` grupuje po `tender_id`; `jjkiljanski` używa `caseId = coalesce(tenderId, objectId)`).
Pułapki jakości etykiety (do powiedzenia jury wprost):
1. Obowiązek publikacji i zakres progowy ogłoszeń o wykonaniu umowy: DO WERYFIKACJI w ustawie Pzp (z pamięci [?]: dotyczy zamówień powyżej progów unijnych; liczba 591 tys. od 2024 sugeruje szersze stosowanie albo wiele ogłoszeń na umowę).
2. Samodeklaracja (5.3) i tendencja do "Tak".
3. Brak ogłoszenia = nie znaczy "brak problemu" (cenzura/selekcja).
4. Wartości w tekście swobodnym, parser musi radzić sobie z formatami.
5. Zmiany ujęte w AgreementUpdateNotice a nie w Performing: łączyć oba.

---

## 2. TED (UE)

Status: **tylko dokumentacja** (strona docs.ted.europa.eu otwarta; nie widziałem odpowiedzi).

- Base: `https://api.ted.europa.eu`, struktura `https://api.ted.europa.eu/{api-version}/{resource}/{action}` [✔ https://docs.ted.europa.eu/api/latest/index.html].
- Search: `POST https://api.ted.europa.eu/v3/notices/search`, **anonimowo, bez klucza** [✔ https://docs.ted.europa.eu/api/latest/search.html i /index.html]. Klucz (EU Login → Developer Portal, jedno konto = jeden klucz) potrzebny tylko do endpointów z nieopublikowanymi ogłoszeniami [✔].
- Swagger: `https://api.ted.europa.eu/swagger` [✔]; Swagger UI wyszukiwania: `https://api.ted.europa.eu/swagger-ui/index.html#/Search/search` [✔ wymieniony na stronie, nie otwarty].
- Treść żądania: `query` (wymagane, składnia ekspercka), `fields` (wymagane, lista nazw z enuma) [✔ https://docs.ted.europa.eu/api/endpoints/ted-europa-eu.html]. Opcjonalne: `limit`, `page`, `scope`, `paginationMode`, `iterationNextToken` [✔/~ opis stronicowania na stronie; przykład z `scope`: "ACTIVE" w https://tenderapi-landing.pages.dev/en/blog/ted-search-api-guide/ [~]]. Wartości `scope` DO WERYFIKACJI w Swaggerze (z historii nas interesuje zakres obejmujący zamknięte ogłoszenia; "ACTIVE" ich nie zwróci).
- Przykład [~ blog powyżej, zmodyfikowany pod Polskę, **nie wykonany**]:

```
curl -sS -X POST https://api.ted.europa.eu/v3/notices/search \
  -H "Content-Type: application/json" \
  -d '{"query":"buyer-country=POL AND publication-date>=20260101","fields":["publication-number","notice-type","publication-date","classification-cpv"],"limit":100,"paginationMode":"ITERATION"}'
```
Wywołanie `buyer-country=POL` zwróciło 200 z `publication-number` i linkami pdf/xml w teście opisanym w `GISBoost/mapy-analizy` `remonty/zrodla_zdit_bzp_ted.md` [~]. Ten sam dokument: próby `buyer-name ~ ...` i `organisation-name-buyer=...` dały HTTP 400 (nazwy pól w składni eksperckiej trzeba brać z enuma, nie zgadywać).
- Stronicowanie [✔ docs.ted.europa.eu/api/endpoints/ted-europa-eu.html]: tryb strony (`limit`, `page`): max 250 ogłoszeń na stronę, max 15 000 ogłoszeń łącznie, max 10 000 pól na stronę (ogłoszenia x pola). Tryb iteracji (`paginationMode: "ITERATION"`, `iterationNextToken`): bez limitu łącznego, token wygasa 24 h po następnym wydaniu OJS. Odpowiedź: `notices`, `totalNoticeCount`, `iterationNextToken`. Błędy: `EXPIRED_ITERATION_TOKEN`, `INVALID_ITERATION_TOKEN`.
- Limity: zapytanie max 2 000 klauzul [✔ https://op.europa.eu/en/web/ted-reusers-workshops/questions_and_answers_2023_12_14]; limity wyszukiwania "na stronie Swaggera", liczb nie ma [✔ ta sama strona]; "calls are throttled", w przykładzie `sleep(1)` między stronami [~ blog].
- Pola (nazwy dosłownie, eForms): `publication-number`, `notice-type`, `publication-date`, `buyer-country`, `classification-cpv`, `estimated-value-proc`, `estimated-value-cur-proc`, `notice-title` (klucz językowy, np. `eng`) [✔/~ strony powyżej]. Pola modyfikacji: `modification-reason-description`, `modification-previous-notice-identifier`, `modification-modified-contract-reference`, `modification-part-reference`, `modification-description`, `modification-justification` (lista pól w `SzymonSt/salespatriot-agent` `data/ted_search_fields.txt`, `mvanhorn/printing-press-library` `library/sales-and-crm/eu-tenders/internal/cli/ted_fields.txt`, `mattahr/ha-edp-radar` `custom_components/edp_radar/normalizer.py` [~]). Dodatkowo `winner-name`, `tender-value`, `result-value-notice`, `change-reason-code`, `contract-identifier`, `title-proc`, `buyer-name` [~ `jakatora/przetargai` `firebase/functions/skrypty/sonda-ted-modyfikacje.mjs`]. Pełny enum: DO WERYFIKACJI w Swaggerze.
- Typy ogłoszeń: ogłoszenie o zmianie umowy w eForms ma kod `can-modif` (lista `cont-modif`) [~ `OP-TED/ted-rdf-mapping-eforms` `src/data/source_can-modif.xml`, `OP-TED/eForms-SDK`]. Inne kody widziane: `cn-standard`, `cn-social`, `cn-desg`, `subco` (ogłoszenia o zamówieniu), `can-standard` (o udzieleniu) [~ `Twista-hub/jarvis`, `atlasprzetargow/...`]. Składnia filtra `notice-type=can-modif`: DO WERYFIKACJI.
- Paczki hurtowe: dzienne i miesięczne `.tar.gz` z XML eForms bez logowania. Wzorzec adresu z bloga: `https://ted.europa.eu/packages/daily/{yyyynnnnn}` i `.../packages/monthly/{yyyy-nn}` [~ blog]; z Q&A Urzędu Publikacji: `https://{ted-url}/packages/notice/daily/{yyyynnnnn}` [✔ strona op.europa.eu]. **Rozbieżność wzorców: DO WERYFIKACJI.** Paczki zawierają stare i nowe formaty; po 31.01.2024 stary schemat tylko dla niektórych typów [✔].
- TED CSV (DG GROW): `https://data.europa.eu/data/datasets/ted-csv` (strona nie otwarta); wg README raportu ECA zbiór pobrany we wrześniu 2022 i obejmuje ogłoszenia 2011-2020 [✔ https://www.eca.europa.eu/OpenData/SR-2023-28/README.pdf]. Czy jest nowszy: DO WERYFIKACJI.
- Licencja: "reuse allowed" [~ `Twista-hub/jarvis` `docs/europa-markt.md`]; tekst licencji DO WERYFIKACJI (zwykle CC BY 4.0 lub zasady ponownego użycia Urzędu Publikacji UE).
- Zakres: TED zawiera tylko zamówienia **powyżej progów UE** [~ jarvis `docs/europa-markt.md`] — dla Polski to ułamek BZP. Pułapka: duplikaty z BZP (to samo ogłoszenie w obu), `Atlas Przetargów` flaguje `is_duplicate` [~].
- Wartość dla Risk Minera: ogłoszenia o zmianie (can-modif) z uzasadnieniem zmiany i polami wartości; ale tylko dla dużych zamówień.

---

## 3. Projekty unijne w Polsce

### 3.1 Lista projektów FE 2021-2027 i 2014-2020 (plik XLSX)

Status: **tylko dokumentacja/wtórne** (strony gov.pl zablokowane robots.txt dla WebFetch; nie otworzyłem plików).

- Strona 2021-2027: `https://funduszeeuropejskie.gov.pl/raporty-i-analizy/lista-projektow-realizowanych-z-funduszy-europejskich-w-polsce-w-latach-2021-2027` [~ stała `FE_PAGE` w `Hubert-Rybak/radar-ozarow` `scripts/investment_sources/private_catalog.py`; WebFetch odmówił]. Kod `discover_fe_link()` szuka na stronie linku `.xlsx` (atrybuty `href` lub `data-url`) o nazwie z `2021_2027`; przykład: `https://funduszeeuropejskie.gov.pl/wp-content/uploads/2026/10/Lista_projektow_FE_2021_2027_30092026-1.xlsx` [~ ten sam kod i testy]. Nazwa pliku niesie datę stanu (`30092026`).
- Pliki używane w innym projekcie: `Lista_projektow_FE_2021_2027_01022026.xlsx` i `Lista_projektow_FE_2014_2020_04012026.xlsx` [~ `aleksandrajaremko/Policy-paper` `code/processing/UE_funds_processing/eu_funds_pipeline.py`]. Czyli aktualizacja co miesiąc lub dwa (ostatnia znana: stan 2026-09-30).
- Lista 2014-2020 ma też strony miesięczne na gov.pl: "Lista projektów realizowanych z Funduszy Europejskich 2014-2020 - 30 czerwca 2026 roku", "... 31 maja 2026 roku" [✔ tytuły w wynikach WebSearch].
- Kolumny (nazwy dosłownie) wydrukowane przez notebook po wczytaniu pliku, z uwagą, że przypisanie do konkretnej listy robię z kontekstu [~ `aleksandrajaremko/Policy-paper` `eu_funds_pipeline_notebook.ipynb`]:
  - Zestaw A (najpewniej 2014-2020): 'Tytuł projektu', 'Skrócony opis [do 2000 znaków]', 'Numer umowy', 'Nazwa beneficjenta', 'Fundusz', 'Program', 'Priorytet', 'Działanie', 'Poddziałanie', 'Wartość projektu (w zł, dla projektów EWT w euro)', 'Wydatki kwalifikowalne (w zł, dla projektów EWT w euro)', 'Wartość unijnego dofinansowania (w zł, dla projektów EWT w euro)', 'Poziom unijnego dofinansowania w procentach (w %)', 'Forma finansowania', 'Miejsce realizacji projektu', 'Typ obszaru, na którym realizowany jest projekt', 'Data rozpoczęcia realizacji projektu', 'Data zakończenia realizacji projektu', 'Projekt konkursowy czy pozakonkursowy', 'Dziedzina działalności gospodarczej, której dotyczy projekt', 'Obszar wsparcia projektu', 'Cel projektu', 'Cel uzupełniający dla projektów EFS', 'Projekt realizowany w ramach terytorialnych mechanizmów wdrażania', 'Finansowanie zakończone'.
  - Zestaw B (najpewniej 2021-2027): 'Nazwa projektu', 'Opis projektu', 'Numer umowy', 'Nazwa beneficjenta', 'Nazwa wykonawcy kontraktu', 'Numer identyfikacyjny statku w rejestrze floty rybackiej UE', 'Fundusz', 'Cel szczegółowy', 'Program', 'Priorytet', 'Działanie', 'Wartość projektu (w zł)', 'Poziom unijnego dofinansowania w procentach (w %)', 'Dofinansowanie z UE (w zł)', 'Kurs EURO', 'Miejsce realizacji projektu', 'Data rozpoczęcia projektu', 'Data zakończenia projektu', 'Kategoria wsparcia'.
  Dopasowanie A/B do list: **DO WERYFIKACJI po pobraniu**. Notebook opisuje 2021-2027 jako "CST2021 / dane.gov.pl" i format lokalizacji `WOJ.: X, POW.: Y, GM.: Z` (z gminą), 2014-2020 jako "SL2014 / dane.gov.pl" i `WOJ.: X, POW.: Y` (bez gminy) [~].
- Daty rozpoczęcia i zakończenia: są (planowane/rzeczywiste, nie wiadomo, które; w zestawie 2007-2013 były osobne pola "Data rzeczywistego zakończenia", w nowych listach tego nie widać) [~].
- **Brak NIP beneficjenta w kolumnach powyżej.** Starsze listy 2007-2013 miały `NIP beneficjenta` [~ ta sama biblioteka funkcji w `_archive/GUS_processing_functions.py`]. To oznacza, że łączenie FE z BZP idzie po nazwie beneficjenta + lokalizacji (sekcja 10).
- 'Nazwa wykonawcy kontraktu' (zestaw B) może pozwolić na dopasowanie wykonawców (po nazwie, nie po NIP).
- Kody interwencji: kolumna 'Kategoria wsparcia' (zestaw B). Czy to pełne kody interwencji UE: DO WERYFIKACJI.
- Wariant CSV z separatorem `;` istniał dla 2014-2020 (`csv_Lista_projektow_FE_2014_2020_030923.csv`) [~ `SuddenlyPineapple/eu-funds-go-quiz-API` `main.py`].
- Licencja: nie ustalona (strony zablokowane). Dane publiczne; DO WERYFIKACJI na stronie lub na dane.gov.pl.

### 3.2 Mapa Dotacji UE (mapadotacji.gov.pl)

[✔ otwarta strona projektu `https://mapadotacji.gov.pl/projekty/1674627/?lang=en`]: pola widoczne: Name of the beneficiary, Project value, Co-financing from the EU, Voivodeship, County, Program, Action, Fund, Perspective. Brak ID projektu/numeru umowy, brak dat projektu, brak informacji o eksporcie/API, brak licencji. Wniosek: do scrapingu nie nadaje się, lista XLSX jest lepsza. Eksport/API: niepotwierdzone.

### 3.3 Kohesio

Status: tylko dokumentacja.
- Dane do pobrania w CSV/XLSX i RDF ze strony `https://kohesio.ec.europa.eu/data/`; ponad 1,7 mln projektów i ok. 500 tys. beneficjentów dla 2014-2020; 2021-2027 dochodzi stopniowo [✔ https://data.europa.eu/en/publications/datastories/linking-data-kohesio-platform].
- SPARQL: `https://query.linkedopendata.eu`; Wikibase (EU Knowledge Graph) `https://linkedopendata.eu/`; eksport: `https://data.linkedopendata.eu` [✔ https://ec-doris.github.io/2023-06-30-ECHO].
- Pola i klucze polskich projektów: DO WERYFIKACJI (nie otwarto schematu). Strony `kohesio.ec.europa.eu/services` i `/en/faq` nie dały się odczytać (zwrócony błąd/pusta treść).
- Licencja: "free for reuse" wg strony data.europa.eu [✔]; konkretna licencja DO WERYFIKACJI.

### 3.4 Cohesion Open Data Platform (cohesiondata.ec.europa.eu, Socrata)

- Zbiór `ibus-er6c` "ESIF 2014-2020 Finance..." (widok społecznościowy): szereg czasowy postępu finansowego dla 530+ programów, wartości kumulatywne ("MUST NOT BE AGGREGATED"), aktualizowany ("updated Sep 9 2026"), CC0 1.0; raportowanie 3 razy w roku dla EFRR/EFS/FS [✔ https://cohesiondata.ec.europa.eu/dataset/Untitled-Visualization-Based-on-ESIF-2014-2020-Fin/ibus-er6c/about]. Kolumn nie wymieniono na stronie (opis w pliku XLSX metadanych).
- Endpoint SODA (wzorzec Socrata, wnioskowany, nie potwierdzony): `https://cohesiondata.ec.europa.eu/resource/ibus-er6c.json` [?]. Strona mówi "SODA2 Only: Yes" [✔].
- Poziom projektu? Ten zbiór jest na poziomie programu/osi, **nie projektu**. Dane projektowe są w Kohesio i w polskiej liście. Wartość: tylko kontekst makro.

### 3.5 KPO

Niepotwierdzone. Nie znalazłem publicznej listy ostatecznych odbiorców/przedsięwzięć w formacie maszynowym. W wynikach pojawiły się strony gov.pl (np. "inwestycje KPO" Ministerstwa Finansów, "lista projektów indywidualnych"), ale gov.pl blokuje WebFetch (robots), więc ich nie otworzyłem. Zadanie na start: Partner (sekcja 12) powinien wskazać źródło.

### 3.6 CST2021

Publicznie dostępny tylko pośrednio: lista projektów 2021-2027 jest wyciągiem z CST2021 [~ notebook Policy-paper]. Dostępu do samego systemu nie ma, jest dla beneficjentów i instytucji.

---

## 4. Rejestry podmiotów

### 4.1 KRS (api-krs.ms.gov.pl)

Status: **tylko dokumentacja/wtórne**. Dokumentacja: `https://prs.ms.gov.pl/krs/openApi` (WebFetch: spoza listy dozwolonych; adres podany w komentarzu `HelpCode-ai/anythingmcp` `packages/backend/src/adapters/pl/krs.live.spec.ts` [~]).
- Bez klucza [~ jw.; opis aktora Apify https://apify.com/bovi/poland-company-registry.md: "fully open API"].
- Endpointy: `GET https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}?rejestr=P|S&format=json`, `.../OdpisPelny/{krs}?...`, `GET https://api-krs.ms.gov.pl/api/Krs/Biuletyn/{data}` (lista numerów KRS ze zmianami danego dnia; test w repozytorium oczekuje tablicy napisów dla `/Biuletyn/2026-11-06`) [~ `krs.live.spec.ts`; `opensanctions/opensanctions` `datasets/pl/krs/crawler.py` ma stałe `EXTRACT_URL` i `BULLETIN_URL`].
- Przykład: `https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000019193?rejestr=P&format=json` (numer z testu w repozytorium: spodziewany NIP `5250000251`) [~]. **Nie wykonany.**
- `rejestr`: `P` (przedsiębiorcy), `S` (stowarzyszenia i inne); numer w jednym z nich [~ crawler OpenSanctions]. Numer dopełniony zerami do 10 cyfr [~ Lex-Machina]. 404 gdy brak [~].
- Struktura: `odpis.naglowekA.numerKRS`, `odpis.dane.dzial1.danePodmiotu` (w tym `identyfikatory.nip`, `identyfikatory.regon`), przy podmiocie zagranicznym `danePodmiotuZagranicznego` [~ `krs.live.spec.ts`, `opensanctions` crawler.py]. Reszta (dział 2 organy, dział 3 przedmiot działalności i wiadomości o sprawozdaniach, dział 4-6) DO WERYFIKACJI na próbce.
- **Brak wyszukiwania po NIP i po nazwie**: tylko po numerze KRS [~ opis aktora Apify]. Mapowanie NIP→KRS: przez Białą listę (zwraca `krs`) albo REGON BIR.
- Limity: oficjalnych nie znalazłem. Crawler OpenSanctions cyklicznie przechodzi cały rejestr, więc nie jest to bardzo restrykcyjne [~]. Zakładaj grzeczne 2-5 zapytań/s i ponawianie.
- Sprawozdania finansowe w tym API: tylko odnośniki (brak PDF/XBRL), pełne dokumenty tylko przez portal eKRS [~ https://dev.to/openregistry/poland-krs-post-ekrs-2024-reality-api-guide-46df, opis narzędzia OpenRegistry]. Maszynowa dostępność sprawozdań: niepotwierdzona (rejestr "rdf-przegladarka.ms.gov.pl" pojawia się w pomiarach domen [~ Lex-Machina], nie sprawdzony).
- Licencja: dane jawne; warunki ponownego użycia DO WERYFIKACJI.

### 4.2 Biała lista VAT (wl-api.mf.gov.pl)

Status: **tylko dokumentacja** (spec otwarta). [✔ https://wl-api.mf.gov.pl/ — wersja 1.6.2; https://www.gov.pl/attachment/9441e336-1379-4f94-a330-64b2663515d4 — OpenAPI].
- Wszystkie `GET`, JSON, parametr `date` wymagany (format `YYYY-MM-DD`) poza `/api2/status/nip/{nip}` (opcjonalny).
- `/api/search/nip/{nip}`, `/api/search/nips/{nips}` (do 30 NIP po przecinku), `/api/search/regon/{regon}`, `/api/search/regons/{regons}` (do 30), `/api/search/bank-account/{rachunek}`, `/api/search/bank-accounts/{rachunki}` (do 30), `/api/check/nip/{nip}/bank-account/{rachunek}`, `/api/check/regon/{regon}/bank-account/{rachunek}` [✔].
- Pełny adres w przykładzie z kodu: `https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={YYYY-MM-DD}` [~ `qa10devteam/behive` `src/behive/engine/entity_resolver.py`]. W spec brak bloku `servers`.
- Pola podmiotu (dosłownie): `name`, `nip`, `statusVat` (Czynny/Zwolniony/Niezarejestrowany), `regon`, `pesel`, `krs`, `residenceAddress`, `workingAddress`, `representatives`, `authorizedClerks`, `partners`, `registrationLegalDate`, `registrationDenialDate`, `registrationDenialBasis`, `restorationDate`, `restorationBasis`, `removalDate`, `removalBasis`, `accountNumbers`, `hasVirtualAccounts` [✔]. Odpowiedź: `result.subject` / `result.entries[]` (`identifier`, `subjects`, `error`), `requestId`, `requestDateTime` (format `DD-MM-YYYY HH:mm:ss`) [✔].
- Limity: **w spec nie podano**. Artykuł powołujący się na dokumentację KAS: 100 zapytań `search` dziennie, po max 30 podmiotów, liczone **na adres IP**, blokada do północy [~ https://invoicedataextraction.com/blog/biala-lista-vat-automatyzacja-weryfikacji-rachunkow; autor wprost nie zweryfikował]. Zakładaj maks. 3 000 NIP/dzień/IP. Strona KAS "jak korzystać z wykazu" (https://www.gov.pl/web/kas/jak-korzystac-z-wykazu) jest zablokowana dla WebFetch: DO WERYFIKACJI.
- Licencja: strona mówi jednocześnie "All rights reserved" i linkuje Apache 2.0 [✔] — niejednoznaczne; kontakt WykazPodatnikow@mf.gov.pl.
- Pułapki: stan "na dzień" (nie pełna historia); tylko podmioty zarejestrowane/były zarejestrowane jako podatnicy VAT; podmioty usunięte pokazują daty `removalDate`. Przydatne jako cecha: status VAT, data rejestracji, liczba rachunków, reprezentanci (do sieci powiązań).

### 4.3 CEIDG API (dane.biznes.gov.pl)

Status: wtórne/niepotwierdzone.
- `GET https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nip=...` [~ `nusquama/n8nworkflows.xyz` readme-10125; `Panelica/pnlcs` `CeidgCompanyProvider.php`].
- Uwierzytelnianie: **Bearer JWT**; token z Hurtowni Danych CEIDG po wniosku (Profil Zaufany), portal `https://dane.biznes.gov.pl/pl/portal/034872` [~ `michaleiatrak-star/Lex-Machina` `shared/DOSTEP-MASZYNOWY-API.md`, pomiar 2026-09-29]. Czas oczekiwania: nieznany [?].
- 401 bez tokenu; 200 → `firmy[]` z NIP i REGON w `wlasciciel.{nip,regon}` (nie w `firmy[].nip`); 204 = brak wpisu (np. spółka z KRS); 400 `NIEPOPRAWNY_NUMER_NIP` (zła suma kontrolna) [~ Lex-Machina]. Limit ok. 50 zapytań / 180 s, liczony od ostatniego żądania (ponawianie przedłuża blokadę) [~ Lex-Machina]. JWT zawiera PESEL właściciela: nie wrzucać do repozytorium [~ tamże].
- Pokrywa tylko jednoosobowe działalności; spółki z KRS => 204.

### 4.4 REGON BIR1.1 (GUS)

- SOAP (nie REST). Dokumentacja: `https://api.stat.gov.pl/Home/RegonApi` [~ opis aktora Apify https://apify.com/bovi/poland-company-registry.md; WebFetch spoza listy].
- Klucz: **wydawany e-mailem** przez GUS (`regon_bir@stat.gov.pl`; podać nazwę podmiotu, swój REGON, osobę kontaktową, adresy IP); brak samoobsługi i SLA, "kilka dni roboczych" [~ jw.; potwierdza `Lex-Machina` `DOSTEP-MASZYNOWY-API.md`]. Środowisko testowe: zamrożona, zanonimizowana migawka z 2014 [~ Apify].
- Wyszukiwanie po NIP, REGON lub KRS; bez wyszukiwania po nazwie [~ Apify]. Ma PKD (pełne) [~ https://medium.com/transparent-data-eng/polish-companies-api-meet-business-registers-of-poland-a75c2f223b34].
- Na hackathonie: tylko jeśli klucz dojdzie; zastępnik: KRS + Biała lista.

### 4.5 CRBR

Niepotwierdzone / raczej nieużyteczne. W wynikach: wyrok TSUE ograniczył publiczny dostęp do rejestrów beneficjentów rzeczywistych, a rząd planuje/wprowadza ograniczenia dostępu do CRBR (tytuły artykułów prawo.pl, rp.pl, akademialtca.pl, KPMG PL z 2025-10) [~ tytuły w wynikach WebSearch; treści nie otwierałem]. Artykuł Transparent Data: rejestracja obowiązkowa tylko do 2020-07-13, więc dane niekompletne [✔ https://medium.com/transparent-data-eng/polish-companies-api-meet-business-registers-of-poland-a75c2f223b34]. Nie planować.

### 4.6 Krajowy Rejestr Zadłużonych (KRZ)

Brak oficjalnego API ("nigdy nie wydano publicznego API") [~ https://dev.to/ucptools/how-to-check-polish-company-insolvency-programmatically-krz-scraper-1m9h, autor scrapera]. Wyszukiwarka publiczna `krz.ms.gov.pl` zwraca 403 (WAF) z adresów centrów danych [~ Lex-Machina `DOSTEP-MASZYNOWY-API.md`]. Dostęp "przez przeglądarkę z tokenem JWT z nieudokumentowanych endpointów" nie jest czymś, co proponuję na hackathon (obejście zabezpieczeń/niestabilność). Niepotwierdzone, pomijamy; alternatywa: statusy upadłości z KRS (w odpisie) i pole `removalDate` z Białej listy.

### 4.7 e-KRS sprawozdania finansowe

Maszynowa dostępność niepotwierdzona (patrz 4.1). Wiadomo, że sprawozdania są w XML od 2018/2019 [~ Medium Transparent Data, stary artykuł], ale API KRS daje tylko referencje. Pomijamy na hackathon.

---

## 5. Kontekst i etykiety pomocnicze

### 5.1 KIO

Orzeczenia KIO: baza UZP `orzeczenia.uzp.gov.pl`; wyszukiwarka UZP używana przez narzędzia (`kio_szukaj`) od 2026-10-02 [~ Lex-Machina `DOSTEP-MASZYNOWY-API.md`]. W SAOS tylko 855 orzeczeń z 2018 (ostatnie 2018-09-06), 0 od 2019 [~ tamże]. SAOS API docs: `https://www.saos.org.pl/help/index.php/dokumentacja-api/api-przeszukiwania-danych` [✔ tylko adres z wyników, nie otwarty]. Eksport hurtowy KIO: niepotwierdzony. Wartość: liczba odwołań na postępowanie jako cecha ryzyka. Niski priorytet.

### 5.2 NIK

Niepotwierdzone: wyniki kontroli to głównie PDF-y na nik.gov.pl; maszynowego API/eksportu nie znalazłem. Pomijamy.

### 5.3 GUS BDL API

Status: **tylko dokumentacja** [✔ https://api.stat.gov.pl/Content/files/bdl/Methods_Description_API_BDL_v1.pdf].
- Base: `https://bdl.stat.gov.pl/api/v1/`. Anonimowo (niższe limity) lub z kluczem w nagłówku `X-ClientId` (klucz na e-mail po rejestracji).
- Endpointy: `Subjects`, `Subjects/search?name=`, `Variables`, `Variables/search?name=`, `Variables/{id}`, `Data/ByVariable/{var-Id}` (parametry `year`, `unitLevel`, `unitParentId`, `page`, `pageSize`, `format=json|jsonapi|xml`, `lang=pl|en`).
- Limity (zapytań): anonimowo 5/s, 100 / 15 min, 1 000 / 12 h, 10 000 / 7 dni; z kluczem 10/s, 500 / 15 min, 5 000 / 12 h, 50 000 / 7 dni. Maks. `pageSize` nie podano [✔].
- **Identyfikatory zmiennych dla wskaźników cen produkcji budowlano-montażowej: nie ustaliłem.** DO WERYFIKACJI: `GET .../Subjects/search?name=budowlano` potem `Variables?subjectId=...`. Opis metodologiczny wskaźnika jest na stat.gov.pl ("Wskaźnik cen produkcji budowlano-montażowej") [✔ tytuł w wynikach]; czy wskaźnik jest w BDL, czy tylko w komunikatach/Skarbnicy Danych (SDP): niepotwierdzone.
- Użycie: deflacja wartości umów (przekroczenie kosztów a inflacja budowlana), cecha okresu.

### 5.4 dane.gov.pl API

Status: wtórne.
- Base: `https://api.dane.gov.pl/1.4/` [~ `yasiupl/nadajniki` `scripts/fetch-data.mjs`; `Havystar/financzeska`; `Badym/DevEstate`].
- Wyszukiwanie: `GET https://api.dane.gov.pl/1.4/search?page=1&per_page=100&model[terms]=dataset&lang=pl` z opcjami `sort=-date`, `format[terms]=csv`, `categories[id][terms]=145`, `q=...` [~ `Havystar/financzeska` `document-finder/crawler.py`; `planetoida90210/cali-park`]. Zasoby zbioru: `GET /1.4/datasets/{id}/resources`; zbiór: `/1.4/datasets/{id}` [~ `yasiupl/nadajniki`; `gryczanm/schron-app`].
- Dokument standardu API (Standardy otwartości): `page`, `limit`, `filter[...]`, `fields`, `sort`, `links.first/prev/self/next/last` [✔ https://dane.gov.pl/media/ckeditor/2020/05/29/standard-api.pdf — ogólny standard; nie wiem, na ile identyczny z 1.4]. Nazwy `per_page` (kod klientów) a `limit` (standard) różnią się: DO WERYFIKACJI.
- Klucz: klienci wywołują bez klucza [~]. Przeglądarka-narzędzia sandboxowe potrafiły zwracać "poza listą" (to ograniczenie ich sandboxu, nie API).
- Zbiory (rejestr umów, plany postępowań, korekty/nieprawidłowości): **nie wyszukałem** konkretnych identyfikatorów. Zadanie na dziś wieczór: `.../1.4/search?q=rejestr%20umów`, `q=plany%20postępowań`, `q=korekty%20finansowe`.
- Licencje zbiorów są per zbiór (zwykle CC0/CC BY): sprawdzać w metadanych.

### 5.5 GUNB RWDZ

Status: niepotwierdzone w zakresie maszynowym. Wyszukiwarka publiczna `wyszukiwarka.gunb.gov.pl` (wnioski o pozwolenie na budowę, decyzje, zgłoszenia) działa od 2016-01-01, dostęp powszechny i bezpłatny [✔ https://inzynierbudownictwa.pl/?p=9536]. Hurtowych CSV na dane.gov.pl nie znalazłem (nie sprawdzano przez API dane.gov.pl). Pola i rozmiar: DO WERYFIKACJI. Łączenie z inwestycją publiczną: tylko po lokalizacji/inwestorze (słabe).

### 5.6 GDDKiA, PKP PLK

Niepotwierdzone. Stronę gov.pl "Postęp realizacji inwestycji drogowych" GDDKiA (`https://www.gov.pl/web/gddkia/postep-realizacji-inwestycji-drogowych`) widziałem tylko jako wynik wyszukiwania; maszynowej publikacji terminów kontraktów nie potwierdziłem. PKP PLK: nic. Alternatywa: ogłoszenia BZP/TED (GDDKiA jest zamawiającym, dane już u nas).

### 5.7 Rejestry umów miast

- Lublin: Rejestr umów 2014 – 2024-12-31, CSV (UTF-8?), kolumny `NUMER_UMOWY`, `DATA_ZAWARCIA`, `KONTRAHENT`, `KWOTA`, `PRZEDMIOT`; CC BY; ostatnia aktualizacja 2025-01-15; bezpośredni link: `https://otwartedane.lublin.eu/dataset/2184ac15-a0cd-427d-8e6b-783293a86635/resource/c18031b8-87cf-442e-8f5c-3f644af9e3bc/download/rejestr-umow.csv` [✔ https://otwartedane.lublin.eu/en/dataset/rejestr-umow/resource/c18031b8-87cf-442e-8f5c-3f644af9e3bc]. Bez dat wykonania i bez aneksów: tylko umowy.
- Warszawa: portale `https://dane.um.warszawa.pl/` (nowy) i `https://api.um.warszawa.pl/` (stary, ma zostać zastąpiony) [✔ https://warszawa19115.pl/-/dane-po-warszawsku]; rejestru umów nie potwierdziłem.
- Gdańsk: CKAN `ckan.multimediagdansk.pl` (`/api/3/action/package_search?q=...`) [~ `gryczanm/schron-app` `docs/research/dane-o-schronach.md`]; rejestru umów nie potwierdziłem.
- Jakość: nieujednolicone formaty, brak identyfikatora postępowania, więc łączenie z BZP po nazwie kontrahenta i kwocie (słabe).

### 5.8 OpenTender / GTI / OCP

- OCDS Data Registry (OCP): "Poland: OpenTender", dane styczeń 2006 – sierpień 2022, źródła TED i krajowe portale, ostatnio pobrane styczeń 2026 [✔ https://data.open-contracting.org/en/search/?region=EU]. Numer publikacji/URL pobrania: DO WERYFIKACJI (strona `.../publication/NN` dla Polski nie została znaleziona).
- Mendeley Data "Public Procurement, Companies, and Contracting Networks" (GTI): zbiór 01 obejmuje Bułgarię, Niemcy, Włochy i **Polskę**; wiersz = zwycięska oferta na część w postępowaniu; identyfikatory postępowania/części/oferty, kupujący i dostawca (id, nazwa), typ procedury, daty publikacji i decyzji, ceny ofert, CPV, NUTS, **wskaźniki integralności (czerwone flagi) na poziomie postępowania**; licencja CC BY-NC-SA 4.0; wersja 2 z 2026-10-16; DOI 10.17632/nfhtfwn5nk.2; jeden plik na kraj [✔ https://data.mendeley.com/datasets/nfhtfwn5nk]. Lata dla Polski: nie podano.
- GTI GPPD (v3, 2024-03-08): 42 kraje, 2006-2021, wskaźniki ryzyka korupcji; licencja "CC BY NC 3.0"; Polska nie jest wymieniona w opisie, lista plików pusta [✔ https://data.mendeley.com/datasets/w9mzf4vswh/3].
- Zenodo "European Union: OpenTender" (2024-10-29): 35 jurysdykcji, CC BY-NC-SA 4.0, 13 plików CSV (`main.csv`, `awards.csv`, `parties.csv`, ...), ale to mała próbka (ok. 2 MB w sumie), Polska niewymieniona [✔ https://zenodo.org/record/14006724].
- Raport ECA 28/2023: 32 pliki CSV (zip) z wskaźnikami, w tym ze źródeł Opentender (CC BY-NC-SA) i TED CSV (CC BY 4.0), lata 2011-2020 [✔ https://www.eca.europa.eu/OpenData/SR-2023-28/README.pdf].
- Uwaga licencyjna: CC BY-NC-SA wymaga użycia niekomercyjnego i dalszego udostępniania na tych samych warunkach: dla prototypu hackathonowego dopuszczalne, ale zaznaczyć w README.
- Pułapka: dane Polski w OpenTender kończą się w sierpniu 2022, więc nie pokrywają okresu nowej BZP w pełni (BZP od 2021).

### 5.9 Gotowy zbiór: Atlas Przetargów (BZP + TED)

Status: wtórne (czytałem fragmenty plików w repo przez wyszukiwarkę GitHub).
- Repo: `https://github.com/atlasprzetargow/polish-tenders-dataset`; DOI Zenodo 10.5281/zenodo.19634050 (znaczek w README); Kaggle `michalpozoga/polish-public-tenders`; wersja `2026.Q2`, wydana 2026-04-17 [~ `CITATION.cff`, README].
- Licencja danych: CC BY 4.0; kod MIT [~ `LICENSE-DATA`, `LICENSE-CODE`].
- Zakres: od 2024 do dziś, ok. 1,4 mln ogłoszeń (BZP + TED), aktualizacja kwartalna (pełny zrzut) [~ README]. Format: CSV + Parquet po latach, np. `data/tenders_2025.parquet`; surowy adres użyty w notebooku: `https://github.com/atlasprzetargow/polish-tenders-dataset/raw/main/data/tenders_2025.parquet` [~ `notebooks/01_getting_started.ipynb`]. Dodatkowo `buyers.csv`, `contractors.csv`.
- Kolumny: `id`, `source`, `notice_type`, `tender_type`, `order_type`, `title`, `buyer`, `buyer_nip`, `nip_normalized`, `city`, `province` (kody PLxx), `latitude`, `longitude`, `cpv_code`, `date`, `publication_date_full`, `submitting_offers_date`, `procedure_result`, `estimated_value`, `currency`, ..., `contractor_name`, `contractor_city`, `contractor_province`, `contractor_country`, `contractor_national_id`, `contractor_count`, `is_consortium`, `is_duplicate` [~ `export.py` `TENDER_COLUMNS` (lista ucięta), `schema/tenders.md`, README]. Pełna lista kolumn (czy jest `tender_id`): DO WERYFIKACJI.
- Ograniczenia: bez `html_body` (czyli bez sekcji 5.x ogłoszeń o wykonaniu), zwycięzca tylko w `TenderResultNotice`, przy konsorcjum tylko pierwszy wykonawca, osoby fizyczne zanonimizowane (hash `anon-...`), brak weryfikacji przeze mnie. Notebook pokazuje wiersz `ContractPerformingNotice` z `estimated_value` 278100 PLN (nie wiem, czy to wartość z sekcji wykonania; DO WERYFIKACJI).
- Wniosek: świetny zapasowy zbiór bazowy (kupujący, wykonawca, CPV, wartość) na pierwsze godziny. Etykiet opóźnień z niego nie zrobimy bez `htmlBody`.

### 5.10 Inne zbiory w tej rodzinie

- Mendeley `xk8db3p74p`: kryteria oceny ofert w polskich postępowaniach (113 373 postępowań, 25 535 unikalnych kryteriów), CC0, dane do klastrowania kryteriów, nie etykiety [✔ https://data.mendeley.com/datasets/xk8db3p74p].

---

## 6. Gotowe zbiory z etykietami opóźnień/przekroczeń (świat), krótko

Wszystko poniżej niepotwierdzone (nie otworzyłem stron danych):
- Flyvbjerg i in. (Oxford Global Projects Database, ok. 16 tys. projektów transportowych): publikacje w wynikach (np. https://core.ac.uk/download/357382624.pdf, arXiv 1303.6571); czy baza jest publicznie do pobrania: niepotwierdzone (próba otwarcia artykułu Cambridge o "Flyvbjerg database" nie powiodła się). W artykule o błędach prognoz użyto bazy, której dostępność należy sprawdzić w sekcji "Data availability".
- Bank Światowy IEG: nie sprawdzałem.
- Kaggle/Zenodo/HuggingFace: wyniki wyszukiwania pokazały m.in. figshare `DATABASE.xlsx` (https://figshare.com/articles/dataset/DATABASE/22043663, zawartość nieznana) i komercyjny "infrastructure delays tracker" (newscatcherapi.com, oparty na wiadomościach, nie otworzony). Nic nie nadaje się bez weryfikacji.
- CoST/OC4IDS: standard `https://standard.open-contracting.org/infrastructure/latest/en/projects/`; publikujących krajów nie sprawdzałem, dowodu na Polskę nie znalazłem.
- Wniosek: nie opieramy się na zagranicznych etykietach; etykiety budujemy z ogłoszeń o wykonaniu/zmianie umowy (sekcja 1.8).

---

## 7. Podsumowanie dostępu

| Źródło | Klucz | Gotowe bez klucza | Status |
|---|---|---|---|
| BZP `/mo-board/api/v1/notice` | nie | tak | tylko dokumentacja wtórna |
| TED search v3 | nie | tak | tylko dokumentacja |
| KRS Open API | nie | tak | tylko dokumentacja wtórna |
| Biała lista VAT | nie | tak (limit/IP) | tylko dokumentacja |
| Atlas Przetargów (GitHub) | nie | tak | wtórne |
| Lista projektów FE XLSX | nie | tak | wtórne |
| Kohesio (CSV/SPARQL) | nie | tak | tylko dokumentacja |
| Cohesion Open Data (Socrata) | nie | tak | tylko dokumentacja |
| GUS BDL | opcjonalnie (`X-ClientId`) | tak (niższe limity) | tylko dokumentacja |
| dane.gov.pl API | nie | tak | wtórne |
| CEIDG v3 | tak (JWT, Profil Zaufany) | nie | wtórne |
| REGON BIR | tak (e-mail do GUS) | nie | wtórne |
| KRZ, CRBR | brak/ograniczone | nie | niepotwierdzone |
| KPO, GUNB bulk, GDDKiA, PLK, NIK | n/d | n/d | niepotwierdzone |

---

## 8. (a) Ranking: 5 źródeł, od których zacząć w sobotę

1. **BZP `/mo-board/api/v1/notice`**: jedyne źródło etykiet (ContractPerformingNotice 5.3/5.5/5.4.x, AgreementUpdateNotice) plus cech (ContractNotice, TenderResultNotice). Bez klucza. Ściągnąć okna dzienne dla 4 typów, w trybie ciągłym w tle (limit 30/min). Zrobić to jak najwcześniej (przed sobotą, jeśli reguły hackathonu pozwalają na prace przygotowawcze na danych publicznych).
2. **Atlas Przetargów (Parquet z GitHuba)**: gotowe tabele kupujący/wykonawca/CPV/wartość od 2024 w kilka minut; zabezpieczenie na wypadek limitów BZP. CC BY 4.0.
3. **Lista projektów FE 2021-2027 + 2014-2020 (XLSX)**: wymiar "projekty unijne" zadania; daty, wartości, dofinansowanie, beneficjent. Pobrać oba pliki z jednej strony; łączenie po nazwie (brak NIP).
4. **TED search v3**: duże zamówienia, `can-modif` z uzasadnieniem zmiany; anonimowo; iteracja tokenem. Mniejsze pokrycie (powyżej progów), ale bogatsze pola.
5. **KRS Open API + Biała lista VAT**: wzbogacenie wykonawców i zamawiających (wiek firmy, status, rachunki, reprezentanci); bez klucza. NIP→KRS przez Białą listę (zwraca `krs`).
Rezerwa: GTI/OpenTender (czerwone flagi, ale Polska do 2022) jako wzór wskaźników.

## 8. (b) Konta i klucze do założenia PRZED 21.11 (czasy oczekiwania: moje szacunki [?])

| Co | Po co | Jak | Czas |
|---|---|---|---|
| Token CEIDG v3 | wykonawcy-osoby fizyczne | wniosek w Hurtowni Danych CEIDG z Profilem Zaufanym (`https://dane.biznes.gov.pl/pl/portal/034872`) | nieznany; zacząć dziś |
| Klucz REGON BIR | PKD, REGON | e-mail na `regon_bir@stat.gov.pl` z nazwą, REGON-em, osobą kontaktową, IP | "kilka dni roboczych"; może nie zdążyć |
| `X-ClientId` GUS BDL | wyższe limity | rejestracja e-mail (formularz ze strony API BDL) | zwykle szybko [?] |
| Nic nie trzeba | BZP, TED search, KRS, Biała lista, Atlas, lista FE, Kohesio, Cohesion Open Data, dane.gov.pl | brak | 0 |
Dla TED API key (EU Login) wyszukiwanie go nie wymaga. Do wszystkiego poza CEIDG/BIR da się zacząć od razu.

## 8. (c) Klucze łączenia i gdzie zawodzą

| Klucz | Łączy | Gdzie zawodzi |
|---|---|---|
| `tenderId` ("Identyfikator postępowania") | ContractNotice ↔ TenderResultNotice ↔ ContractPerformingNotice ↔ AgreementUpdateNotice (BZP) | `null` dla `SmallContractNotice`; wiele części/umów na jedno postępowanie; ogłoszenia o zmianie treści (`NoticeUpdateNotice`) duplikują |
| `bzpNumber`/`noticeNumber` | pojedyncze ogłoszenie; linki do poprzedniego ogłoszenia | numer ogłoszenia ≠ numer postępowania; format DO WERYFIKACJI |
| `objectId` | unikalny rekord w API | nie wspólny z TED |
| NIP zamawiającego (`organizationNationalId`) | BZP ↔ KRS (przez Białą listę) ↔ Atlas `buyer_nip` | nie zawsze NIP (REGON?); jednostki organizacyjne gminy z NIP gminy; błędne wpisy |
| NIP/REGON wykonawcy (`contractorNationalId`) | BZP ↔ Biała lista/KRS/CEIDG | konsorcja (wielu wykonawców, Atlas bierze pierwszego); wykonawcy zagraniczni; osoby fizyczne z PESEL (11 cyfr) |
| KRS | KRS API (jedyny klucz tego API) | brak wyszukiwania po NIP; NIP→KRS przez WL `krs` lub BIR |
| REGON | BIR, WL | 9 vs 14 cyfr (jednostka lokalna) |
| `publication-number` (TED) | TED ↔ TED | TED ↔ BZP: brak potwierdzonego wspólnego klucza; duplikaty (Atlas `is_duplicate`) |
| Numer projektu FE ('Numer umowy') | tylko wewnątrz list FE | brak NIP beneficjenta i brak numeru postępowania BZP; łączenie z BZP przez: nazwa beneficjenta ≈ nazwa zamawiającego, lokalizacja (WOJ/POW/GM), tytuł, daty, kwota; 'Nazwa wykonawcy kontraktu' ≈ nazwa wykonawcy |
| CPV | filtrowanie robót budowlanych (45xxxxxx) | `cpvCode` BZP to tekst z opisem; główny vs dodatkowe CPV |
| Nazwa + miasto + kwota | rejestry umów miast ↔ BZP | brak ID postępowania; formaty |

## 9. Pierwsze kroki weryfikacyjne w sobotę (komendy do uruchomienia z maszyny z internetem)

```
# BZP: struktura odpowiedzi i kursor
curl -sS "https://ezamowienia.gov.pl/mo-board/api/v1/notice?NoticeType=ContractPerformingNotice&PublicationDateFrom=2026-11-10T00:00:00&PublicationDateTo=2026-11-11T00:00:00&PageSize=2" -o samples/bzp_cpn.json
# TED
curl -sS -X POST https://api.ted.europa.eu/v3/notices/search -H "Content-Type: application/json" -d '{"query":"buyer-country=POL","fields":["publication-number","notice-type"],"limit":2}' -o samples/ted.json
# KRS
curl -sS "https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000019193?rejestr=P&format=json" -o samples/krs.json
# Biała lista
curl -sS "https://wl-api.mf.gov.pl/api/search/nip/5250000251?date=$(date +%F)" -o samples/wl.json
```
Do zapisania w repo: nagłówki odpowiedzi (limity: `X-RateLimit-*`, `Retry-After`).

## 10. (d) 8 pytań o dane do Partnera (MFiPR) na starcie

1. Jednostką analizy jest projekt FE, kontrakt wykonawczy czy postępowanie (jak je łączyć, gdy jeden projekt FE ma wiele przetargów)?
2. Jak definiujecie "opóźnienie" i "przekroczenie kosztów" (próg w dniach/procentach, względem czego: pierwotna umowa, wniosek o dofinansowanie, harmonogram w umowie o dofinansowanie)?
3. Czy dostaniemy dane niepubliczne lub zanonimizowany wyciąg z CST2021/SL2014 (harmonogramy, wnioski o płatność, aneksy), choćby próbkę do kalibracji etykiet?
4. Czy za etykiety wolno uznać samodeklaracje z ogłoszeń o wykonaniu umowy (pole 5.3, wartości z 4.4/5.5) i zmiany umowy z BZP, czy macie lepszy standard?
5. W którym momencie cyklu życia ryzyko ma być oceniane (przed ogłoszeniem przetargu, po wyborze wykonawcy, w trakcie realizacji) i jaki horyzont prognozy?
6. Jaki zakres: tylko roboty budowlane (CPV 45) i infrastruktura, czy także dostawy/usługi IT; jakie lata; czy tylko beneficjenci publiczni?
7. Gdzie jest lista KPO (ostateczni odbiorcy, przedsięwzięcia) w formie maszynowej i czy można ją łączyć z BZP po NIP?
8. Ograniczenia: RODO dla osób fizycznych (wykonawcy z PESEL w BZP), użycie danych o licencji CC BY-NC-SA (OpenTender/GTI) w prototypie, publikacja wyników i flag na nazwane podmioty (jak formułować "czerwone flagi" bez zarzutu naruszenia prawa)?
