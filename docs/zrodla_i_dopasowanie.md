# Źródła danych, metoda dopasowania i model dowodów

## 1. Źródła

| Źródło | Dostęp | Co pobieramy | Status |
|---|---|---|---|
| Lista projektów organizatora (`Risk_Miner_dane_projekty.xlsx`) | plik | 22 projekty: identyfikator RM, NIP beneficjenta, TERYT, tytuł, zakres rekordu (całe postępowanie / część N), numer BZP lub KPO, adnotacja (wartość, dotacja, opis) | działa |
| Materiały eksperckie MFiPR (2 × docx) | plik | katalog ryzyk R01–R15 ze skutkami, tabela zdarzenie → źródło, podstawy art. 455, 6 podsektorów, fazy i dokumenty, porady, 9-punktowa lista kontrolna | działa |
| **BZP – lustro organizatora** `bzp.cytr.us/mo-board/api/v1/notice` | REST, bez klucza | ogłoszenia 4 typów z pełną treścią HTML | działa |
| **BZP – oficjalne API** `ezamowienia.gov.pl/mo-board/api/v1/notice` | REST, 30 zapytań/min | zapas, gdy lustro nie działa; trwałe linki | działa |
| Paczka BZP 2021–2026 (113 tys. ogłoszeń wod-kan) | jednorazowe pobranie | poziom automatyczny (klasa referencyjna), praca offline | działa |
| Biała lista podatników VAT | REST | nazwa, REGON, KRS, status VAT beneficjentów i wykonawców; kontrola krzyżowa z BZP | działa |
| Raporty NIK (wod-kan) | PDF z URL | lekcje: przypadek → przyczyna → sygnał → skutek → zalecenie | działa (1–2 raporty) |
| Dokumenty inwestycji (SWZ, PFU, OPZ, PPU, umowy, aneksy, protokoły) | upload / URL | fragmenty ryzyk ze stroną lub akapitem | działa |
| TED, KRS, KIO, Baza Konkurencyjności, KPOŚK | REST / HTML | ogłoszenia powyżej progów UE, status wykonawców, odwołania, zasada konkurencyjności | zaprojektowane (rejestr konektorów) |

Uwagi o API BZP (sprawdzone 21.11.2026):
- wymagane `NoticeType`, `PublicationDateFrom`, `PublicationDateTo`; stronicowanie `SearchAfter=<objectId>`;
- filtry `TenderId`, `OrganizationNationalId`, `OrganizationId`, `BzpNumber` są **ignorowane**, więc filtrujemy po
  stronie klienta (NIP, OCID);
- lustro odrzuca domyślny User-Agent Pythona (HTTP 403), więc wysyłamy własny;
- lustro działa tylko podczas hackathonu, dlatego jako dowód zapisujemy **trwały link**
  `https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/<objectId>`, a adres lustra trafia do pola
  `retrieved_from`.

Licencje i podstawy prawne źródeł: [LICENSES-THIRD-PARTY.md](../LICENSES-THIRD-PARTY.md) oraz `GET /api/ops/licences`.

## 2. Przetwarzanie ogłoszeń

1. Każda odpowiedź trafia do magazynu surowego (`raw_record`: sha256, URL, data pobrania), a każde zapytanie do
   dziennika `op_log` (URL, parametry, kod HTTP, liczba wyników, czas).
2. Parser DOM rozbija treść na pola `(sekcja, etykieta, wartość, offset, część)` i buduje tekst kanoniczny, do którego
   odnoszą się cytaty. Pola rozpoznajemy po treści etykiety, a nie po numerze sekcji, bo numeracja różni się
   między typami ogłoszeń. Treść dzielimy najpierw na części zamówienia.
3. Normalizacja: kwoty z oznaczeniem podstawy (netto / brutto / nieznana; nie porównujemy kwot o różnej podstawie),
   okresy („6 miesiące” → miesiące kalendarzowe od daty umowy), identyfikatory (BZP, OCID, TED, KPO, NIP, REGON).
   Wykonawcy będący osobami fizycznymi są domyślnie maskowani.

## 3. Dopasowanie projekt → postępowanie → ogłoszenia → umowa → zmiany

