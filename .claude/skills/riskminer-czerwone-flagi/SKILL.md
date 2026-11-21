---
name: riskminer-czerwone-flagi
description: Wyznacza sygnały ryzyka dla umów i inwestycji publicznych na podstawie reguł z dowodem: jedna oferta, tryb niekonkurencyjny, cena daleko od szacunku, napięty termin, historia opóźnień, termin minął bez ogłoszenia o wykonaniu, ogłoszenia o zmianie umowy. Użyj, gdy zespół prosi „policz czerwone flagi", „które umowy wymagają uwagi", „ranking ryzyka z uzasadnieniem", „sygnały ostrzegawcze w trakcie realizacji", „dlaczego ten projekt jest ryzykowny".
---

# riskminer-czerwone-flagi

## Cel
Dla każdej umowy lista sygnałów, z których każdy ma: kod, nazwę, wagę, dowód (wartość i pole źródłowe) i podstawę (przepis, literatura albo wynik z naszych danych). Wynik to kolejka do przejrzenia przez człowieka. Zasady języka i czerwone linie: `research/05_prawo_etyka_ryzyka.md`, sekcja (c).

## Ścieżki
Komendy uruchamiaj z katalogu głównego repozytorium, w którym leży `.claude/skills/`; dane robocze trzymaj w `data/` (utwórz katalog). Pliki `research/...` i `data-samples/...` są w pakiecie `prep/risk_miner/` repozytorium setup: instalując skille w repozytorium rozwiązania, skopiuj oba katalogi obok (np. do `docs/riskminer/`), inaczej odwołania do nich będą puste.

## Kroki
1. Przygotuj tabelę (`riskminer-dane-i-zrodla`). Dla sygnałów w trakcie realizacji dodaj kolumnę `n_change_notices` (liczba ogłoszeń o zmianie umowy z `changes.csv`, po `result_notice` albo `tender_id`) i zostaw `done` puste dla umów bez ogłoszenia o wykonaniu.
2. Uruchom:
   ```bash
   python3 .claude/skills/riskminer-czerwone-flagi/scripts/flags.py --data data/dataset.csv --out data/flags.jsonl \
       --table .claude/skills/riskminer-klasa-referencyjna/references/reference_table_bzp_works_2026-11.json --asof 2026-11-21
   ```
3. Przeczytaj podsumowanie: skrypt wypisuje, jak często umowy z daną flagą były opóźnione. Flagę, która nie różni się od odsetka ogólnego, pokaż jako informację, nie jako ryzyko realizacyjne.
4. W interfejsie pokazuj `level` słownie i listę flag z dowodem. Nie pokazuj samej liczby `score` bez listy.

## Przykład wejście → wyjście
Wejście: umowa z próbki (wolna ręka, 1 033 000 zł, 90 dni). Wyjście:
```json
{"id": "probka-0103", "score": 6, "level": "podwyzszona uwaga", "p_late_refclass": 0.419,
 "flags": [{"code": "K2", "name": "Tryb niekonkurencyjny", "severity": 2, "evidence": "tryb: zamówienie z wolnej ręki", "basis": "tryb bez ogloszenia: wskaznik CRI"},
           {"code": "H1", "name": "Krotki termin przy duzej wartosci", "severity": 2, "evidence": "90 dni na umowe za 1,033,000 zl", "basis": "napiety harmonogram (hipoteza...)"},
           {"code": "R1", "name": "Wysokie ryzyko w klasie referencyjnej", "severity": 2, "evidence": "w podobnych zakonczonych umowach opoznienie zadeklarowano w 42% przypadkow", "basis": "klasa referencyjna..."}]}
```

## Katalog flag
Pełny opis, progi i ich źródła: `references/katalog-flag.md`. Skrót: K1 jedna oferta, K2 tryb niekonkurencyjny, C1 cena poniżej 70% szacunku, C2 cena powyżej szacunku, C3 duży rozrzut ofert, C4 oferty z rażąco niską ceną, H1 krótki termin przy dużej wartości, H2 koniec robót zimą, R1 wysokie ryzyko w klasie referencyjnej, W1 historia wykonawcy, Z1 historia zamawiającego, S1 termin minął bez ogłoszenia o wykonaniu, S2 ogłoszenia o zmianie umowy.

## Kiedy nie używać
- Jako dowodu nieprawidłowości. Flaga to powód, żeby zajrzeć do dokumentów.
- Do oceniania osób fizycznych (jednoosobowe działalności): W1 wyłącz dla takich wykonawców albo pokazuj tylko zagregowane.
- Zamiast klasy referencyjnej: na próbce 500 umów klasyczne flagi zamówieniowe (K1, K2, C1) nie wiązały się z opóźnieniem, a R1 i Z1 tak (liczby w `references/test-run.md`).

## Pułapki
- Wagi (`severity`) są ekspercką oceną zespołu, nie wynikiem kalibracji; wynik łączny nie rośnie monotonicznie z odsetkiem opóźnień (grupa 4–6 punktów: 27% przy n=15).
- Historia wykonawcy i zamawiającego liczona jest z pominięciem ocenianej umowy; przy krótkim oknie danych prawie nikt nie ma trzech umów. Na pełnym zbiorze licz ją tylko z umów zakończonych przed datą zawarcia ocenianej.
- S1 zakłada obowiązek ogłoszenia w 30 dni od wykonania (art. 448 Pzp). Brak ogłoszenia może oznaczać zaniedbanie publikacji, nie opóźnienie robót.
- C1 i C2 przyjmują VAT 23% do porównania wartości netto i brutto.

## Zależności
pandas, numpy (BSD-3-Clause). Flaga R1 importuje `refclass_forecast.py` ze skilla `riskminer-klasa-referencyjna` (oba katalogi muszą leżeć obok siebie).
