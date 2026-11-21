# 04. Architektura MVP i sposób mierzenia jakości

Stan na 2026-11-16. Liczby z danych BZP policzyłem sam (dowód: `data-samples/`, `references/test-run.md` w skillach). Liczby z literatury mają źródła w `zalaczniki/notatki_metody.md` i `zrodla.md`.

## Odpowiedź w skrócie

MVP to trzy warstwy na jednej tabeli umów: (1) klasa referencyjna z rzeczywistych wyników zakończonych umów, (2) sygnały ryzyka z dowodem, (3) wyjaśnienie przyczyn z tekstów zmian umów. Model uczenia maszynowego jest dodatkiem, nie rdzeniem: na próbce 500 prawdziwych umów gradient boosting osiąga AUC 0,71 (walidacja krzyżowa 0,66 ± 0,04), a sama tabela referencyjna 0,63. Jakość mierzymy na prawdziwych etykietach z BZP, więc każdą liczbę w demo da się odtworzyć.

## Architektura MVP (22 h, 2 osoby)

| Warstwa | Co robi | Technologia | Stan w pakiecie |
|---|---|---|---|
| Dane | Pobranie ogłoszeń BZP, parsowanie do tabeli umów, łączenie z ogłoszeniem o wyniku | Python, biblioteka standardowa, pandas | Parser uruchomiony na 4 prawdziwych ogłoszeniach (ze skróconym HTML), pobieranie na atrapie API; przeciw żywemu API z Pythona nieuruchomione (`riskminer-dane-i-zrodla`) |
| Klasa referencyjna | Dla wartości, planowanego okresu i finansowania UE: odsetek opóźnień i wzrostów kosztu w podobnych zakończonych umowach; symulacja P50 i P80 terminu i kosztu | numpy | Uruchomione na próbce 500 umów; tabela z 2 318 umów policzona osobnym parserem w przeglądarce (`riskminer-klasa-referencyjna`) |
| Sygnały | Reguły z dowodem i podstawą; wynik opisowy „do przejrzenia / podwyższona uwaga / pilne" | pandas | Uruchomione na próbce 500 umów (`riskminer-czerwone-flagi`) |
| Przyczyny | Klasyfikacja przyczyn zmian umów; ekstrakcja ryzyk z dokumentu z cytatem | reguły + Claude API | Baseline i walidator przetestowane; wywołania modelu nietestowane (brak klucza w tej sesji) |
| Model | Regresja logistyczna i gradient boosting na cechach znanych w dniu umowy | scikit-learn | Uruchomione na próbce 500 umów (`riskminer-ewaluacja`) |
| Interfejs | Lista inwestycji z rankingiem, karta inwestycji, widok portfela | Streamlit (Apache-2.0) | Do zbudowania w sobotę |

Uzasadnienie stacku: Python, bo całe przetwarzanie i model są w pandas i scikit-learn, a Streamlit daje działający interfejs w 2–3 godziny bez osobnego frontendu. TypeScript nie jest potrzebny, dopóki jury nie wymaga aplikacji webowej z prawdziwego zdarzenia. Jeśli druga osoba woli React, backend FastAPI (MIT) wystawia te same funkcje; szacuję to na kilka godzin więcej (ocena własna).

Koszt i opóźnienia: klasa referencyjna i sygnały działają lokalnie w milisekundach. Wywołania modelu językowego: przyczyny zmian mają medianę ok. 100 znaków, więc klasyfikacja 10 tys. tekstów na `claude-haiku-5-5` to rząd pojedynczych dolarów [?: ceny z dokumentacji Anthropic odczytane przez subagenta, sprawdź przed zakupem]. Ekstrakcja z dokumentu 50 stron na `claude-sonnet-5-5`: kilkadziesiąt sekund na dokument.

## Alternatywy

| Wariant | Kiedy | Koszt | Ryzyko |
|---|---|---|---|
| A. Opisany wyżej (klasa referencyjna + sygnały + przyczyny) | Domyślnie | Najniższy | Jury może oczekiwać „więcej AI" |
| B. Model predykcyjny jako rdzeń (gradient boosting na pełnym zbiorze 50 tys.+ umów, wyjaśnienia SHAP) | Gdy kryteria mierzą metrykę albo Partner da zbiór z etykietą | +3–4 h | AUC może zostać w okolicy 0,7; trudniej to obronić jako „przewidywanie" |
| C. Analiza dokumentów jako rdzeń (rejestr ryzyk z cytatami ze studium wykonalności lub SWZ) | Gdy Partner da dokumenty, a nie tabele | Koszt API, +4 h na złoty zbiór | Halucynacje; ocena jakości wymaga ręcznej pracy |
| Model lokalny zamiast API (Bielik 11B v3.0, PLLuM 12B; oba Apache-2.0 [~]) | Gdy dane Partnera nie mogą wyjść poza UE | Plik modelu Bielik Q4_K_M ma 6,7 GB (strona Ollama, załącznik o metodach); wymagania pamięci niesprawdzone | Jakość ekstrakcji niesprawdzona |

## Co jest technicznie ryzykowne i czym to zastąpić

| Ryzyko | Zamiennik |
|---|---|
| API BZP niedostępne z sieci hali (limit 30/min na IP) | Dane pobrane przed wyjazdem; próbka i generator syntetyczny w pakiecie |
| Parser nie radzi sobie z ogłoszeniem (wiele części, nietypowy zapis okresu) | Pola krytyczne mają kompletność 96–100% na 2 318 rekordach; rekordy bez etykiety pomijamy i liczymy ich udział |
| Model przeuczony albo z przeciekiem etykiety | Lista kolumn-przecieków w `baseline.py`; cechy tylko z dnia zawarcia umowy |
| Model językowy zmyśla ryzyka | `validate_extraction.py` odrzuca ryzyko bez cytatu obecnego w dokumencie |
| Dane Partnera w nieznanym formacie | `baseline.py` czyta CSV, XLSX, JSON i Parquet z dowolną etykietą; skill wspólny `hn-dane-od-partnera` |

