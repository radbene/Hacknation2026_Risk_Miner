# RISK MINER – opis rozwiązania

*HackNation 2026 · zadanie Ministerstwa Funduszy i Polityki Regionalnej · pilotaż: gospodarka wodno-kanalizacyjna.*
*Limit: 10 stron. Wersja PDF: `docs/opis_rozwiazania.pdf` (pandoc / druk z przeglądarki).*

## 1. Problem i odbiorca (½ strony)

Instytucja zarządzająca i beneficjent planują inwestycję wod-kan, nie widząc doświadczeń podobnych inwestycji. Te
doświadczenia istnieją w danych publicznych: ogłoszenia o zmianie umowy (podstawa i przyczyna z art. 455), ogłoszenia
o wykonaniu umowy (termin, zapłacona kwota, liczba zmian), wyniki postępowań (liczba ofert, ceny), raporty NIK.
Brakuje powiązania ich z projektami, skategoryzowania (R01–R15) i udokumentowania, tak aby ekspert mógł
im zaufać.

{{1–2 zdania z liczbą z bazy: np. „w N zakończonych umowach wod-kan z lat 2021–2026 X% zadeklarowało zmianę terminu”}}

## 2. Rozwiązanie w skrócie (1 strona)

- **Baza doświadczeń (ścieżka A):** z listy projektów organizatora i BZP budujemy łańcuch projekt → postępowania →
  ogłoszenia → umowa → zmiany → zdarzenia → koszty i terminy → dokumenty, a każdy element ma dowód.
- **Analiza nowej inwestycji (ścieżka B):** z opisu lub dokumentu: podobne zakończone projekty z wyjaśnieniem,
  zakresy odchyleń kosztu i czasu z liczebnością próby i niepewnością, ocena budżetu i harmonogramu, flagi, działania
  i klauzule umowne. Wynik to rekordy do zatwierdzenia i eksportu (JSON/CSV/DOCX).
- **Kontrola eksperta:** nic nie jest „prawdą” bez akceptacji; korekty, odrzucenia, przepięcia powiązań i edycje
  wiedzy są wersjonowane i nie giną przy ponownym przetwarzaniu.
- **Monitoring (bonus):** obserwacja niezakończonych inwestycji, alert przy nowym ogłoszeniu, ponowna analiza, tryb
  odtwarzania historii `as_of`.

## 3. Co działa, a co jest zaprojektowane (1½ strony)

Tabela generowana z `docs/status.md` (`riskminer.monitor.docs_gen.status_table()`); wklejana przy zamrożeniu kodu.

{{TABELA_DZIALA_ZAPROJEKTOWANE}}

## 4. Pozyskanie i łączenie danych (1½ strony)

Skrót [zrodla_i_dopasowanie.md](zrodla_i_dopasowanie.md): źródła, dziennik zapytań, parser DOM, dopasowanie po kluczach i
kandydatach z oceną, części zamówień, pułapki.
Wyniki na zbiorze wzorcowym (z [raport_z_testu.md](raport_z_testu.md) §2): {{PRECYZJA / RECALL / C-U-W-M}}.
Przykłady: Oława (pełny łańcuch), Biecz część 1, Nowogard (2 zmiany: R03 służebność, R02 warunki gruntowe),
Wolin RM-2026-022 (numer BZP z xlsx nie istnieje, powiązanie przez ogłoszenie o zmianie i pułapkę).

## 5. Zdarzenia, przyczyny i dokumenty (1½ strony)

- reguły na polach ogłoszeń (po terminie, zapłata powyżej wartości, zmiany terminu/wynagrodzenia/zakresu,
  unieważnienie, powtórzenie, jedna oferta, oferty powyżej budżetu);
- przyczyny zmian: reguły + model językowy z obowiązkowym cytatem sprawdzanym względem źródła;
- dokumenty PDF/DOCX: fragmenty ryzyk ze stroną/akapitem; lekcje NIK;
- skutek (dni, PLN, %), środek zaradczy i jego skuteczność.
{{TRAFNOSC_PRZYCZYN na zbiorze 26 + 32}}

## 6. Analiza nowej inwestycji (2 strony)

Przebieg na fixture'ach z `backend/tests/fixtures/new_investments/` ([raport_z_testu.md](raport_z_testu.md) §5) i
przykładowy eksport [exports/przyklad/](../exports/przyklad/).
{{zrzut ekranu: sąsiedzi z rozbiciem podobieństwa · zakresy z n · ocena budżetu P50/P80 · flagi · klauzule}}

## 7. Kontrola eksperta i modułowość (1 strona)

Statusy, kolejka przeglądu, akceptacja hurtowa powiązań z kluczem, historia, propozycje przy ponownym przetwarzaniu,
edytor tabel wiedzy (import z docx eksperta → YAML → wersje w bazie), routing modeli per zadanie z miejscem
przetwarzania danych, rejestr konektorów (nowe źródło = nowa klasa), nowy sektor = nowe pliki wiedzy.

## 8. Architektura, wdrożenie, bezpieczeństwo (1 strona)

Skrót [architektura.md](architektura.md) i [uruchomienie.md](uruchomienie.md). Serwer w UE; LLM opcjonalny
(profile local / eu / non_eu / none); dane osobowe usuwane przed wysłaniem do modelu; treść dokumentów
traktowana jako niezaufana (test prompt injection); licencje bez GPL/AGPL ([LICENSES-THIRD-PARTY.md](../LICENSES-THIRD-PARTY.md)).

## 9. Ograniczenia i następne kroki (½ strony)

- dokumenty z platform zakupowych wymagają uploadu lub URL;
- małe n dla rzadkich podsektorów (pokazujemy to jawnie);
- pilotaż: wyciąg z CST2021 (NIP beneficjenta, daty) dla jednego programu i miesiąc pracy w jednej instytucji
  zarządzającej.