**Ścieżka 1 – klucze** (pewność 1,0, status „proponowane”, ekspert może zatwierdzić hurtowo):
1. numer KPO w sekcjach 3.3/3.4 ogłoszeń o wykonaniu i zmianie umowy (oraz 2.14 ogłoszenia o zamówieniu);
2. numer BZP z xlsx → ogłoszenie o zamówieniu → OCID, NIP, REGON (kontrola: NIP, tytuł, województwo);
3. OCID + NIP: wszystkie ogłoszenia tego samego postępowania;
4. odwołania krzyżowe: 4.5 (wykonanie/zmiana → wynik), 2.14 / 3.1.1 / 3.2.1 (poprzednie ogłoszenie), 5.7
   (wcześniejsza zmiana);
5. część zamówienia: dla rekordów „część N” łączymy tylko umowę i ogłoszenia tej części (tytuł „Umowa dla części nr N”,
   NIP wykonawcy, wartość, data).

**Ścieżka 2 – kandydaci z oceną** (gdy brak klucza albo klucze są sprzeczne, np. RM-2026-022 Wolin: numer BZP
z xlsx nie istnieje w BZP). Kandydaci to postępowania tego samego NIP z CPV wod-kan. Ocena jest sumą ważoną
składników, a każdy składnik ma dowód:

| Składnik | Waga domyślna (edytowalna) |
|---|---|
| podobieństwo tytułu (token-set + n-gramy znakowe) | 0,40 |
| nazwy miejscowości / obiektów | 0,15 |
| CPV / podsektor | 0,10 |
| data (np. sufiks KPO /24 → 2024–2026) | 0,10 |
| wartość umowy vs wartość projektu | 0,10 |
| zakres (km, przyłącza, przepompownie) | 0,10 |
| zgodność z xlsx (status, część) | 0,05 |

Wynik ma wyjaśnienie słowne, a odrzucone alternatywy (pułapki) są pokazane z ich ocenami. Status „do weryfikacji”: ekspert
akceptuje, wybiera innego kandydata, wpisuje OCID lub numer ogłoszenia ręcznie albo odrzuca. Decyzje są
zapamiętywane: odrzucony kandydat nie wraca, a ręczne powiązanie przetrwa przebudowę.

**Postępowania pokrewne** (unieważnione i powtórzone o podobnym tytule) są dołączane do projektu i dają zdarzenia
„Unieważnienie” i „Powtórzenie postępowania”.

**Jakość dopasowania** mierzymy na ręcznie zweryfikowanym zbiorze wzorcowym
(`backend/tests/fixtures/gold/links_gold.csv`: oczekiwane powiązania, pułapki, inne części, braki w BZP). Raport z
testu ([raport_z_testu.md](raport_z_testu.md)) podaje powiązania poprawne / niepewne / błędne / brakujące, precyzję i
kompletność.

## 4. Model dowodów

Każdy fakt, powiązanie, zdarzenie i wniosek wskazuje rekordy `evidence`:

| Pole | Znaczenie |
|---|---|
| `source_code`, `kind` | źródło (bzp, xlsx, vat_whitelist, upload …) i rodzaj lokalizatora |
| `url` | trwały link (ezamowienia.gov.pl, strona NIK …) |
| `retrieved_from`, `retrieved_at` | skąd i kiedy faktycznie pobrano (np. lustro) |
| `locator` | sekcja ogłoszenia + numer zmiany + część / strona PDF / akapit DOCX / arkusz!wiersz:kolumna |
| `quote`, `quote_verified` | dosłowny cytat, sprawdzany względem tekstu źródłowego (po normalizacji) |
| `derivation` | dla obliczeń: identyfikatory dowodów wejściowych, wzór i wartości |

Zasady:
- wszystko, co wytworzył system, ma status `proposed`; zatwierdza, poprawia lub odrzuca tylko ekspert, a każda
  zmiana trafia do historii (`review`);
- ponowne przetwarzanie nie nadpisuje danych zatwierdzonych, tylko zapisuje propozycję zmian do porównania;
- identyfikatory to uuid5 z kluczy naturalnych, więc drugi przebieg nie tworzy duplikatów;
- wynik modelu językowego jest oznaczony „Wniosek modelu” wraz z dostawcą i modelem, a bez cytatu z dokumentu
  nie jest przyjmowany.
