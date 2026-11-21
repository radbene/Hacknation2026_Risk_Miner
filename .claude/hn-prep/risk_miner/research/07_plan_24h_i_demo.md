# 07. Plan na 24 godziny i demo

Zespół: 2 osoby, obie piszą kod (założenie z kontekstu). Osoba D prowadzi dane i model, osoba I prowadzi interfejs, demo i zgłoszenie. Godziny według harmonogramu z hacknation.pl (odczyt 2026-11-16): sobota 11:00 publikacja treści, niedziela 11:00 koniec kodowania, 14:45 finaliści, 15:15 pitche. Termin wyboru zadania w HackTribe (20:00) pochodzi z kontekstu promptu; strona główna go nie podaje, więc potwierdź go w przewodniku uczestnika.

## Harmonogram

| Godzina | Osoba D | Osoba I | Punkt kontrolny |
|---|---|---|---|
| Sob. 11:00–12:00 | Czyta pełną treść i kryteria; uruchamia `hn-godzina-zero` (skill z pakietu wspólnego; jeśli go nie ma, tabela decyzji z pliku 06); jeśli są dane Partnera: `baseline.py` na nich | Czyta regulamin zadania (prawa autorskie, platforma zgłoszeń); pyta mentora Partnera o dane (pytania z pliku 03) | 12:00: wybrany wariant z pliku 06 albo decyzja „nie bierzemy" |
| 12:00–14:00 | Kontrola zbioru i tabeli referencyjnej zbudowanych przed wyjazdem (jeśli ich nie ma: praca na próbce 500 umów i jawna informacja o tym w demo); dopasowanie do danych Partnera | Szkielet Streamlit: formularz inwestycji, karta wyniku na danych z próbki | 14:00: tabela referencyjna gotowa (pełna albo z próbki); pierwszy ekran działa |
| 14:00–17:00 | Sygnały (`flags.py`) i sygnały w trakcie realizacji; klasyfikacja przyczyn na całym zbiorze | Karta inwestycji: rozkład wyników, P50 i P80, przyczyny z przykładami, linki do ogłoszeń | 17:00: pełna ścieżka dla jednej inwestycji od wpisania do wyniku |
| 17:00–19:00 | Pomiar jakości: kalibracja, precyzja w górnych 10%; zapis do `metrics.json` | Widok portfela: ranking umów UE w toku z sygnałami | 19:00: decyzja ostateczna o zadaniu; rejestracja projektu w HackTribe przed 20:00 |
| 19:00–23:00 | Model (gradient boosting) jako dodatkowa kolumna rankingu; klasyfikacja przyczyn modelem językowym, porównanie z baseline | Ekran „Skąd te liczby": źródła, definicje etykiet, ograniczenia; czerwone linie z pliku 05 | 23:00: zamrożenie zakresu; lista rzeczy, których nie robimy |
| 23:00–03:00 | Jeden przypadek retrospektywny: prawdziwa opóźniona inwestycja, co było widać wcześniej | Scenariusz demo, dane demo zapisane lokalnie, tryb bez sieci | 03:00: próba demo od początku do końca na czystym laptopie |
| 03:00–07:00 | Sen na zmianę (po 2 h); poprawki błędów z próby | Sen na zmianę; README dla jury | 07:00: nagranie wideo do 2 minut |
| 07:00–10:00 | Repozytorium: instrukcja uruchomienia, licencje zależności, lista materiałów przygotowanych wcześniej | Prezentacja (5 slajdów), opis w HackTribe, linki | 10:00: zgłoszenie wysłane; 10:00–11:00 rezerwa |
| Niedz. 11:00–15:15 | Sen; jeśli finał: próba pitchu z pytaniami z tej strony | Sen; próba pitchu | 14:45: lista finalistów |

## Definicja „done" dla MVP

1. Użytkownik wpisuje wartość, planowany okres, typ robót i źródło finansowania i w ciągu sekundy widzi: odsetek opóźnień i wzrostów kosztu w podobnych umowach z liczebnością klasy, P50 i P80 terminu i kosztu, pięć najczęstszych przyczyn zmian z przykładami.
2. Każda liczba ma odesłanie do źródła (liczba umów, okres, link do przykładowych ogłoszeń).
3. Jest drugi ekran z rankingiem co najmniej 100 prawdziwych umów w toku z sygnałami.
4. Ekran „Skąd te liczby" pokazuje zmierzoną jakość i ograniczenia.
5. Aplikacja działa bez sieci na danych zapisanych lokalnie.
6. Repozytorium uruchamia się jedną komendą według README.

## Demo wideo (do 2 minut)

