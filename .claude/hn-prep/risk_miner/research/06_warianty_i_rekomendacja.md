# 06. Warianty pełnej treści i rekomendacja

Stan na 2026-11-16. Prawdopodobieństwa to ocena własna na podstawie opisu zadania, plików 01–02 i relacji z HackNation 2025; nie są faktami.

## Odpowiedź w skrócie

Niezależnie od wariantu budujemy ten sam rdzeń: **klasę referencyjną z rzeczywistych wyników zakończonych umów publicznych, sygnały ryzyka z dowodem i taksonomię przyczyn**. Rdzeń działa na danych publicznych sprawdzonych w tej sesji i przyjmie dane Partnera, jeśli je dostaniemy. O 11:00 w sobotę wybieramy tylko „skórkę": widok portfela (wariant A), kreator planowanej inwestycji (B) albo analizę dokumentu (C).

## Warianty pełnej treści

| # | Czego może żądać Partner | Prawd. | Uzasadnienie | Co wtedy budujemy |
|---|---|---|---|---|
| A | **Wczesne ostrzeganie w portfelu projektów.** Partner daje wyciąg danych o projektach (lista projektów, postęp, zmiany) i chce rankingu projektów zagrożonych z uzasadnieniem | 35% | NIK w 2026 r. opisuje ryzyka rozpoznawane po fakcie i „wskaźniki zagrożone" w KPO (plik 01, H1, H4); słowa „wcześniej identyfikować ryzyka" | Ranking portfela: każdy projekt dostaje prognozę z klasy referencyjnej, sygnały i przyczyny; widok „gdzie skierować uwagę w tym miesiącu" |
| B | **Planowanie inwestycji przed startem.** Narzędzie dla beneficjenta lub oceniającego wniosek: czy harmonogram i budżet są realistyczne, jakie ryzyka przewidzieć | 30% | Końcówka opisu: „skuteczniej planować realizację inwestycji"; wytyczne wymagają analizy ryzyka w studium wykonalności (plik 01) | Kreator: typ, wartość, okres, źródło finansowania → rozkład wyników podobnych umów, P50 i P80 terminu i kosztu, pięć najczęstszych przyczyn zmian z przykładami i mitygacją |
| C | **Analiza dokumentów.** Partner daje studia wykonalności, wnioski, umowy; oczekuje rejestru ryzyk | 20% | MFiPR wdraża moduł AI do grupowania wniosków o dofinansowanie (plik 01, H11), więc dokumenty są dla niego naturalnym materiałem | Rejestr ryzyk z cytatami, każdy z częstością tej kategorii w danych BZP („to ryzyko wystąpiło w X% podobnych umów") |
| D | **Zadanie otwarte bez danych.** „Zaproponuj, jak wykorzystać dane i AI" | 15% | Opis na hacknation.pl jest pytaniem („Jak wykorzystać dane, AI…?"), bez wzmianki o zbiorze danych; przy pozostałych zadaniach też brak zapowiedzi danych | Wariant B jako demo plus widok portfela na danych publicznych |

## Ocena koncepcji

| Kryterium (przypuszczalne) | A: portfel | B: kreator | C: dokumenty |
|---|---|---|---|
| Użyteczność dla Partnera | wysoka, jeśli połączymy projekty z umowami | wysoka dla beneficjentów i oceniających | średnia: rejestr ryzyk bez częstości to lista życzeń |
| Wdrażalność | średnia: wymaga łączenia danych | wysoka: tylko dane publiczne | niska do średniej: dane wrażliwe, koszt API |
| Jakość techniczna do obrony | wysoka (prawdziwe etykiety) | wysoka | zależy od złotego zbioru |
| Siła demo w 2 minuty | średnia (tabela) | wysoka (wpisujesz inwestycję, widzisz rozkład) | wysoka, ale ryzykowna na żywo |
| Wykonalność w 22 h | 3/5 (łączenie projektów z BZP jest niepewne) | 4/5 (tabela, prognoza i sygnały uruchomione na próbce 500 umów; pobieranie z Pythona i parser na pełnym HTML jeszcze nie) | 3/5 |

## Rekomendacja

