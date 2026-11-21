# Wideo – scenariusz (cel 175 s, limit 3:00)

Nagranie: ekran z aplikacją pod adresem z wersji działającej, 1920×1080, głos lektora. Sprawdzenie:
`bash .claude/skills/hn-zgloszenie/scripts/video_check.sh nagranie.mov --max 175 --fix docs/demo.mp4`.
Przed nagraniem: `riskminer demo` na serwerze, „Przywróć stan demo”, przeglądarka w trybie incognito, powiększenie
125%. Zdarzenia i liczby podmień na wartości z bazy w dniu nagrania.

| Czas | Ekran | Lektor |
|---|---|---|
| 0:00–0:12 | strona główna (dashboard z liczbami) | „RISK MINER to baza doświadczeń inwestycji wod-kan dla instytucji zarządzających. Każdy wniosek ma źródło w publicznych danych i akceptację eksperta.” |
| **Ścieżka A – baza doświadczeń** | | |
| 0:12–0:30 | „Źródła” → „Wzbogać” na liście 22 projektów; dziennik zapytań BZP się zapełnia | „Startujemy od listy 22 projektów. System sam odpytuje BZP i Białą listę VAT, a każde zapytanie trafia do dziennika.” |
| 0:30–0:55 | karta Nowogard (RM-2026-020): graf projekt → postępowanie → umowa → 2 zmiany | „Dla Nowogardu znalazł postępowanie, umowę i dwie zmiany terminu. Pierwsza to brak służebności przesyłu (R03), druga to złe warunki gruntowe (R02).” |
| 0:55–1:10 | klik w zdarzenie → podświetlona sekcja ogłoszenia, link ezamowienia.gov.pl, data pobrania | „Kliknięcie pokazuje dokładny fragment ogłoszenia z trwałym linkiem. Wynik bez źródła nie istnieje.” |
| 1:10–1:30 | „Kolejka” → Wolin RM-2026-022: niepewne powiązanie z wyjaśnieniem i pułapką → „Przepnij” / „Akceptuj” → historia | „Numer BZP z listy dla Wolina nie istnieje. System proponuje kandydata z wyjaśnieniem i pokazuje pułapkę. Ekspert decyduje, a decyzja przetrwa ponowne przetwarzanie.” |
| **Ścieżka B – nowa inwestycja** | | |
| 1:30–1:45 | „Nowa inwestycja” → wklejenie opisu (sieć kanalizacyjna, 12 km, 2,4 mln zł, 14 mies.) → cechy z oznaczonym źródłem | „Teraz nowa inwestycja: wklejamy opis, a system odczytuje cechy i pokazuje, skąd każda pochodzi.” |
| 1:45–2:05 | podobne projekty z rozbiciem podobieństwa; zakresy kosztu i czasu z n | „W podobnych zakończonych umowach termin wydłużał się o {{X}} dni (n = {{N}}); widać, dlaczego każdy przypadek jest podobny.” |
| 2:05–2:25 | ocena budżetu i harmonogramu; flagi R-kody; działania i klauzule | „Harmonogram 14 miesięcy jest poniżej mediany podobnych inwestycji. Sygnały do przejrzenia: kolizje sieci i warunki gruntowe. Proponujemy klauzule i działania.” |
| 2:25–2:38 | eksport DOCX/JSON; „Wiedza”: edycja katalogu R01–R15 | „Wynik eksportujemy, a ekspert może edytować katalog ryzyk i wagi bez programisty.” |
| 2:38–2:50 | „Monitoring”: suwak `as_of` → nowe ogłoszenie → alert | „Dla inwestycji w toku system obserwuje BZP i sam ponawia analizę po każdym nowym ogłoszeniu.” |
| 2:50–2:55 | slajd końcowy: link, „działa na serwerze w UE, LLM opcjonalny” | „Dane publiczne, serwer w UE, kod na licencji Apache. Link w opisie.” |

Plan awaryjny: nagranie z lokalnego stosu (`deploy/local-prod-test.sh up`, `LLM_MODE=replay`), bez sieci.
