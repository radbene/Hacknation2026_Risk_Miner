# Raport z testu – RISK MINER

Wygenerowano automatycznie: 2026-11-22 01:26 CET (`riskminer report`). Wszystkie liczby pochodzą z bazy po przebiegu `riskminer demo`; nic nie jest wpisane ręcznie.

## 1. Liczba rekordów

| Tabela | Rekordy |
|---|---|
| project | 34421 |
| procedure | 45055 |
| project_procedure | 34421 |
| notice | 112729 |
| contract | 39094 |
| contract_change | 26804 |
| event | 104 |
| document | 3 |
| chunk | 4 |
| evidence | 872767 |
| data_issue | 162 |
| analysis | 8 |
| analysis_item | 350 |
| alert | 13465 |
| knowledge_table | 21 |
| review | 60 |
| op_log | 733 |
| llm_call | 89 |
| raw_record | 113682 |

Postępowania wg poziomu szczegółowości: **auto**: 44684, **deep**: 371.

## 2. Powiązania projekt → postępowanie vs zbiór wzorcowy

Zbiór wzorcowy: 95 wierszy (ręcznie zweryfikowanych), 22 projektów, 22 oczekiwanych powiązań (projekt, OCID, część).

| Wynik | Liczba | Znaczenie |
|---|---|---|
| poprawne | 22 | powiązanie zgodne ze wzorcem (zatwierdzone lub pewność ≥ 0,9) |
| niepewne | 0 | zgodne, ale czeka w kolejce przeglądu eksperta |
| błędne | 0 | powiązanie z pułapką / inną częścią / spoza wzorca |
| brakujące | 0 | oczekiwane powiązanie nie zostało znalezione |

Precyzja: **1** · kompletność (recall): **1** · precyzja powiązań automatycznych: **1**.

Ocena obejmuje projekty z pliku organizatora (warstwa pogłębiona). Warstwa automatyczna z kopii BZP (jedno postępowanie = jedna inwestycja) nie ma wzorca i służy jako tło do porównań w analizie nowej inwestycji.

Projekty, dla których wzorzec stwierdza brak ogłoszeń w BZP: RM-2026-022.

Poziom ogłoszeń (moduł dopasowania, `riskminer.link.quality.evaluate`):

| Miara | Wartość |
|---|---|
| projekty | 22 |
| ogłoszenia wzorcowe | 76 |
| ogłoszenia powiązane | 76 |
| trafione | 76 |
| nadmiarowe | 0 |
| pominięte | 0 |
| precyzja | 1 |
| kompletność | 1 |
| F1 | 1 |
| projekty w pełni poprawne | 22 |
| projekty niepewne (pewność < 0,95) | 5 |

## 3. Błędy i braki w danych organizatora

Wykryte problemy wg rodzaju: completeness: 161, organizer_error: 1.

| Projekt | Rodzaj | Pole | Stan | Opis |
|---|---|---|---|---|
| RM-2026-012 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-010 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-018 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-005 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-011 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-021 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-003 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-019 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-004 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-015 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-013 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-009 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-016 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-001 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-008 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-017 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-020 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-007 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-006 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-014 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-022 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-002 | completeness | dokumenty: aneksy/protokoły | nie_ma_w_paczce | Brak w paczce: aneksy/protokoły. |
| RM-2026-004 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-012 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-001 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-014 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-013 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-002 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-020 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-022 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-003 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-019 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-005 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-006 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-018 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-007 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-017 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-008 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-009 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-016 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-021 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-010 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-015 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-011 | completeness | dokumenty: OPZ/PFU/projekt | nie_ma_w_paczce | Brak w paczce: OPZ/PFU/projekt. |
| RM-2026-006 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-009 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-011 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-018 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-014 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-007 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-001 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-016 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-008 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-015 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-004 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-012 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-002 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-022 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-010 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-021 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-019 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-005 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-017 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-013 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-003 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-020 | completeness | dokumenty: SWZ | nie_ma_w_paczce | Brak w paczce: SWZ. |
| RM-2026-012 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-018 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-010 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-006 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-021 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-015 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-007 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-020 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-022 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-017 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-008 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-001 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-016 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |
| RM-2026-009 | completeness | dokumenty: umowa/PPU | nie_ma_w_paczce | Brak w paczce: umowa/PPU. |

## 4. Zdarzenia i przyczyny (projekty organizatora)

