---
name: riskminer-wiedza-domenowa
description: Wiedza domenowa do zadania RISK MINER (Ministerstwo Funduszy i Polityki Regionalnej): słownik pojęć z zamówień publicznych i funduszy UE, aktorzy, podstawy prawne, gdzie szukać liczb i typowe pomyłki. Użyj, gdy zespół pyta „co to jest ogłoszenie o wykonaniu umowy", „czym się różni IZ od IP", „co znaczy art. 455", „jak ministerstwo rozumie ryzyko", „skąd ta liczba" albo gdy trzeba napisać tekst w języku Partnera.
---

# riskminer-wiedza-domenowa

## Cel
Żeby nikt w zespole nie pomylił pojęć przed jury złożonym z ekspertów ministerstwa. Ten skill nie przechowuje faktów: wskazuje, w którym pliku research jest ich jedyna wersja.

## Gdzie co jest (jedna wersja prawdy)
| Pytanie | Plik |
|---|---|
| Kim jest Partner, co go boli, jak mówi | `research/01_partner_i_problem.md` (hipotezy H1–H11, „Słownictwo Partnera") |
| Jakie narzędzia już istnieją (Arachne, SKANER, czerwone flagi) i gdzie jest luka | `research/02_istniejace_rozwiazania.md` |
| Jakie dane, jakie pola, jakie liczby z BZP | `research/03_dane_i_api.md` |
| Metoda, etykiety, zmierzona jakość, liczby z literatury | `research/04_technologia_i_ewaluacja.md` |
| Przepisy, czerwone linie, pytania prawnika | `research/05_prawo_etyka_ryzyka.md` |
| Słownik pojęć | `references/slownik.md` |

## Kroki
1. Gdy pada pojęcie: sprawdź `references/slownik.md`. Jeśli go tam nie ma, poszukaj w plikach research; jeśli nie ma nigdzie, powiedz, że to niesprawdzone, zamiast odpowiadać z pamięci.
2. Gdy pada liczba: podaj ją razem z plikiem i mianownikiem (np. „25,4% z 2 318 umów na roboty, ogłoszenia 2–13.11.2026, plik 03"). Liczby z oznaczeniem [~] albo [?] w research cytuj z tym zastrzeżeniem.
3. Gdy piszesz tekst dla jury: użyj słownictwa z pliku 01 (instytucja zarządzająca, beneficjent, wniosek o płatność, analiza ryzyka, próba kontrolna) i zasad języka z pliku 05 (sygnał, nie zarzut).

## Przykład wejście → wyjście
Pytanie: „Czy Arachne jest obowiązkowe?" Odpowiedź: „Według strony Komisji Europejskiej korzystanie z Arachne+ jest dobrowolne; obowiązkowe ma być przekazywanie do niego danych od 2028 r. (plik 02, wiersz Arachne; plik 05, wiersz o rozporządzeniu finansowym; oznaczone [~], numer przepisu do weryfikacji w EUR-Lex)."

## Typowe pomyłki
- **Ogłoszenie o wyniku** (kto wygrał, ile ofert) to nie **ogłoszenie o wykonaniu umowy** (jak umowa się skończyła). Etykiety są w tym drugim.
- **Opóźnienie** w naszych danych to deklaracja zamawiającego o niedotrzymaniu pierwotnego terminu, nie orzeczenie o winie wykonawcy. Prawo rozróżnia opóźnienie i zwłokę.
- **Zmiana umowy** (art. 455 Pzp) jest legalnym, częstym zdarzeniem; nie jest nieprawidłowością.
- **Nieprawidłowość** i **korekta finansowa** to pojęcia z prawa funduszy UE o ściśle określonym znaczeniu. Nasze sygnały nimi nie są.
- **Wartość szacunkowa** jest netto, **cena oferty** i **wartość umowy** brutto.
- **BZP** obejmuje zamówienia krajowe; duże zamówienia są ogłaszane w TED, ale ogłoszenie o wykonaniu umowy trafia do BZP także dla nich.
- **Projekt** (umowa o dofinansowanie z beneficjentem) to nie **zamówienie** ani **umowa z wykonawcą**: jeden projekt ma zwykle kilka umów.
- Minister: w październiku 2026 r. nastąpiła zmiana, a powołanie następczyni nie było potwierdzone w źródłach (plik 01). Nie wymieniaj nazwiska ministra w prezentacji.

## Kiedy nie używać
Do pytań o technikę pobierania danych (`riskminer-dane-i-zrodla`) i o scenariusz prezentacji (`riskminer-demo-i-pitch`).

## Zależności
Brak (sam tekst).
