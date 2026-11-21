# 03. Jakie dane są naprawdę dostępne

Stan na 2026-11-16. Oznaczenia: [✔] sprawdzone przeze mnie na żywym źródle lub w źródle pierwotnym; [~] dokumentacja wtórna lub cudzy kod; [?] niepotwierdzone. Szczegóły techniczne drugiego rzędu: `zalaczniki/notatki_dane_api.md`.

## Odpowiedź w skrócie

Najważniejsze źródło to publiczne API Biuletynu Zamówień Publicznych. Bez klucza i bez rejestracji zwraca „ogłoszenia o wykonaniu umowy", a każde z nich mówi wprost, czy umowę wykonano w terminie, ile było zmian, z jakich przyczyn i ile ostatecznie zapłacono [✔]. Na 2 318 umowach na roboty budowlane z 2–13.11.2026 policzyłem: 25,4% po terminie, 39% ze zmianą umowy, 26,4% z wypłatą wyższą niż wartość umowy [✔]. To zmienia założenie pakietu: etykiety opóźnień istnieją w otwartych danych. Reszta źródeł (TED, lista projektów FE, rejestry firm) jest udokumentowana, ale z tej sesji nie dało się ich przetestować.

## Tabela źródeł

| Źródło | Dostęp | Format | Licencja | Aktualność | Pułapki jakości | Test |
|---|---|---|---|---|---|---|
| **BZP: ogłoszenia o wykonaniu umowy** (`NoticeType=ContractPerformingNotice`) | `GET https://ezamowienia.gov.pl/mo-board/api/v1/notice`; bez klucza; 30 zapytań/min/IP, potem HTTP 403 [✔ strona integracji UZP] | JSON, treść w polu `htmlBody` (HTML, ok. 11 KB na ogłoszenie) | ISP, brak jawnej licencji CC [✔ brak na stronie] | Publikacja do 30 dni po wykonaniu umowy (art. 448 Pzp [✔]); ok. 200–260 ogłoszeń o robotach na dzień roboczy [✔] | Etykieta „w terminie" to deklaracja zamawiającego: wśród 2 226 umów z kompletem dat 326 oznaczono jako terminowe, choć data wykonania była ponad 7 dni po dacie wynikającej z planowanego okresu [✔]. Przekrój z krótkiego okna zaniża udział długich kontraktów. 22% dopasowanych ogłoszeń o wyniku (205 z 936) obejmuje wiele części i wymaga osobnego parsowania | ✅ 2 318 rekordów pobranych i sparsowanych, próbka w `data-samples/bzp/` |
| **BZP: ogłoszenia o wyniku** (`TenderResultNotice`) | to samo API | to samo | to samo | ok. 200 dziennie dla robót [✔] | Wartość szacunkowa (pole 4.3, netto) wypełniona w 39% dołączonych rekordów [✔]; ceny ofert brutto | ✅ 16 362 rekordy przejrzane, 936 dopasowanych do umów |
| **BZP: ogłoszenia o zmianie umowy** (`AgreementUpdateNotice`) | to samo API | to samo | to samo | 26 dla robót jednego dnia (12.11.2026) [✔] | Publikowane tylko dla części zmian (art. 455 Pzp); przyczyny tekstem, mediana ok. 100 znaków | ✅ 1 rekord w próbce, parser przetestowany |
| **BZP: ogłoszenia o zamówieniu** (`ContractNotice`) | to samo API | to samo | to samo | 90 dla robót jednego dnia [✔] | Pola: kryteria i wagi, wadium, zaliczki, termin składania ofert (`submittingOffersDate` w JSON) | ⚠️ nagłówki sekcji obejrzane, parser nienapisany |
| TED (zamówienia powyżej progów UE) | `POST https://api.ted.europa.eu/v3/notices/search`, anonimowo; 250 ogłoszeń na stronę, tryb iteracji [~ dokumentacja TED] | JSON (eForms) | ponowne użycie dozwolone, tekst licencji DO WERYFIKACJI | bieżąca | Nazwy pól trzeba brać ze Swaggera; ogłoszenia o modyfikacji umowy mają typ `can-modif` [~] | ❌ |
| Lista projektów FE 2021–2027 (MFiPR) | plik XLSX ze strony funduszeeuropejskie.gov.pl, bez logowania [~] | XLSX | DO WERYFIKACJI | co 1–2 miesiące; ostatni znany stan 30.09.2026 [~] | Brak NIP beneficjenta; łączenie po numerze umowy lub nazwie [~]. W BZP tylko 16,5% zamówień unijnych ma w nazwie projektu numer w formacie FE [✔] | ❌ |
| Kohesio (KE) | CSV/XLSX i SPARQL, bez klucza [~] | CSV, RDF | „free for reuse" [~] | 2014–2020 pełne, 2021–2027 dochodzi | Schemat pól nieobejrzany | ❌ |
| KRS | `https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}?rejestr=P&format=json`, bez klucza, tylko po numerze KRS [~] | JSON | dane jawne | bieżąca | Brak wyszukiwania po NIP | ❌ |
| Biała lista VAT | `https://wl-api.mf.gov.pl/api/search/nip/{nip}?date=RRRR-MM-DD`, bez klucza; do 30 NIP w zapytaniu [~ specyfikacja] | JSON | — | bieżąca | Limity dzienne: źródła się różnią, DO WERYFIKACJI | ❌ |
| CEIDG, REGON BIR | wymagają klucza (wniosek; REGON „kilka dni roboczych") [~] | JSON / SOAP | — | — | Zamówić przed 21.11, jeśli chcemy danych o firmach | ❌ |
| Centralny rejestr umów JSFP | publiczna strona; obejmuje umowy od 1.07.2026 [~] | DO WERYFIKACJI | — | od 07.2026 | Brak historii, dostęp maszynowy niepotwierdzony | ❌ |
| GUS BDL, dane.gov.pl, GUNB RWDZ, orzeczenia KIO, raporty NIK | patrz załącznik | — | — | — | Niepotwierdzone w tej sesji | ❌ |

## Mechanika API BZP (wszystko [✔], sprawdzone doświadczalnie 2026-11-16)

- Wymagane parametry: `NoticeType`, `PublicationDateFrom`, `PublicationDateTo`. Bez nich HTTP 400 z opisem błędu po polsku.
- `PageSize` maksymalnie 500 (powyżej: HTTP 400). Stronicowanie: `SearchAfter=<objectId ostatniego rekordu>`. Parametry `PageNumber`, `Page`, `Skip`, `Offset` są ignorowane (zwracają pierwszą stronę).
- Filtry: `OrderType=Works|Delivery|Services`, `CpvCode=45233120-6`. Daty działają z dokładnością do dnia, dzień „To" wchodzi w zakres. Wyszukiwanie po numerze ogłoszenia lub `tenderId` bez dat nie działa.
- Typy przyjmowane przez API: `ContractNotice`, `TenderResultNotice`, `ContractPerformingNotice`, `AgreementUpdateNotice`, `AgreementIntentionNotice`, `SmallContractNotice`, `CompetitionNotice`, `CompetitionResultNotice`, `NoticeUpdateNotice`, `ConcessionNotice`, `ConcessionAgreementNotice`, `ConcessionUpdateAgreementNotice`, `ConcessionIntentionAgreementNotice`, `NoticeUpdateConcession`, `CircumstancesFulfillmentNotice`.
- Pola JSON: `noticeNumber`, `bzpNumber`, `publicationDate`, `orderObject`, `orderType`, `cpvCode`, `organizationName`, `organizationNationalId` (NIP zamawiającego), `organizationProvince` (np. `PL04`), `tenderId` (OCID), `contractors[]` z `contractorNationalId`, `isTenderAmountBelowEU`, `htmlBody`, `objectId`.
- Pola ogłoszenia o wykonaniu umowy w `htmlBody`: 3.2.1 numer ogłoszenia o zamówieniu; 3.3 czy projekt UE; 3.4 nazwa projektu; 3.5 tryb; 3.9 CPV; 4.1 data umowy; 4.2 okres realizacji; 4.4 wartość umowy; 4.5 numer ogłoszenia o wyniku; 5.1 czy wykonana; 5.2 termin wykonania; 5.3 czy w pierwotnym terminie; 5.4.x zmiany (liczba, podstawa prawna, przyczyny, wartość, wzrost ceny); 5.5 łączna wypłata; 5.6 czy należycie.
- Klucze łączenia: umowa → ogłoszenie o wyniku po numerze z pola 4.5; wszystkie ogłoszenia postępowania po `tenderId`; wykonawca i zamawiający po NIP.

## Co policzyłem na 2 318 umowach (roboty budowlane, ogłoszenia 2–13.11.2026) [✔]

| Przekrój | n | Po terminie | Wypłata > 101% wartości | Zmiana umowy |
|---|---|---|---|---|
| Wszystkie | 2 318 | 25,4% | 26,4% | 39,0% |
| Wartość < 200 tys. zł | 576 | 15,2% | 17,0% | 20,7% |
| 200 tys.–1 mln zł | 1 162 | 20,9% | 22,7% | 33,8% |
| 1–5 mln zł | 453 | 41,4% | 40,0% | 63,6% |
| 5–20 mln zł | 106 | 55,7% | 52,4% | 79,2% |
| Projekt UE: tak / nie | 340 / 1 978 | 34,8% / 23,8% | 39,8% / 24,1% | 55,6% / 36,1% |
| Projekt UE tak / nie w przedziale 200 tys.–1 mln zł | 138 / 1 024 | 29,7% / 19,7% | 31,1% / 21,7% | 47,8% / 31,9% |
| Projekt UE tak / nie w przedziale 1–5 mln zł | 111 / 342 | 40,9% / 41,5% | 56,0% / 34,9% | 68,5% / 62,0% |
| Planowany okres do 60 dni / 241–480 dni / ponad 480 dni | 645 / 199 / 104 | 16,9% / 48,7% / 60,6% | 19,2% / 48,7% / 40,2% | 26,0% / 70,4% / 77,9% |

Wśród 561 umów opóźnionych z kompletem dat mediana opóźnienia to 35 dni (kwartyle 18 i 76 dni), czyli 28% planowanego okresu. Wypłata przekroczyła 110% wartości umowy w 11,3% wykonanych umów. Umów niewykonanych jest 1,0%. Pełna tabela: `data-samples/bzp/reference_table_bzp_works_2026-11.json`.

Różnica między umowami z UE i bez wynika głównie z tego, że umowy unijne są większe: dla terminu znika od 1 mln zł, dla kosztu zostaje. Nie potwierdziłem w dokumentacji UZP, czy pole 5.2 „Termin wykonania umowy" to data faktycznego wykonania; w obejrzanych ogłoszeniach tak wygląda (np. umowa na 3 miesiące z 26.02.2025, pole 5.2 = 8.06.2025, zadeklarowane opóźnienie).

Ograniczenia tych liczb: 82% umów w przekroju zawarto w 2026 r. (krótkie kontrakty kończą się i są ogłaszane szybciej), tylko 54 umowy były powyżej progów unijnych, a okno 12 dni nie pokazuje sezonowości.

## Plan B: dane syntetyczne

`riskminer-ewaluacja/scripts/synth.py` generuje umowy w tym samym schemacie z częstościami z tabeli referencyjnej. Służy do testów interfejsu i jako awaryjne źródło, gdy API nie odpowiada. Każdy ekran z danymi syntetycznymi musi mieć etykietę „dane syntetyczne".

## Ryzyko operacyjne na miejscu

Limit 30 zapytań na minutę liczy się na adres IP. Sieć hali ma zwykle jeden adres wyjściowy dla wszystkich zespołów, więc w sobotę API BZP może być dla nas niedostępne (HTTP 403), jeśli inne zespoły też z niego korzystają. Dane trzeba pobrać przed wyjazdem. Rok ogłoszeń o wykonaniu umów na roboty to ok. 60 tys. rekordów: przy pobieraniu dzień po dniu ok. 400 zapytań, kwadrans przy limicie i ok. 0,7 GB surowych danych (szacunek z 11 KB na ogłoszenie).

## Pytania o dane do Partnera na starcie

1. Czy dostajemy wyciąg z CST2021 (projekty, harmonogramy, wnioski o płatność, zmiany umów o dofinansowanie)? W jakim formacie i z jakimi identyfikatorami?
2. Czy w danych jest etykieta problemu (projekt zagrożony, korekta, aneks terminu, rozwiązanie umowy)? Kto ją nadaje?
3. Czy jest NIP beneficjenta i numer postępowania BZP lub TED, żeby połączyć projekty z zamówieniami?
4. Jaki typ inwestycji i jaki okres obejmują dane? Czy są projekty zakończone?
5. Czy jury policzy metrykę na ukrytym zbiorze? Jaką i na jakim formacie odpowiedzi?
6. Czy wolno łączyć dane Partnera z danymi publicznymi i wysyłać je do zewnętrznego API modelu językowego?
7. Czy są dokumenty (studia wykonalności, harmonogramy, umowy) i w jakiej liczbie?
8. Kto u Partnera byłby użytkownikiem: instytucja zarządzająca, pośrednicząca czy beneficjent?
