# Prezentacja (≤ 10 slajdów) – plan

PDF: `docs/prezentacja.pdf`. Jeden slajd = jedna myśl, zrzut ekranu z prawdziwych danych, maks. 25 słów tekstu.
Słownictwo Partnera: „instytucja zarządzająca”, „beneficjent”, „ryzyko realizacyjne (termin, koszt)”, „sygnał do
przejrzenia”; nie: „podejrzany”, „scoring”, „przewidujemy, że się opóźni”.

| # | Tytuł | Treść / zrzut |
|---|---|---|
| 1 | RISK MINER – baza doświadczeń inwestycji wod-kan | jedno zdanie + liczba z bazy: {{X% zakończonych umów wod-kan miało zmianę terminu}} · link do wersji działającej |
| 2 | Problem | doświadczenia są w publicznych ogłoszeniach (zmiana umowy, wykonanie umowy, NIK), ale nie są powiązane z projektami i nie są udokumentowane |
| 3 | Jak budujemy bazę (ścieżka A) | diagram łańcucha projekt → postępowania → ogłoszenia → umowa → zmiany → zdarzenia; liczby rekordów z dashboardu |
| 4 | Każdy fakt ma źródło | zrzut: kliknięcie zdarzenia Nowogard → podświetlona sekcja 5.4.4 ogłoszenia + trwały link ezamowienia.gov.pl |
| 5 | Łączenie danych – jakość | precyzja / kompletność na zbiorze wzorcowym; przykład Wolin (błędny numer BZP w xlsx → powiązanie z wyjaśnieniem i pułapką) |
| 6 | Ekspert decyduje | kolejka przeglądu: akceptuj / popraw / odrzuć / przepnij; historia; zatwierdzone dane nie są nadpisywane |
| 7 | Nowa inwestycja (ścieżka B) | zrzut: podobne projekty z rozbiciem podobieństwa → zakresy (n, przedział) → ocena budżetu i harmonogramu |
| 8 | Flagi, działania, klauzule | R-kody z uzasadnieniem i źródłem, propozycje klauzul, eksport DOCX/JSON |
| 9 | Skala i wdrożenie | poziom auto: tysiące postępowań z BZP; monitoring + `as_of`; serwer w UE; LLM opcjonalny (lokalny / UE / bez LLM); nowy sektor = nowe pliki wiedzy |
| 10 | Co działa, co dalej | tabela działa / zaprojektowane (skrót); prośba o pilotaż: wyciąg CST2021 dla jednego programu |