## Jak mierzymy jakość

Etykiety (wszystkie z ogłoszenia o wykonaniu umowy):

| Etykieta | Definicja | Częstość (2 318 umów) | Podstawa |
|---|---|---|---|
| Opóźnienie | pole 5.3 = „Nie" | 25,4% | deklaracja zamawiającego |
| Wzrost kosztu | wypłata (5.5) > 101% wartości umowy (4.4) | 26,4% | różnica kwot |
| Istotny wzrost kosztu | wypłata ≥ 110% wartości umowy | 11,3% | próg raportu z realizacji zamówienia, art. 446 ust. 1 pkt 1 Pzp [✔] |
| Niewykonanie | pole 5.1 = „Nie" | 1,0% | deklaracja |

Wyniki bazowe na próbce 500 umów (`riskminer-ewaluacja/references/test-run.md`):

| Metoda | AUC | Uwagi |
|---|---|---|
| Stała (odsetek bazowy) | 0,50 | punkt odniesienia |
| Tabela referencyjna (wartość × okres × UE) | 0,63 | liczona na danych, z których pochodzi próbka, więc wynik jest zawyżony |
| Regresja logistyczna | 0,63 | test: 129 umów innych zamawiających niż w treningu |
| Gradient boosting | 0,71 | walidacja krzyżowa na treningu 0,66 ± 0,04; precyzja w górnych 10% rankingu 54% (7 z 13 umów) przy odsetku bazowym 26% |

Najsilniejsze cechy: planowany okres, miesiąc zawarcia umowy, wartość. Klasyczne flagi zamówieniowe nie przewidują opóźnień: umowy z jedną ofertą były opóźnione w 31% (4 z 13), z trybu niekonkurencyjnego w 13% (2 z 15), z ceną poniżej 70% szacunku w 11% (2 z 18), przy 27% ogółem. Liczebności są małe, ale kierunek jest jasny: wskaźniki nadużyć to inna rzecz niż ryzyko realizacyjne. Dla porównania literatura podaje AUC 0,78–0,80 dla przewidywania aneksów na 2,2 mln kontraktów w Kolumbii (Gallego i in., 2021 [~]).

„Wystarczająco dobre do demo": (1) tabela referencyjna zbudowana na co najmniej 20 tys. umów z 12 miesięcy; (2) kalibracja: w grupie z prognozą 40–60% opóźnia się 40–60% umów; (3) precyzja w górnych 10% rankingu co najmniej dwa razy wyższa od odsetka bazowego; (4) klasyfikator przyczyn z F1 powyżej 0,71 na zbiorze kontrolnym (tyle osiąga baseline na słowach kluczowych, 32 teksty); (5) żaden ekran nie pokazuje liczby bez źródła.

Jeśli jury policzy metrykę: najbardziej prawdopodobne są AUC albo F1 dla klasyfikacji „projekt z problemem / bez" albo trafność rankingu (precyzja w górnych k). `baseline.py --data <plik Partnera> --label <kolumna>` daje wszystkie trzy w kilka minut.

## Pułapki metodyczne, które już wystąpiły w tej sesji

1. **Podział po dacie zawarcia umowy jest obciążony przy krótkim oknie publikacji.** W próbce z 12 dni świeżo zawarte umowy to tylko te krótkie i terminowe: odsetek opóźnień spadł z 33% w treningu do 8% w teście. Poprawny układ: kohorta umów zawartych w danym kwartale, obserwowana co najmniej 12–18 miesięcy, albo podział grupowany po zamawiającym.
2. **Etykieta jest deklaracją.** 326 umów oznaczonych jako terminowe zakończyło się ponad 7 dni po dacie wynikającej z planowanego okresu. Możliwe przyczyny: aneks terminu potraktowany jako „pierwotny termin", okres liczony od innej daty niż zawarcie umowy. Dla jury: pokazujemy obie miary (deklarację i różnicę dat).
3. **Przeciek etykiety.** Liczba zmian, wypłata, data wykonania są znane po fakcie. Nie mogą być cechami modelu prognozującego w dniu umowy; mogą być sygnałami w trakcie realizacji.
4. **Zmiana umowy nie oznacza problemu.** 39% umów ma zmianę; część to rozliczenie obmiarowe albo zmiana kierownika budowy. Stąd taksonomia przyczyn.
5. **Monte Carlo z niezależnymi rozkładami zaniża ogon.** Symulacja w pakiecie wiąże opóźnienie z kosztem i jawnie wypisuje, że ogon powyżej P95 jest ekstrapolowany.

## Liczby z literatury do pitchu (źródła w załączniku)

- Średnie przekroczenie kosztów: kolej 44,7%, mosty i tunele 33,8%, drogi 20,4% (Flyvbjerg 2005, 258 projektów) [✔ subagent]. Nasze dane o małych i średnich umowach pokazują inną skalę: mediana 0%, P95 +17%.
- Europejski Trybunał Obrachunkowy, sprawozdanie 10/2020: osiem flagowych projektów transportowych, koszt +47%, średnie opóźnienie 11 lat; aktualizacja 02/2026: +82% i 17 lat [✔ subagent].
- Polska, 2024: średnio 2,84 oferty na postępowanie; jedna oferta w 35% postępowań poniżej progów (UZP) i 56% według Single Market Scoreboard, który liczy inną populację [✔ subagent].
- Arachne: 107 wskaźników w 7 kategoriach, Arachne+ 78; użycie dobrowolne [✔ subagent, strona KE].
