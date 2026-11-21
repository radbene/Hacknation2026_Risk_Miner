---
name: riskminer-klasa-referencyjna
description: Liczy prognozę z klasy referencyjnej dla inwestycji: jak często podobne zakończone umowy publiczne były opóźnione lub droższe, oraz P50 i P80 terminu i kosztu z symulacji Monte Carlo. Użyj, gdy zespół prosi „jakie jest ryzyko opóźnienia dla takiej inwestycji", „policz rezerwę na P80", „zbuduj tabelę referencyjną", „czy ten harmonogram jest realistyczny", „reference class forecasting" albo potrzebuje prognozy dla listy projektów.
---

# riskminer-klasa-referencyjna

## Cel
Zamiast pytać „co może pójść źle w tym projekcie", pokazujemy, co faktycznie stało się w podobnych zakończonych umowach. Uzasadnienie metody i liczby do cytowania: `research/04_technologia_i_ewaluacja.md`; pochodzenie danych: `research/03_dane_i_api.md`.

## Ścieżki
Komendy uruchamiaj z katalogu głównego repozytorium, w którym leży `.claude/skills/`; dane robocze trzymaj w `data/` (utwórz katalog). Pliki `research/...` i `data-samples/...` są w pakiecie `prep/risk_miner/` repozytorium setup: instalując skille w repozytorium rozwiązania, skopiuj oba katalogi obok (np. do `docs/riskminer/`), inaczej odwołania do nich będą puste.

## Kroki
1. **Tabela referencyjna.** Gotowa z 2 318 umów (roboty, ogłoszenia 2–13.11.2026): `.claude/skills/riskminer-klasa-referencyjna/references/reference_table_bzp_works_2026-11.json`. Na pełnym zbiorze zbuduj nową:
   ```bash
   python3 .claude/skills/riskminer-klasa-referencyjna/scripts/refclass_build.py --data data/dataset.csv --out data/reference_table.json --source "BZP, roboty, ogłoszenia 2025-11..2026-11"
   ```
2. **Prognoza dla jednej inwestycji:**
   ```bash
   python3 .claude/skills/riskminer-klasa-referencyjna/scripts/refclass_forecast.py --table data/reference_table.json --value 3200000 --period-days 270 --eu 1 --start 2026-12-01
   ```
3. **Prognoza dla listy** (CSV z kolumnami `value`, `period_days`, opcjonalnie `eu`): `--batch plik.csv --out prognozy.csv`.
4. **W interfejsie** zawsze pokazuj razem: odsetek, liczebność klasy (`n_cell`), źródło i okres danych oraz założenia zwrócone w polu `assumptions`.

## Przykład wejście → wyjście
Wejście: wartość 3 200 000 zł, 270 dni, projekt UE, start 2026-12-01. Wyjście (tabela z listopada 2026):
`p_late 0.451 (klasa: 1–5 mln zł, 241–480 dni, n=97), p_cost_up 0.571, days_p50 270, days_p80 360, end_planned 2027-08-28, end_p80 2027-11-26, cost_p80 3 507 289 zł, reserve_p80_pct 9.6, p_within_both_p80 0.664`.
Zdanie dla użytkownika: „W 97 podobnych zakończonych umowach opóźnienie zadeklarowano w 46% przypadków (prognoza po korekcie o liczebność klasy i finansowanie UE: 45%). W 80% symulacji inwestycja kończy się do 26.11.2027; osobno, w 80% symulacji koszt nie przekracza 3,51 mln zł. Oba warunki naraz spełnia 66% symulacji." Nie łącz dwóch P80 w jedno zdanie „z prawdopodobieństwem 80% zmieści się w terminie i budżecie": to nieprawda.

## Jak to liczy
- Odsetek z komórki wartość × planowany okres jest ściągany do odsetka dla przedziału wartości, a ten do ogólnego: (k + 20·p_rodzica)/(n + 20). Mała komórka nie da skrajnej prognozy.
- Finansowanie UE koryguje szanse ilorazem z tabeli `by_value_eu`, osłabionym przy małej liczbie umów.
- Symulacja (20 000 losowań): opóźnienie tak/nie, długość opóźnienia z kwantyli opóźnienia względnego wśród umów opóźnionych (mediana 28% planowanego okresu), koszt końcowy z kwantyli wypłata/wartość. Opóźnienie i koszt wiąże kopuła Gaussa z korelacją 0,45, oszacowaną na próbce: wzrost kosztu wystąpił w 46% umów opóźnionych i 19% terminowych. Rozkład brzegowy kosztu zgadza się z tabelą (P80 kosztu = wartość × `ratio_p80`).

## Kiedy nie używać
- Megaprojekty (setki milionów zł, wieloletnie): w tabeli jest 127 umów od 5 mln zł i prawie nic powyżej 50 mln zł. Dla nich cytuj literaturę z pliku 04 i mów wprost, że klasa jest inna.
- Dostawy i usługi: tabela dotyczy robót budowlanych. Trzeba pobrać `OrderType=Delivery|Services` i zbudować osobną.
- Jako wyrok o konkretnym wykonawcy: to częstość w grupie, nie ocena podmiotu.

## Pułapki
- Tabela z 12 dni publikacji zaniża udział długich kontraktów (82% umów zawarto w 2026 r.). Przed demo przebuduj ją z 12 miesięcy.
- „Opóźnienie" to deklaracja zamawiającego (pole 5.3). Opisuj jako „zadeklarowano opóźnienie".
- Ogony rozkładów (opóźnienie powyżej P90, koszt powyżej P95) są ekstrapolowane, a korelacja pochodzi z 493 umów. Skrypt wypisuje to w polu `assumptions`; nie usuwaj tej informacji z interfejsu.
- Tabela zbudowana z danych bez dat zawarcia i wykonania umowy (np. z próbki) nie ma rozkładu długości opóźnienia: `refclass_build.py` ostrzega o tym, a prognoza używa rozkładu domyślnego z listopada 2026 i zapisuje to w `assumptions`.
- `refclass_build.py` pomija umowy w walucie innej niż PLN i okresy niedodatnie.
- Nie potwierdzono w dokumentacji UZP, czy pole 5.2 „Termin wykonania umowy" to data faktycznego wykonania; przykłady na to wskazują (plik 03).
- AUC samej tabeli na próbce to 0,63 i jest zawyżone (próbka pochodzi z tych samych danych). Tabela służy do kalibracji oczekiwań, nie do rankingu pojedynczych umów.

## Zależności
numpy (BSD-3-Clause), pandas (BSD-3-Clause, tylko budowa tabeli i tryb `--batch`). Wyniki uruchomień: `references/test-run.md`.
