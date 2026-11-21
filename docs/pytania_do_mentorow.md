# RISK MINER — pytania do mentorów MFiPR

Stan: 2026-11-21. Każde pytanie ma krótki powód („Dlaczego pytamy") i nasze obecne założenie. Jeśli mentor nie zna odpowiedzi, zostajemy przy założeniu.
**Priorytet:** 🔴 pytamy w pierwszej godzinie · 🟠 dziś · 🟢 jeśli zostanie czas.

Zapisuj odpowiedzi w polu „Odpowiedź" razem z imieniem mentora i godziną. Wynik rozmowy wpisz do `docs/status.md`.

---

## A. Test łączenia i zestaw referencyjny

**A1 🔴 Jakie poziomy powiązań obejmuje zestaw referencyjny?**
Na przykład: projekt → postępowanie (OCID), ogłoszenie o zamówieniu, ogłoszenie o wyniku, ogłoszenia o zmianie umowy, ogłoszenie o wykonaniu, umowa, wykonawca (NIP), ogłoszenie TED, rekord BK2021.
- Dlaczego pytamy: tak ustawimy kolumny eksportu `links.csv`, żeby dało się go łatwo porównać z Waszym zestawem.
- Nasze założenie: jeden wiersz to jedno powiązanie (projekt, poziom, identyfikator docelowy, metoda, pewność, status).
- Odpowiedź:

**A2 🔴 W jakim formacie porównujecie identyfikatory?**
Numer ogłoszenia z wersją (`2022/BZP 00058537/01`) czy bez niej (`2022/BZP 00058537`)? OCID (`ocds-148610-…`)? `objectId`? Numer TED w formacie `NNNNN-RRRR`?
- Dlaczego pytamy: chcemy uniknąć „błędnych" trafień, które wynikają tylko z formatu zapisu.
- Nasze założenie: eksportujemy wszystkie formy.
- Odpowiedź:

**A3 🔴 Czy test łączenia obejmuje 7 projektów, które mają tylko numer KPO (bez numeru BZP)?**
Czy oczekujecie, że system sam znajdzie ich postępowania w BZP?
- Dlaczego pytamy: dla tych projektów robimy dopasowanie przybliżone po NIP, tytule, CPV, dacie i wartości. Taki wynik dostaje status „do weryfikacji".
- Nasze założenie: tak, są w teście, a wynik niepewny ma trafić do eksperta.
- Odpowiedź:

**A4 🟠 Jak liczycie „poprawne", „niepewne" i „błędne" połączenie?**
Czy dopasowanie, które system oznaczył jako niepewne i oddał ekspertowi, liczy się na plus, czy jako brak?
- Odpowiedź:

**A5 🟠 Czy do projektu należą też postępowania unieważnione albo powtórzone?**
Chodzi o postępowania na ten sam przedmiot, które poprzedziły właściwą umowę.
- Nasze założenie: tak, jako powiązane postępowania (sygnał ryzyka R11/R13).
- Odpowiedź:

**A6 🟠 Projekty „część 1" (Biecz) i „część 2" (Zakrzew).**
Czy rekord ma się wiązać wyłącznie z umową dla tej części? Czy ogłoszenie o wyniku, które obejmuje wszystkie części, też liczy się jako powiązanie?
- Nasze założenie: wiążemy ogłoszenie o zamówieniu i ogłoszenie o wyniku całego postępowania oraz umowę i ogłoszenie o wykonaniu tylko danej części.
- Odpowiedź:

---

## B. Dane od Organizatora: błędy i braki

**B1 🔴 Czy wolno mówić, jakie typy błędów są w pliku?**
Bez wskazywania konkretnych rekordów. Na przykład: zły numer ogłoszenia, nieaktualny status, zła część, zły NIP.
- Dlaczego pytamy: już znaleźliśmy, że numer ogłoszenia **2023/BZP 00110672/01 (RM-2026-022, Wolin) nie występuje w BZP**. Postępowanie o tym samym tytule odnajdujemy przez ogłoszenia o zmianie i o wykonaniu umowy. Chcemy wiedzieć, czy dobrze rozumiemy, co jest testowane.
- Odpowiedź:

**B2 🟠 Pole „Status przedsięwzięcia = Zakończone" — według jakiego źródła?**
Czy jest pewne? Kilka postępowań jest z 2026 r. (np. Biecz, Bobrowniki).
- Nasze założenie: status sprawdzamy w ogłoszeniu o wykonaniu umowy. Rozbieżność pokazujemy jako „sprzeczność".
- Odpowiedź:

**B3 🟠 W jakiej podstawie VAT są kwoty w adnotacji KPO („Wartość przedsięwzięcia", „dofinansowanie")?**
Netto, brutto czy koszty kwalifikowalne?
- Dlaczego pytamy: zgodnie z poradami porównujemy tylko kwoty tego samego rodzaju. Dziś oznaczamy je jako „podstawa nieznana".
- Odpowiedź:

**B4 🟠 Czy numer KPO ma stałą budowę?**
Chodzi o numer `KPOD.03.15-IW.nn-xxxx/rr`. We wszystkich 7 rekordach `IW.nn` = 12 + kod TERYT województwa / 2 (np. dolnośląskie 02 → IW.13). Czy to jest reguła (WFOŚiGW danego województwa jako instytucja wdrażająca)? Co oznacza końcówka `/24`, `/25`: rok umowy, naboru, czy coś innego?
- Dlaczego pytamy: chcemy dodać walidację numerów i lepsze okno dat przy dopasowaniu.
- Odpowiedź:

**B5 🟠 Czy numer KPO pojawia się w ogłoszeniach BZP?**
Na przykład w polu „nazwa projektu lub programu" (3.3/3.4) ogłoszenia o wykonaniu umowy.
- Dlaczego pytamy: to byłby dokładny klucz łączenia zamiast dopasowania przybliżonego.
- Odpowiedź:

**B6 🟠 Czy dostaniemy dane z CST2021 (numery projektów) dla któregoś z 22 projektów?**
Treść zadania wspomina CST2021, ale w pliku są tylko numery KPO i BZP.
- Odpowiedź:

**B7 🟠 Czy dojdą dodatkowe pliki z danymi lub dokumentami?**
Treść zadania mówi o „pełnym pakiecie wiedzy eksperckiej… oraz FAQ". Dostaliśmy 2 pliki docx i xlsx. Gdzie jest FAQ? Czy będzie aktualizacja pakietu w trakcie wydarzenia?
- Odpowiedź:

**B8 🟢 Kolumna „Wersja rekordu = 2.0".**
Czy była wersja 1.0 i czy ma znaczenie dla oceny?
- Odpowiedź:

---

## C. Źródła publiczne i test integracji

**C1 🔴 Czy w teście integracji możemy pobierać dane z kopii `bzp.cytr.us`?**
Czy jury oczekuje zapytań do `ezamowienia.gov.pl`?
- Dlaczego pytamy: adres API mamy w konfiguracji i obsługujemy oba. Linki-dowody prowadzą zawsze do trwałych stron ezamowienia.gov.pl, bo kopia działa tylko na czas wydarzenia.
- Odpowiedź:

**C2 🟠 Co dokładnie zawiera paczka `risk_miner_bzp_kopia.zip`?**
Pytamy o zakres dat, typy ogłoszeń i kryterium doboru (tylko wod-kan, czy wszystkie roboty zamawiających wod-kan). Do jakiej daty jest aktualna?
- Dlaczego pytamy: na jej podstawie budujemy bazę porównawczą (tysiące postępowań). Musimy podać liczebność próby i okres.
- Nasze obserwacje: w kopii są też ogłoszenia spoza wod-kan (drogi, budynki); ostatnie z ok. 12.11.2026.
- Odpowiedź:

**C3 🟠 Jakie źródło dodatkowe (poza BZP) najbardziej Was interesuje?**
Możliwości: TED, BK2021, KPOŚK/AKPOŚK, BIP, NIK, KIO.
- Nasze założenie: Biała lista VAT (weryfikacja NIP i REGON z danymi podmiotu), raporty NIK o wod-kan (lekcje), TED (zwykle wynik „brak" dla zamówień krajowych), a jeśli zdążymy, to KIO i BK2021.
- Odpowiedź:

**C4 🟠 Czy możecie wskazać konkretne raporty NIK i orzeczenia KIO dla sektora wod-kan?**
Najlepiej takie, które uważacie za wzorcowe.
- Odpowiedź:

**C5 🟠 BK2021: czy znacie publiczne API, czy integrujemy się ze stroną?**
Czy któryś z 22 projektów ma postępowania w Bazie Konkurencyjności?
- Odpowiedź:

**C6 🟠 KPOŚK/AKPOŚK: która wersja i z jakiego źródła?**
Czy powiązanie projektu z aglomeracją (RLM, czy projekt leży w aglomeracji) jest dla Was ważne? Projekty KPO B3.1.1 są „poza aglomeracjami".
- Odpowiedź:

**C7 🔴 Dokumenty postępowań (SWZ, PFU, PPU, odpowiedzi na pytania) leżą na platformach zakupowych.**
platformazakupowa.pl blokuje automatyczny dostęp (wymaga logowania). Czy możemy wgrać dokumenty pobrane ręcznie z publicznych stron postępowań, z zachowaniem źródła? Czy dostarczycie dokumenty dla części projektów?
- Dlaczego pytamy: treść zadania wyklucza „manualny import i powiązanie". Chcemy mieć pewność, że wgranie pliku (dalej przetwarzanego automatycznie) jest w porządku.
- Odpowiedź:

**C8 🟢 Czy możemy używać wyszukiwarki internetowej do znajdowania dokumentów?**
Na przykład BIP i komunikatów gmin, przez API wyszukiwarki, z oznaczeniem pewności.
- Odpowiedź:

**C9 🟢 Czy pole 5.2 ogłoszenia o wykonaniu umowy to faktyczna data wykonania?**
Pole „Termin wykonania umowy". Używamy go do liczenia opóźnienia w dniach.
- Odpowiedź:

---

## D. Analiza nowej inwestycji (25%)

**D1 🔴 W jakiej formie dostaniemy „przykładową nową inwestycję" do testu?**
Opis tekstowy, PDF czy DOCX? Jaki podsektor (np. sieć wodociągowa, jak w poradniku)? Czy możemy dostać przykład już teraz albo wzór, jak będzie wyglądał?
- Dlaczego pytamy: przygotujemy pod to testy i dane demo.
- Odpowiedź:

**D2 🔴 Grupa porównawcza: wszystkie zakończone postępowania wod-kan z BZP czy 22 projekty pilotażowe?**
Przy 22 projektach próba jest za mała na przedziały.
- Nasze założenie: obie. 22 projekty to „przypadki szczegółowe", a tysiące postępowań z BZP to „baza porównawcza". Zawsze podajemy n i okres.
- Odpowiedź:

**D3 🟠 Co rozumiecie przez „ocenę kosztorysu i harmonogramu"?**
Proponujemy: pozycję budżetu i czasu trwania (percentyl) na tle podobnych umów; koszt na km sieci lub na RLM; stosunek wygrywającej oferty do szacunku; odsetek unieważnień z powodu ceny powyżej budżetu (art. 255 pkt 3). Czego brakuje? Czy budżet w opisie podaje się zwykle netto czy brutto?
- Odpowiedź:

**D4 🟠 Propozycje zapisów umownych: jakiego poziomu szczegółu oczekujecie?**
Gotowa treść klauzuli, czy wskazanie typu zapisu z podstawą (np. zmiany przewidziane w dokumentach zamówienia, art. 455 ust. 1 pkt 1; waloryzacja, art. 439)? Czy macie wzorcowe klauzule, które możemy wpisać jako wiedzę ekspercką?
- Odpowiedź:

**D5 🟠 Skuteczność działań zaradczych: jak ją mierzyć na danych publicznych?**
Proponujemy reguły: czy umowę wykonano w zmienionym terminie; czy przedłużano wielokrotnie; czy wykonano należycie (5.6); czy wypłata nie przekroczyła wartości umowy powiększonej o zmiany. Czy to akceptowalne?
- Odpowiedź:

**D6 🟠 Checklista z poradnika istnieje tylko dla sieci wodociągowej (9 punktów).**
Czy macie listy dla kanalizacji, oczyszczalni, SUW i deszczówki? Jeśli nie, czy możemy przygotować projekty list, oznaczone jako „do zatwierdzenia przez eksperta"?
- Odpowiedź:

**D7 🟢 Jaki horyzont czasu ma mieć prognoza?**
Czas od ogłoszenia do zakończenia, czy od podpisania umowy do odbioru? Czy liczyć też czas postępowania przetargowego?
- Odpowiedź:

---

## E. Katalog ryzyk i ekstrakcja zdarzeń

**E1 🟠 Czy katalog R01–R15 i tabela „zdarzenie → źródło" to cały katalog ekspercki?**
Czy dostaniemy szczegółowe definicje, sygnały i środki zaradcze dla każdego R?
- Odpowiedź:

**E2 🟠 Czy jedno zdarzenie może mieć kilka kodów R?**
Przykład: „kolizja z niezinwentaryzowaną siecią" to R02 i R03. Czy mamy wskazać kod główny?
- Nasze założenie: kod główny i kody dodatkowe.
- Odpowiedź:

**E3 🟠 Przykładowe mapowanie, chcemy sprawdzić, czy myślimy jak Wy.**
Nowogard (RM-2026-020), dwie zmiany z art. 455 ust. 1 pkt 4:
- „konieczność ustanowienia służebności przesyłu na działce nr 3/39" → R03, termin +1 mies.;
- „ujawniono niekorzystne warunki gruntowe… wysoki poziom wód gruntowych" → R02, termin +1 mies.

Czy to poprawne?
- Odpowiedź:

**E4 🟢 Nowe kategorie ryzyk proponowane przez system: kto je zatwierdza i jak szczegółowe mają być?**
Czy wystarczy nazwa, definicja i 2–3 przykłady z cytatami?
- Odpowiedź:

**E5 🟢 Czy ogłoszenia BZP liczą się jako „dokumenty" w kryterium jakości analizy dokumentów?**
Czy też oczekujecie analizy SWZ, PFU i umów?
- Odpowiedź:

---

## F. Panel eksperta i praca jury

**F1 🔴 Ilu jurorów będzie testować aplikację jednocześnie? Czy potrzebne są konta?**
- Nasze założenie: konta demo z rolami (ekspert, analityk, admin). Każdy juror dostaje kopię bazy z przyciskiem „Przywróć stan demo", żeby testy się nie mieszały.
- Odpowiedź:

**F2 🟠 Czy dopasowania pewne (zgodny numer, OCID i NIP) też wymagają zatwierdzenia przez eksperta?**
- Nasze założenie: wszystko zaczyna jako „propozycja", a pewne dopasowania zatwierdza się zbiorczo jednym kliknięciem.
- Odpowiedź:

**F3 🟢 Czy ważne jest śledzenie, który ekspert zatwierdził zmianę?**
Imiennie i z historią wersji. Czy wystarczy rola?
- Odpowiedź:

**F4 🟢 Oznaczanie materiałów jako „wzorcowe": czego dotyczy?**
Dokumentów, zdarzeń, całych projektów, klauzul? Jak ma wpływać na dalsze analizy?
- Nasze założenie: wzorcowe elementy stają się przykładami dla modelu i mają większą wagę w podobieństwie.
- Odpowiedź:

---

## G. Model językowy, dane i bezpieczeństwo

**G1 🔴 Czy można przetwarzać dane publiczne modelem w chmurze poza UE?**
Na przykład API Anthropic, OpenAI, Gemini.
- Dlaczego pytamy: musimy opisać, gdzie przetwarzane są dane. Mamy też opcje: model lokalny (Ollama, PLLuM/Bielik), Gemini/Vertex w regionie UE i tryb bez modelu (same reguły). Wszystko przełączamy w konfiguracji, bez zmian w kodzie.
- Odpowiedź:

**G2 🟠 Czy jury będzie testować z własnym kluczem API?**
Czy mamy zapewnić działający klucz na serwerze demo?
- Odpowiedź:

**G3 🟠 Dane osobowe: jak traktować wykonawców, którzy są osobami fizycznymi (JDG)?**
Ich imię i nazwisko jest w nazwie firmy.
- Nasze założenie: w interfejsie maskujemy je domyślnie, a z Białej listy nie zapisujemy rachunków ani reprezentantów.
- Odpowiedź:

**G4 🟢 Czy macie preferencje co do miejsca hostingu?**
Na przykład serwer w UE albo w Polsce. Czy dopuszczacie prototyp uruchamiany lokalnie, jeśli hosting zawiedzie?
- Odpowiedź:

---

## H. Formalności, prawa i zgłoszenie

**H1 🔴 Materiały przygotowane przed wydarzeniem.**
To skrypty pobierania i parsowania BZP, research, skille. Czy wystarczy je ujawnić w README i w opisie?
- Odpowiedź:

**H2 🟠 Czy możemy umieścić w publicznym repozytorium dwa pliki docx z wiedzą ekspercką i plik xlsx?**
Czy tylko dane pochodne (YAML z katalogiem) z podaniem źródła?
- Odpowiedź:

**H3 🟠 Jaką licencję kodu preferujecie?**
Z uwagi na przeniesienie praw (§4 regulaminu). Planujemy Apache-2.0 i wyłącznie zależności na licencjach permisywnych (bez GPL i AGPL).
- Odpowiedź:

**H4 🟠 Gdzie składamy materiały?**
Opis (≤10 stron), PDF (≤10 slajdów), film (≤3 min), raport z testu, eksport, dokumentacja. Wszystko w HackTribe, czy coś osobno? Film: wystarczy link (YouTube, niepubliczny)?
- Odpowiedź:

**H5 🟢 Czas i forma finału.**
Ile minut trwa pitch? Czy demo ma być na żywo na Waszych danych?
- Odpowiedź:

---

## Ściąga: pierwsza runda (5 minut przy stoisku)
1. A1 i A3: zestaw referencyjny i projekty KPO.
2. C1: kopia BZP w teście integracji.
3. C7: dokumenty z platform zakupowych.
4. D1: forma przykładowej nowej inwestycji.
5. G1: przetwarzanie danych poza UE.
6. F1: liczba jurorów i konta.
7. H1: ujawnienie materiałów przygotowanych wcześniej.