| Czas | Obraz | Narracja |
|---|---|---|
| 0:00–0:15 | Jedna liczba na ekranie: „1 na 4" | „Co czwarta umowa na roboty budowlane w Polsce kończy się po terminie. Przy umowach za 5–20 mln zł ponad połowa. To wiadomo z publicznych ogłoszeń, tylko nikt tego planującym nie pokazuje." |
| 0:15–0:50 | Kreator: gmina, droga, 3,2 mln zł, 9 miesięcy, projekt UE | „Wpisujemy planowaną inwestycję. W 97 podobnych zakończonych umowach opóźnienie zadeklarowano w 46% przypadków. W 80% symulacji koniec wypada do trzech miesięcy po terminie z harmonogramu; rezerwa kosztu na P80 to blisko 10%." |
| 0:50–1:20 | Lista przyczyn z przykładami i linkami do ogłoszeń | „Dlaczego? Roboty dodatkowe, kolizje z sieciami, pozwolenia, pogoda. Każda przyczyna prowadzi do prawdziwych ogłoszeń i ma propozycję działania przed startem." |
| 1:20–1:45 | Widok portfela: umowy UE w toku, sygnały | „Dla instytucji zarządzającej: umowy w toku, w których minął termin albo pojawiło się ogłoszenie o zmianie. To lista do przejrzenia, nie lista winnych." |
| 1:45–2:00 | Ekran „Skąd te liczby" | „Dane: Biuletyn Zamówień Publicznych, ponad 20 tysięcy umów. Jakość zmierzona i pokazana. Wdrożenie nie wymaga integracji z żadnym systemem." |

Liczby w narracji pochodzą z tabeli referencyjnej z tej sesji (2 318 umów). Po przebudowaniu tabeli na pełnym zbiorze trzeba je podmienić na aktualne.

Realne w demo: dane, tabela referencyjna, symulacja, sygnały, przyczyny, linki. Zmockowane, jeśli zabraknie czasu: widok portfela na próbce zamiast pełnego zbioru (oznaczyć), ekstrakcja z dokumentu jako jeden przygotowany przykład. Plan awaryjny na żywo: aplikacja lokalna bez sieci; gdy laptop zawiedzie, nagranie wideo i trzy zrzuty ekranu w prezentacji.

## Demo na żywo w finale (założenie: 3–5 minut)

1. Minuta: problem liczbami z polskich danych i jedno zdanie o Partnerze (ryzyka rozpoznawane po fakcie, plik 01).
2. Dwie minuty: kreator na inwestycji zaproponowanej przez jury („proszę podać wartość i okres").
3. Minuta: portfel i ekran jakości.
4. Ostatnie 30 sekund: co potrzeba do pilotażu (wyciąg z CST2021 z NIP beneficjenta) i co dostanie Partner po miesiącu.

Relacja z 2025 r. mówi, że jury prosiło o demo na żywo zamiast slajdów (plik 02), więc slajdów jest najwyżej pięć.

## Dziesięć najtrudniejszych pytań jury

1. **Skąd pewność, że pole „w terminie" jest prawdziwe?** Nie ma pewności: to deklaracja zamawiającego. Dlatego pokazujemy drugą miarę z dat i wiemy, że w około 20% umów oznaczonych jako terminowe data wykonania jest ponad tydzień po planowanej (326 z około 1 665 umów terminowych z kompletem dat).
2. **To małe umowy. Co z dużymi projektami?** Odpowiedź z pliku 06: liczba projektów UE w samorządach, obowiązek ogłoszeń także powyżej progów, osobna klasa dla megaprojektów z raportów NIK i Trybunału, ta sama metoda na danych CST2021.
3. **Czym to się różni od Arachne?** Arachne ocenia ryzyko nadużyć i konfliktu interesów na danych instytucji. My pokazujemy ryzyko realizacyjne (termin, koszt) na danych publicznych. Sprawdziliśmy, że klasyczne flagi nadużyć nie przewidują opóźnień (plik 04).
4. **Jaka jest trafność?** AUC 0,71 dla modelu i 0,63 dla samej tabeli na próbce 500 umów; precyzja w górnych 10% dwa razy wyższa od odsetka bazowego. Po przebudowie na pełnym zbiorze podajemy nowe liczby z ekranu jakości.
5. **Czy to nie stygmatyzuje wykonawców i gmin?** Jednostką jest umowa, wynik to „sygnał do przejrzenia" z dowodem, nie ma automatycznych skutków, a dane osób fizycznych są ograniczone (plik 05).
6. **Jak połączycie to z projektami unijnymi?** Ogłoszenie ma pole „projekt UE" i nazwę projektu; numer projektu w rozpoznawalnym formacie jest w 16,5% takich ogłoszeń, reszta wymaga dopasowania po nazwie beneficjenta i tytule. Z NIP beneficjenta z CST2021 łączenie jest proste.
7. **Co z danymi wysyłanymi do modelu językowego?** W demo tylko publiczne ogłoszenia. Dla dokumentów wrażliwych wariant z modelem lokalnym; rdzeń (tabela, sygnały) w ogóle nie używa modelu językowego.
8. **Ile kosztuje utrzymanie?** Pobranie nowych ogłoszeń raz dziennie (kilka zapytań), przeliczenie tabeli w minutę, bez licencji i bez integracji. Koszt modelu językowego tylko przy klasyfikacji przyczyn.
9. **Co przygotowaliście przed hackathonem?** Skrypty pobierania i parsowania, tabelę referencyjną z próbki, research. Lista jest w README i w zgłoszeniu; interfejs i analizy na pełnym zbiorze powstały na miejscu.
10. **Dlaczego urzędnik miałby temu zaufać?** Bo każda liczba ma mianownik i link do ogłoszeń, a narzędzie mówi też, czego nie wie: liczebność klasy, przedział, ograniczenia etykiety.