| Rodzaj zdarzenia | Metoda | Status | Liczba |
|---|---|---|---|
| zmiana terminu | Bielik (z cytatem) | czeka na eksperta | 3 |
| zmiana terminu | reguły | czeka na eksperta | 1 |
| zmiana terminu | reguły | poprawione przez eksperta | 2 |
| zmiana terminu | Bielik (z cytatem) | zatwierdzone | 4 |
| zmiana zakresu | reguły | czeka na eksperta | 1 |
| zmiana zakresu | Bielik (z cytatem) | zatwierdzone | 1 |
| zmiana zakresu | Bielik (z cytatem) | czeka na eksperta | 18 |
| zmiana zakresu | Bielik (z cytatem) | poprawione przez eksperta | 1 |
| zmiana wynagrodzenia | Bielik (z cytatem) | czeka na eksperta | 7 |
| zmiana wynagrodzenia | reguły | czeka na eksperta | 1 |
| sygnał ryzyka w dokumencie | reguły | czeka na eksperta | 5 |
| sygnał ryzyka w dokumencie | Bielik (z cytatem) | odrzucone | 3 |
| sygnał ryzyka w dokumencie | reguły | odrzucone | 5 |
| sygnał ryzyka w dokumencie | Bielik (z cytatem) | czeka na eksperta | 6 |
| nienależyte wykonanie / kary | reguły | czeka na eksperta | 5 |
| opóźnienie | reguły | czeka na eksperta | 19 |
| wypłata ponad wartość umowy | reguły | czeka na eksperta | 19 |
| powtórzone postępowanie | reguły | czeka na eksperta | 1 |
| powtórzone postępowanie | Bielik (z cytatem) | czeka na eksperta | 2 |

Dokumenty wgrane do projektów:

| Projekt | Plik | Rodzaj | Warstwa tekstowa |
|---|---|---|---|
| RM-2026-002 | Risk_Miner_protokol_konieczności_aneksowania_zagrodno.pdf | protokół | tak |
| RM-2026-005 | Risk_Miner_protokol_koniecznosci_zławieś.docx | protokół | tak |
| RM-2026-010 | Risk_Miner_pismo_termin_grodzisko.pdf | – | OCR (Tesseract, pewność 94,9%) |

## 5. Monitoring

| Rodzaj alertu | Waga | Liczba |
|---|---|---|
| new_notice | warning | 92 |
| new_notice | info | 2508 |
| deadline_passed | high | 7187 |
| deadline_passed | warning | 3678 |

## 6. Analizy nowych inwestycji

### 01 siec wodociagowa

- wynik: działania: 8, oceny: 7, flagi: 9, podobne inwestycje: 12, zakresy: 9
- model językowy: nie użyto (same reguły i obliczenia)
- budżet: nie porównano: nie wiadomo, czy kwota jest netto czy brutto
- harmonogram: wyżej niż połowa podobnych
- flagi: Roboty przy czynnym obiekcie; Opis wskazuje brak lub niepewność; Opis wskazuje brak lub niepewność; Trasa / teren wymaga praw do nieruchomości; Inwestycja zależy od decyzji i uzgodnień podmiotów trzecich; Nieprzewidziane zmiany i roboty dodatkowe: u 4 z 12 podobnych inwestycji

### 02 kanalizacja sanitarna

- wynik: działania: 10, oceny: 7, flagi: 11, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 22 755 000 zł – wyżej niż 9 na 10 podobnych (kwota netto × 1,23 (ZAŁOŻENIE: VAT 23%) porównana z kwotami brutto); rezerwa P80: 25 765 486 zł
- harmonogram: niżej niż połowa podobnych
- flagi: Krótki harmonogram na tle sąsiadów (percentyl 10%); Kolizje z istniejącą infrastrukturą; Uwarunkowania środowiskowe lub gruntowo-wodne; Opis wskazuje brak lub niepewność; Inwestycja zależy od decyzji i uzgodnień podmiotów trzecich; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności

### 03 oczyszczalnia suw

- wynik: działania: 7, oceny: 7, flagi: 9, podobne inwestycje: 12, zakresy: 9
- model językowy: nie użyto (same reguły i obliczenia)
- budżet: 41 300 000 zł – wyżej niż 9 na 10 podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 41 766 690 zł
- harmonogram: wyżej niż połowa podobnych
- flagi: Roboty przy czynnym obiekcie; Opis wskazuje brak lub niepewność; Opis wskazuje brak lub niepewność; Nieprzewidziane zmiany i roboty dodatkowe: u 3 z 12 podobnych inwestycji; Unieważnienia z powodu ceny powyżej budżetu: 23% podobnych postępowań; Zmiana umowy prawdopodobna: 64%

### Przykład – kanalizacja sanitarna

