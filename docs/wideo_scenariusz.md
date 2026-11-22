# Demo – film (≤ 3:00) i pokaz na żywo dla jury

Zgodne z interfejsem po zmianach z 22.11 (górne menu, role „Analityk” / „Ekspert”, kafelki). Liczby z przykładowej
analizy „Przykład – kanalizacja sanitarna” i projektu Nowogard (RM-2026-020) – w dniu nagrania sprawdź je w aplikacji.

## Przygotowanie

- Aplikacja, worker i Bielik uruchomione; publiczny adres przez `ngrok http 5180` albo serwer z `docs/hosting.md`.
- Przeglądarka 1920×1080, powiększenie 110–125%, tryb incognito (rola „Analityk” na starcie).
- Wcześniej policz jedną analizę z przykładowym opisem (odczyt cech trwa 1–2 min, liczenie ryzyka do 2 min):
  w filmie pokazujemy początek oczekiwania i tniemy w montażu.
- Nagranie ekranu: OBS albo `ffmpeg -f x11grab`; lektor nagrany osobno.
- Sprawdzenie długości: `ffprobe -v error -show_entries format=duration -of csv=p=0 film.mp4` (< 180 s).

## Film – scenariusz (cel 2:55)

| Czas | Ekran (co kliknąć) | Lektor |
|---|---|---|
| 0:00–0:12 | Strona startowa: tytuł RISK MINER, ilustracja, okno „wybierz_role.exe” | „Co piąta umowa wod-kan w BZP ma zmieniany termin. RISK MINER zbiera, co poszło nie tak w zakończonych inwestycjach, i podpowiada, jak tego uniknąć w następnej.” |
| **Ścieżka A – baza doświadczeń** | | |
| 0:12–0:27 | „Baza przypadków” → „Importuj listę projektów (Excel)” (plik organizatora) → „Pobierz aktualne dane z BZP” → postęp zadania | „Startujemy od pliku organizatora z 22 projektami. System sam odpytuje BZP i zapisuje każde zapytanie, więc proces można powtórzyć.” |
| 0:27–0:45 | Karta „Nowogard – Konarzewo” → zakładka „Ogłoszenia BZP tej inwestycji”: lista warunków z ✓ i przyciskami „Źródło” | „Projekt powiązał z postępowaniem i pokazuje dlaczego: nazwa, miejsce, CPV, data i wartość, każdy warunek ze źródłem. Na zbiorze wzorcowym wszystkie 22 projekty są powiązane poprawnie.” |
| 0:45–1:05 | Zakładka „Zdarzenia i przyczyny”: „Zmiana umowy nr 1 – termin”, R03, +37 dni → „Pokaż w źródle” → PDF z podświetlonym pkt 5.3 | „Zmiana terminu o 37 dni: brak służebności przesyłu, kategoria R03. Kliknięcie otwiera oryginalne ogłoszenie z e-Zamówień z podświetlonym fragmentem. Wynik bez źródła nie istnieje.” |
| 1:05–1:22 | „Panel eksperta” → „Do zatwierdzenia”: pozycja → „Zatwierdź” z uzasadnieniem; „Wiedza ekspercka” → „Katalog ryzyk R01–R15” | „Wszystko, co system zbudował sam, jest propozycją. Ekspert zatwierdza, poprawia albo odrzuca, a przeliczenie nie nadpisuje jego decyzji. Katalog ryzyk i wagi zmienia bez programisty.” |
| **Ścieżka B – nowa inwestycja** | | |
| 1:22–1:38 | Wyjdź z panelu → „Nowa analiza” → „Wstaw przykładowy opis” → „Odczytaj cechy” → (cięcie) → cechy i pytanie netto/brutto | „Teraz nowa inwestycja: 6,5 km kanalizacji, 9,8 mln zł, 18 miesięcy. Bielik na naszym serwerze odczytuje cechy, każdą z cytatem.” |
| 1:38–1:46 | „Analizuj ryzyko” → okno „kopalnia_ryzyka.exe” (kilof rozbija skałę) → (cięcie) → wynik | „Liczymy ryzyko na tle 26 tysięcy zakończonych umów.” |
| 1:46–2:08 | „W skrócie” → „Na co uważać”: kafelki flag | „W 9 z 12 najbardziej podobnych umów termin się przesunął, typowo o 75 dni. Harmonogram jest krótszy niż w podobnych, a trasa wymaga praw do nieruchomości. Każda liczba ma liczbę przypadków i przedział.” |
| 2:08–2:22 | „Podobne inwestycje”: otwórz kafelek → zgodność cech → „Pomiń w porównaniu” → przeliczenie | „Widać, dlaczego każda inwestycja jest podobna. Nietrafioną można pominąć, a wynik przeliczy się bez niej.” |
| 2:22–2:37 | „Zalecane działania i zapisy” → „Pobierz kartę (Word)”, „Dane (JSON)”, „Dane (CSV)” | „Dostajemy działania i propozycje zapisów umownych z katalogu ekspertów, a cały wynik eksportujemy do Worda, JSON i CSV.” |
| 2:37–2:48 | „Źródła danych” → „Trwające inwestycje”: alerty o nowych ogłoszeniach | „Dla trwających inwestycji system obserwuje BZP i zgłasza nowe ogłoszenie, które zmienia obraz projektu.” |
| 2:48–2:55 | Ostatni slajd prezentacji (link, repozytorium) | „Dane publiczne, model lokalny, kod na licencji Apache. Link do aplikacji w opisie.” |

## Pokaz na żywo dla jury (ok. 8 min)

Kolejność odpowiada testom z treści zadania (rozdz. 6).

1. **Test integracji** – „Źródła danych” → „Źródła”: uruchom pobieranie z BZP; „Dziennik zapytań”: zapytania z czasem i liczbą wyników. Ponowne uruchomienie niczego nie dubluje.
2. **Test łączenia** – „Źródła danych” → „Trafność dopasowania” (zbiór wzorcowy); karta projektu → „Ogłoszenia BZP tej inwestycji” z warunkami i odrzuconymi kandydatami.
3. **Test kompletności przypadku** – karta Nowogardu: „Przebieg w czasie”, „Umowy i zmiany”, „Mapa powiązań”, „Braki w danych”.
4. **Test źródłowy** – dowolne zdarzenie → „Pokaż w źródle”; komórka z pliku organizatora otwiera arkusz z zaznaczoną komórką.
5. **Test pracy eksperta** – „Panel eksperta” (w wersji demo jednym kliknięciem) → „Do zatwierdzenia”: zatwierdź jedno, odrzuć drugie z uzasadnieniem; na karcie projektu „Wskaż inne postępowanie”; „Historia zmian”.
6. **Test nowej inwestycji** – opis od jury albo dokument PDF/DOCX → cechy → wynik → pominięcie sąsiada → eksport.
7. **Test założeń** – „Modele językowe”: kolejność modeli dla zadań, dodanie własnego modelu bez zmian w kodzie; „Wiedza ekspercka”: nowy sektor to nowe tabele.

Plan awaryjny: bez sieci analiza działa na lokalnej kopii BZP; gdy Bielik nie odpowiada, system przechodzi na reguły i oznacza to w wyniku.
