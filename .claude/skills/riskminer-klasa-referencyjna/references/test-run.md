# Wyniki uruchomień (2026-11-16)

## refclass_build.py na prawdziwej próbce 500 umów
```
Klasa referencyjna: n=500, opoznione 26.9%, wzrost kosztu 25.8%, komorek 18. Zapisano /tmp/ref_sample.json
by_value: <200k n=121 21.7% | 200k-1M n=243 22.6% | 1-5M n=101 33.7% | >=5M n=35 54.3%
```
Na próbce (bez dat wykonania) skrypt wypisał ostrzeżenie o braku rozkładu długości opóźnienia. Na danych syntetycznych z datami (3 000 umów) policzył go: względne `{'p25': 0.12, 'p50': 0.26, 'p75': 0.53, 'p90': 0.89, 'p95': 1.52}`, w dniach `{'p25': 12, 'p50': 33, 'p75': 83, 'p90': 188, 'p95': 294}`; `changed_pct` 49.4. Funkcja `period_bucket` zwraca `x:brak` dla okresu ujemnego i zerowego.

NIE sprawdzono: `refclass_build.py` na pełnych 2 318 umowach (tabelę z tych umów policzono w przeglądarce, patrz niżej) ani na zbiorze z walutą inną niż PLN.

## refclass_forecast.py z tabelą reference_table_bzp_works_2026-11.json
`--value 3200000 --period-days 270 --eu 1 --start 2026-12-01`:
```
p_late 0.451, n_cell 97, p_cost_up 0.571, ratio_q {p50 1.007, p80 1.096, p95 1.151},
days_p50 270, days_p80 360, days_p95 511, cost_p50 3226416, cost_p80 3507289, cost_p95 3682907,
reserve_p80_pct 9.6, p_within_both_p80 0.664, end_planned 2027-08-28, end_p50 2027-08-28, end_p80 2027-11-26
```
Kontrola rozkładu brzegowego: cost_p80 / value = 1.096 = ratio_p80 komórki. `--value 0` kończy się komunikatem „--value i --period-days musza byc wieksze od zera."

Historia: pierwsza wersja symulacji wiązała koszt z opóźnieniem w sposób, który psuł rozkład kosztu (rezerwa P80 wychodziła 5,6% zamiast 9,6%). Błąd znalazł niezależny przegląd; poprawiono na kopułę Gaussa i dodano powyższą kontrolę.
`--value 150000 --period-days 45 --eu 0`: `p_late 0.133, n_cell 292, p_cost_up 0.19`.

## Tryb --batch na 500 prawdziwych umowach (porównanie prognozy z wynikiem)
```
Zapisano 500 prognoz; srednie P(opoznienie) = 0.257
n 499  AUC 0.625  Brier 0.1856 (baza 0.1964)
przedzial prognozy   n    prognoza  faktycznie
(0.132, 0.139]      100   0.135     0.230
(0.139, 0.187]      169   0.185     0.183
(0.187, 0.189]       51   0.189     0.176
(0.189, 0.396]       97   0.329     0.320
(0.396, 0.663]       82   0.515     0.488
```
Zastrzeżenie: próbka 500 jest podzbiorem 2 318 umów, z których policzono tabelę, więc to nie jest test na danych niewidzianych. Najniższy przedział jest niedoszacowany (prognoza 13,5%, faktycznie 23%).

## Skąd tabela reference_table_bzp_works_2026-11.json
Komórki policzone w przeglądarce na 2 318 rekordach z API (parser w JavaScripcie o tej samej logice co `bzp_parse.py`). Marginesy `by_value` to średnie ważone z `by_value_eu`, więc ich kwantyle są przybliżone.