- wynik: działania: 8, oceny: 7, flagi: 7, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 9 800 000 zł – wyżej niż połowa podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 10 462 480 zł
- harmonogram: niżej niż 9 na 10 podobnych
- flagi: Krótki harmonogram na tle sąsiadów (percentyl 9%); Trasa / teren wymaga praw do nieruchomości; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności; Nieprzewidziane zmiany i roboty dodatkowe: u 3 z 12 podobnych inwestycji; Zmiana umowy prawdopodobna: 70%; Wysokie prawdopodobieństwo opóźnienia: 44%

### Przykład – kanalizacja sanitarna

- wynik: działania: 8, oceny: 7, flagi: 6, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 9 800 000 zł – wyżej niż połowa podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 9 879 380 zł
- harmonogram: niżej niż 9 na 10 podobnych
- flagi: Wysokie prawdopodobieństwo opóźnienia: 59%; Krótki harmonogram na tle sąsiadów (percentyl 9%); Trasa / teren wymaga praw do nieruchomości; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności; Niewystarczająca zdolność wykonawcy lub łańcucha dostaw: u 3 z 12 podobnych inwestycji; Zmiana umowy prawdopodobna: 70%

### Przykład: kanalizacja sanitarna

- wynik: działania: 8, oceny: 7, flagi: 6, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 9 800 000 zł – wyżej niż połowa podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 9 879 380 zł
- harmonogram: niżej niż 9 na 10 podobnych
- flagi: Wysokie prawdopodobieństwo opóźnienia: 59%; Krótki harmonogram na tle sąsiadów (percentyl 9%); Trasa / teren wymaga praw do nieruchomości; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności; Niewystarczająca zdolność wykonawcy lub łańcucha dostaw: u 3 z 12 podobnych inwestycji; Zmiana umowy prawdopodobna: 70%

### Przykład: kanalizacja sanitarna

- wynik: działania: 8, oceny: 7, flagi: 6, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 9 800 000 zł – wyżej niż połowa podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 9 879 380 zł
- harmonogram: niżej niż 9 na 10 podobnych
- flagi: Wysokie prawdopodobieństwo opóźnienia: 59%; Krótki harmonogram na tle sąsiadów (percentyl 9%); Trasa / teren wymaga praw do nieruchomości; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności; Niewystarczająca zdolność wykonawcy lub łańcucha dostaw: u 3 z 12 podobnych inwestycji; Zmiana umowy prawdopodobna: 70%

### Przykład: kanalizacja sanitarna

- wynik: działania: 8, oceny: 7, flagi: 6, podobne inwestycje: 12, zakresy: 9
- model językowy: Bielik (podsumowanie i działania, oznaczone „Wniosek modelu”)
- budżet: 9 800 000 zł – wyżej niż połowa podobnych (kwota brutto porównana z kwotami brutto); rezerwa P80: 9 879 380 zł
- harmonogram: niżej niż 9 na 10 podobnych
- flagi: Wysokie prawdopodobieństwo opóźnienia: 59%; Krótki harmonogram na tle sąsiadów (percentyl 9%); Trasa / teren wymaga praw do nieruchomości; Formuła „zaprojektuj i wybuduj” (PFU): ryzyko zakresu i odpowiedzialności; Niewystarczająca zdolność wykonawcy lub łańcucha dostaw: u 3 z 12 podobnych inwestycji; Zmiana umowy prawdopodobna: 70%

## 7. Integracja ze źródłami (op_log)

| Źródło | Operacja | Zapytania | Wyniki | Błędy | Ostatnio |
|---|---|---|---|---|---|
| bzp | notice_pdf | 3 | – | 0 | 2026-11-21 23:38 |
| bzp | search | 728 | 10418 | 0 | 2026-11-21 18:58 |
| bzp_zip | load | 2 | 113776 | 0 | 2026-11-21 18:58 |

## 8. Wywołania modeli językowych

| Zadanie | Dostawca | Miejsce przetwarzania | Wywołania | Z cache | Koszt USD |
|---|---|---|---|---|---|
| features | openai | local | 5 | 0 | 0 |
| recommendations | openai_compatible | local | 24 | 10 | 0 |
| recommendations | openai | local | 5 | 0 | 0 |
| features | openai_compatible | local | 4 | 4 | 0 |
| llm_test | openai_compatible | local | 1 | 0 | 0 |
| llm_test | openai | local | 2 | 0 | 0 |
| causes | openai | local | 43 | 3 | 0 |
| doc_fragments | openai_compatible | local | 4 | 0 | 0 |
| causes | anthropic | non_eu | 1 | 0 | 0 |

