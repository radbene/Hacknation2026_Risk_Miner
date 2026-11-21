# Wyniki uruchomień (2026-11-16)

## classify_reasons.py
```
--gold change_reasons_gold_26.jsonl      {"n": 26, "precision": 1.0, "recall": 1.0, "f1": 1.0, "exact_match": 1.0}
--gold change_reasons_holdout_32.jsonl   {"n": 32, "precision": 0.75, "recall": 0.667, "f1": 0.706, "exact_match": 0.656}
--text "Konieczność wykonania robót dodatkowych i zamiennych."   {"labels": ["ZAKRES"]}
--csv /tmp/perf_fx.csv   Umowy z przyczynami: 1 z 2;  ZAKRES 1
```
Wynik 1,0 na pierwszym zbiorze jest bez wartości: reguły pisano, patrząc na te teksty. Zbiór kontrolny (32 teksty z innego dnia, etykiety nadane przed uruchomieniem) daje F1 0,71. Błędy na zbiorze kontrolnym: 5 tekstów o zakresie bez słów „roboty dodatkowe", 2 teksty o podwykonawcach (brak kategorii), 1 o finansowaniu, 3 z pominiętą drugą kategorią.

Wcześniejszy, prostszy zestaw słów kluczowych uruchomiony w przeglądarce na 140 przyczynach z 12.11.2026 nie przypisał żadnej kategorii 56 tekstom (40%). Najczęstsze kategorie: roboty dodatkowe i zamienne 57, kolizje i grunt 14, decyzje i uzgodnienia 8, pogoda 7, dokumentacja 7, dostawy 7.

## validate_extraction.py
Dokument: tekst prawdziwego ogłoszenia o zmianie umowy (2026/BZP 00535376). Wynik modelu napisany ręcznie do testu: 3 ryzyka, w tym jedno ze zmyślonym cytatem i jedno z kategorią „KORUPCJA".
```
Przyjete: 1, odrzucone: 2, udzial poprawnych: 0.333
  odrzucone #1: cytatu nie ma w dokumencie
  odrzucone #2: nieznana kategoria KORUPCJA
exit=1
```
NIE sprawdzono: żadnego wywołania modelu językowego (brak klucza API w sesji), promptów z `prompty.md`, dokumentów PDF.
