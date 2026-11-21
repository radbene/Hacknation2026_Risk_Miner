---
name: riskminer-ekstrakcja-przyczyn
description: Klasyfikuje przyczyny zmian i opóźnień umów (teksty z ogłoszeń BZP) do taksonomii przyczyn oraz wyciąga ryzyka z dokumentów inwestycji (SWZ, umowa, studium wykonalności) modelem językowym z obowiązkowym cytatem. Użyj, gdy zespół prosi „dlaczego umowy się opóźniają", „sklasyfikuj przyczyny aneksów", „wyciągnij ryzyka z dokumentu", „zrób rejestr ryzyk z cytatami", „sprawdź, czy model nie zmyśla".
---

# riskminer-ekstrakcja-przyczyn

## Cel
Dwa zadania na tej samej taksonomii: (1) zamienić krótkie, swobodne opisy przyczyn zmian umów w kategorie, które da się policzyć i pokazać jako „najczęstsze przyczyny w podobnych umowach"; (2) z dokumentu inwestycji zrobić rejestr ryzyk, w którym każde ryzyko ma dosłowny cytat. Wzorce wywołań modelu (klucze, ponawianie, koszty): skill wspólny `hn-llm-w-produkcie`.

## Taksonomia (kody)
ZAKRES roboty dodatkowe i zamienne · PROJEKT błędy dokumentacji, zmiana rozwiązań · GRUNT_KOLIZJE warunki gruntowe, kolizje z sieciami, odkrycia · POGODA · DECYZJE pozwolenia i uzgodnienia · STRONA_TRZECIA prace innych podmiotów · KADRY zmiana kierownika budowy · ROZLICZENIE obmiar, waloryzacja · FINANSOWANIE dotacja, terminy programu · PRAWO zmiana przepisów · DOSTAWY · WYKONAWCA · NIEOKRESLONA (sama „konieczność zmiany terminu", odesłanie do protokołu). Dla dokumentów dodatkowo HARMONOGRAM i INNE.

## Ścieżki
Komendy uruchamiaj z katalogu głównego repozytorium, w którym leży `.claude/skills/`; dane robocze trzymaj w `data/` (utwórz katalog). Pliki `research/...` i `data-samples/...` są w pakiecie `prep/risk_miner/` repozytorium setup: instalując skille w repozytorium rozwiązania, skopiuj oba katalogi obok (np. do `docs/riskminer/`), inaczej odwołania do nich będą puste.

## Kroki: przyczyny zmian umów
1. Baseline bez modelu: `python3 .claude/skills/riskminer-ekstrakcja-przyczyn/scripts/classify_reasons.py --csv data/contracts.csv --col change_reasons --out data/reasons.csv` (wypisuje częstości kategorii).
2. Pomiar na zbiorze kontrolnym: `python3 .claude/skills/riskminer-ekstrakcja-przyczyn/scripts/classify_reasons.py --gold data-samples/bzp/change_reasons_holdout_32.jsonl`. Wynik baseline: F1 0,71.
3. Model językowy: prompt z `references/prompty.md` (sekcja A), po 20–50 tekstów w zapytaniu, wynik w JSON. Zmierz na tym samym zbiorze kontrolnym. Jeśli F1 nie przekracza 0,71, zostań przy baseline.
4. Do interfejsu: dla klasy referencyjnej danej inwestycji pokaż 5 najczęstszych kategorii z udziałem i 2–3 prawdziwymi przykładami tekstu z numerem ogłoszenia.

## Kroki: ryzyka z dokumentu
1. Zamień dokument na tekst (PDF: skill wspólny albo `pdftotext`). Zapisz tekst do pliku, bo walidator porównuje cytaty z tym samym tekstem.
2. Wywołaj model z promptem z `references/prompty.md` (sekcja B) i schematem `references/schemat-ryzyka.json`.
3. Zweryfikuj: `python3 .claude/skills/riskminer-ekstrakcja-przyczyn/scripts/validate_extraction.py --doc dokument.txt --llm wynik.json --out raport.json`. Ryzyka bez cytatu obecnego w dokumencie są odrzucane; kod wyjścia 1 oznacza, że coś odrzucono.
4. Do każdego przyjętego ryzyka dołącz częstość jego kategorii w danych BZP („w podobnych umowach ta przyczyna stanowiła X% zmian").

## Przykład wejście → wyjście
`classify_reasons.py --text "W trakcie realizacji prac konieczne okazało się usunięcie kolizji z siecią energetyczną, z uwagi na czasochłonny okres prowadzonych uzgodnień z zarządca sieci..."` → `{"labels": ["GRUNT_KOLIZJE", "DECYZJE"]}`.
Walidator na prawdziwym ogłoszeniu o zmianie umowy i trzech ryzykach (jedno poprawne, jedno ze zmyślonym cytatem, jedno z kategorią spoza listy): `Przyjete: 1, odrzucone: 2`.

## Kiedy nie używać
- Do ustalania winy: tekst przyczyny pisze zamawiający, często ogólnikowo (w próbce kontrolnej 9 z 32 tekstów nie podaje żadnej przyczyny).
- Do dokumentów z danymi osobowymi lub niejawnych przez zewnętrzne API: patrz `research/05`, wiersz o przetwarzaniu w API Claude.

## Pułapki
- Reguły baseline pisano na zbiorze `change_reasons_gold_26.jsonl`, więc wynik 1,0 na nim nic nie znaczy. Uczciwy pomiar to zbiór kontrolny (0,71). Nie poprawiaj reguł pod zbiór kontrolny; jeśli musisz, wylosuj nowy.
- Etykiety w obu zbiorach nadał model, nie ekspert. Przed pitchem niech jedna osoba przejrzy 32 etykiety (10 minut).
- Brakuje kategorii PODWYKONAWCY (2 z 32 tekstów kontrolnych). Dodaj ją w sobotę, jeśli będzie potrzebna.
- Według dokumentacji Anthropic odczytanej 2026-11-16 funkcji cytowań i wymuszonego schematu JSON nie da się łączyć w jednym zapytaniu [~]; dlatego cytaty sprawdzamy własnym walidatorem.
- Wywołania modelu nie były testowane w tej sesji (brak klucza API). Prompty w `references/prompty.md` są nieprzetestowanym punktem startu.

## Zależności
Tylko biblioteka standardowa; pandas (BSD-3-Clause) dla trybu `--csv`. Wyniki uruchomień: `references/test-run.md`.