**Budujemy kreator (B) na wspólnym rdzeniu i dokładamy widok portfela (A) na umowach współfinansowanych z UE.** Jedno zdanie dla jury: „Dla planowanej albo trwającej inwestycji pokazujemy, jak naprawdę kończyły się podobne umowy w Polsce, jakie sygnały ryzyka już widać i z jakich przyczyn umowy się zmieniają; każda liczba prowadzi do ogłoszeń w Biuletynie Zamówień Publicznych."

Wspólny rdzeń (działa w A, B, C i D):
1. Tabela umów z wynikami z ogłoszeń o wykonaniu umowy (skill `riskminer-dane-i-zrodla`).
2. Klasa referencyjna i symulacja terminu oraz kosztu (`riskminer-klasa-referencyjna`).
3. Sygnały z dowodem, w tym sygnały w trakcie realizacji: ogłoszenie o zmianie umowy, termin minął bez ogłoszenia o wykonaniu (`riskminer-czerwone-flagi`).
4. Taksonomia przyczyn zmian i walidator cytatów (`riskminer-ekstrakcja-przyczyn`).

Dlaczego to: dane i etykiety są sprawdzone (2 318 umów, plik 03); żadne narzędzie z pliku 02 nie pokazuje polskiej klasy referencyjnej; wynik jest wyjaśnialny bez modelu; a zmierzona siła predykcji (AUC ok. 0,7) uczciwie wystarcza do ustawiania kolejności uwagi, nie do wyroków.

## Który wariant wybrać w pierwszej godzinie

| Jeśli pełna treść… | to |
|---|---|
| daje tabelę projektów z etykietą problemu albo zapowiada metrykę | wariant A; najpierw `baseline.py` na danych Partnera, potem rdzeń jako cechy i wyjaśnienie |
| daje tabelę projektów bez etykiety | wariant A z klasą referencyjną z BZP jako źródłem prognoz; sprawdź, czy da się połączyć po NIP albo numerze projektu |
| mówi o planowaniu, wnioskach, beneficjentach | wariant B |
| daje dokumenty | wariant C, ale z częstościami z rdzenia; ogranicz się do jednego typu dokumentu |
| jest ogólna | B jako demo, A jako drugi ekran |
| dotyczy czegoś spoza zamówień i projektów (np. ryzyka makro, kursy, podaż wykonawców) | sygnał „nie bierzemy" (README) |

## Najmocniejszy kontrargument i odpowiedź

**Kontrargument.** „To są dane o małych umowach gminnych. Ministerstwo martwi się o duże projekty: kolej, drogi ekspresowe, programy za miliardy. W waszej próbce jest 54 umów powyżej progów unijnych, a etykieta to deklaracja urzędnika."

**Odpowiedź.** Po pierwsze, większość projektów unijnych co do liczby to właśnie inwestycje samorządów: w 12 dniach listopada znalazłem 340 zakończonych umów z oznaczeniem projektu UE, co daje rząd kilku tysięcy rocznie. Opóźniają się częściej niż pozostałe (34,8% wobec 23,8%), ale głównie dlatego, że są większe: w przedziale 1–5 mln zł różnicy nie ma (40,9% wobec 41,5%), a różnica zostaje tylko poniżej 1 mln zł (np. 29,7% wobec 19,7% dla 200 tys.–1 mln zł). Po drugie, obowiązek ogłoszenia o wykonaniu umowy dotyczy też zamówień powyżej progów (art. 448 Pzp), więc dłuższe okno danych da więcej dużych umów; do megaprojektów dokładamy przypadki z raportów NIK i sprawozdań Europejskiego Trybunału Obrachunkowego jako osobną, jawnie małą klasę referencyjną. Po trzecie, metoda nie zależy od źródła: `refclass_build.py` przyjmie wyciąg z CST2021, jeśli ma on wartość, planowany okres i wynik projektu (czas przygotowania zależy od formatu danych, którego nie znamy). Co do deklaracji: pokazujemy drugą miarę z różnicy dat i mówimy wprost, gdzie się różnią (plik 04).

Drugi kontrargument, krótszy: „AUC 0,7 to mało". Odpowiedź: nie sprzedajemy przewidywania pojedynczej umowy, tylko częstości bazowe, których dziś nikt planującemu nie pokazuje, oraz sygnały w trakcie realizacji. W teście na 129 umowach precyzja w górnych 10% rankingu (13 umów) była dwa razy wyższa od odsetka bazowego; to mała próba i liczbę trzeba powtórzyć na pełnym zbiorze.
