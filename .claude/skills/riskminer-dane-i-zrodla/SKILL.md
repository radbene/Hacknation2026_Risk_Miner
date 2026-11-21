---
name: riskminer-dane-i-zrodla
description: Pobiera ogłoszenia z Biuletynu Zamówień Publicznych (API e-Zamówienia) i zamienia je w tabelę umów z wynikami: czy w terminie, zmiany, wypłata, projekt UE, liczba ofert. Użyj, gdy zespół prosi „pobierz dane z BZP", „zbuduj zbiór umów", „dociągnij ogłoszenia o wykonaniu umowy", „połącz umowy z wynikami przetargów", „sparsuj ogłoszenie" albo gdy potrzebna jest tabela wejściowa dla pozostałych skilli riskminer.
---

# riskminer-dane-i-zrodla

## Cel
Jedna tabela `dataset.csv`: wiersz = umowa na roboty budowlane, z etykietami wyniku i cechami znanymi w dniu zawarcia umowy. Fakty o źródłach, limity i statusy testów: `research/03_dane_i_api.md` (jedna wersja prawdy; nie kopiuj stamtąd liczb, odwołuj się).

## Ścieżki
Komendy uruchamiaj z katalogu głównego repozytorium, w którym leży `.claude/skills/`; dane robocze trzymaj w `data/` (utwórz katalog). Pliki `research/...` i `data-samples/...` są w pakiecie `prep/risk_miner/` repozytorium setup: instalując skille w repozytorium rozwiązania, skopiuj oba katalogi obok (np. do `docs/riskminer/`), inaczej odwołania do nich będą puste.

## Kroki
1. **Sprawdź, czy dane już są.** Jeśli istnieje `data/bzp_raw/`, nie pobieraj ponownie: skrypt pomija dni zapisane w cache.
2. **Pobierz** (limit API: 30 zapytań na minutę na adres IP, skrypt czeka 2,1 s między zapytaniami; po HTTP 403 czeka 65 s):
   ```bash
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_fetch.py --type ContractPerformingNotice --order-type Works --from 2025-11-01 --to 2026-11-20 --out data/bzp_raw
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_fetch.py --type TenderResultNotice     --order-type Works --from 2025-01-01 --to 2026-11-20 --out data/bzp_raw
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_fetch.py --type AgreementUpdateNotice  --order-type Works --from 2026-01-01 --to 2026-11-20 --out data/bzp_raw
   ```
3. **Sparsuj** każdy typ do CSV:
   ```bash
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_parse.py data/bzp_raw/ContractPerformingNotice_Works/*.jsonl --out data/contracts.csv
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_parse.py data/bzp_raw/TenderResultNotice_Works/*.jsonl --out data/results.csv
   python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_parse.py data/bzp_raw/AgreementUpdateNotice_Works/*.jsonl --out data/changes.csv
   ```
4. **Połącz** i dodaj cechy: `python3 .claude/skills/riskminer-dane-i-zrodla/scripts/bzp_join.py --contracts data/contracts.csv --results data/results.csv --out data/dataset.csv`
5. **Sprawdź kompletność**: odsetek pustych `label_late`, `value`, `period_days`. W teście na 2 318 rekordach pola krytyczne miały 96–100% (plik 03). Jeśli jest gorzej, obejrzyj 5 rekordów z brakami, zanim pójdziesz dalej.
6. **Bez sieci**: `python3 .claude/skills/riskminer-dane-i-zrodla/scripts/sample_to_full.py --sample data-samples/bzp/contracts_works_sample_500.csv --out data/dataset_sample.csv` daje 500 prawdziwych umów w tym samym schemacie.

## Przykład wejście → wyjście
Wejście: rekord API z `data-samples/bzp/notices_fixture_4.json` (ogłoszenie 2026/BZP 00534981). Wyjście `bzp_parse.py`:
`value=897204.9, paid=949764.56, signed_date=2025-02-26, period_days=90, done=1, on_time=0, n_changes=1, sum_changes=52559.66, price_up=1, label_late=1, label_cost_up=1, change_reasons="Zwiększenie zakresu przedmiotu zamówienia o niezbędne prace remontowe oraz zmiana terminu wykonania umowy"`.

## Kolumny wyniku (najważniejsze)
`bzp, pub_date, province, buyer_nip, contractor_nip, cpv, eu_funded, eu_name, eu_project_no, mode, signed_date, period_days, value, paid, done, done_date, on_time, n_changes, sum_changes, price_up, proper, change_reasons, label_late, label_cost_up, label_failed`; po połączeniu: `n_offers, est_value, price_min, price_max, contractor_size, subcontract, joint, single_bid, won_to_est, spread, log_value, cpv3, signed_month`.

## Kiedy nie używać
- Dane Partnera w innym formacie: użyj skilla wspólnego `hn-dane-od-partnera`, a potem `riskminer-ewaluacja`.
- Zamówienia powyżej progów UE jako główny temat: BZP ma ich mało; potrzebny TED (nieprzetestowany, plik 03).
- Dane o firmach (KRS, Biała lista): w pakiecie nie ma przetestowanych skryptów.

## Pułapki
- **Sieć na hackathonie.** Limit liczy się na adres IP, a hala ma zwykle wspólny adres. Pobierz dane przed wyjazdem.
- Stronicowanie tylko przez `SearchAfter` (objectId ostatniego rekordu). `PageNumber` jest ignorowany i zwraca w kółko pierwszą stronę.
- `est_value` jest netto, ceny ofert i wartość umowy brutto; `won_to_est` przyjmuje VAT 23%.
- Ogłoszenia o wyniku z wieloma częściami są pomijane przy łączeniu (22% dopasowanych w teście).
- Tekst po usunięciu HTML bywa sklejony („zmian: 15.4.2.)"); wyrażenia w parserze to uwzględniają, przy nowych polach rób tak samo.
- `contractor_nip` osoby prowadzącej jednoosobową działalność to dane osobowe: nie pokazuj bez potrzeby (plik 05).
- Skrypty nie były uruchomione z Pythona przeciw żywemu API (szczegóły: `references/test-run.md`). Pierwsza komenda na własnym laptopie to test jednego dnia.

## Zmienne środowiskowe
`BZP_USER_AGENT` (przedstaw się, z kontaktem), `BZP_MIN_INTERVAL_S` (domyślnie 2.1), `BZP_API_BASE` (tylko do testów). Wzór: `.env.example` w katalogu pakietu.

## Zależności
Python 3.10+; `bzp_fetch.py` i `bzp_parse.py` tylko biblioteka standardowa; `bzp_join.py`, `sample_to_full.py`: pandas (BSD-3-Clause), numpy (BSD-3-Clause).
