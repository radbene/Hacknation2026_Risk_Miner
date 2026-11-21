# RISK MINER — pakiet startowy (stan na 2026-11-16)

**Do zrobienia przed wyjazdem, najważniejsze:** na własnym laptopie pobrać dane z BZP i zbudować zbiór (checklista niżej). Skrypt pobierania nie był jeszcze uruchomiony z Pythona przeciw żywemu API, a na hali limit API dzieli się między wszystkie zespoły.

## Karta zadania

| Pole | Treść |
|---|---|
| Partner i pula | Ministerstwo Funduszy i Polityki Regionalnej; 25 000 (waluta niepodana na hacknation.pl) |
| Najbardziej prawdopodobny wariant pełnej treści | Wczesne ostrzeganie o ryzyku opóźnień i wzrostu kosztów w portfelu inwestycji publicznych, z uzasadnieniem dla urzędnika (35%); zaraz za nim narzędzie do planowania inwestycji przed startem (30%) |
| Rekomendowana koncepcja | Klasa referencyjna z rzeczywistych wyników zakończonych umów publicznych: dla planowanej lub trwającej inwestycji pokazujemy częstość opóźnień i wzrostów kosztu w podobnych umowach, sygnały ryzyka z dowodem i najczęstsze przyczyny zmian |
| Dane: co mamy sprawdzone | Publiczne API Biuletynu Zamówień Publicznych, bez klucza: ogłoszenia o wykonaniu umowy z etykietami (termin, zmiany, wypłata). Pobrane i sparsowane 2 318 umów na roboty: 25,4% po terminie, 39% ze zmianą, 26,4% z wyższą wypłatą |
| Dane: czego brakuje | Danych Partnera (CST2021); przetestowanego łączenia umów z projektami UE; TED, KRS i listy projektów FE (tylko dokumentacja); pełnego zbioru z 12 miesięcy (do pobrania przed wyjazdem) |
| Czy jury zmierzy jakość liczbowo | Może. Jeśli Partner da zbiór z etykietą: AUC albo F1 dla klasyfikacji projektów z problemem, ewentualnie trafność rankingu |
| Kompetencje w zespole | Parsowanie ogłoszeń BZP w pandas i wyrażenia regularne; częstości, kalibracja i Monte Carlo (numpy, scikit-learn); jedna osoba, która odróżnia ogłoszenie o wyniku od ogłoszenia o wykonaniu umowy i zna pojęcia IZ, beneficjent, art. 455 Pzp |
| Wykonalność w 22 h | 4/5: tabela referencyjna, prognoza, sygnały i baseline uruchomione na próbce 500 prawdziwych umów; parser na 4 ogłoszeniach; pobieranie z Pythona przeciw żywemu API nieuruchomione; do zbudowania interfejs i pełny zbiór |
| Siła demo | 4/5: jury podaje wartość i okres inwestycji, wynik liczy się na żywo z linkami do ogłoszeń; słabiej, jeśli Partner oczekuje megaprojektów |
| Dopasowanie do Partnera | 3/5: problem „ryzyka rozpoznawane po fakcie" jest udokumentowany przez NIK, ale nie wiemy, czy Partner myśli o umowach samorządów, czy o dużych programach |
| Ryzyko prawne i etyczne (5 = wysokie) | 2/5: dane publiczne, jednostką jest umowa; uwagi wymagają jednoosobowe działalności i język wyników |
| Sygnały „nie bierzemy" | Pełna treść dotyczy ryzyk makro (kursy, ceny, podaż wykonawców) albo wyłącznie megaprojektów bez danych; Partner wymaga pracy na zamkniętej platformie bez łączenia z danymi publicznymi; kryteria punktują głównie model predykcyjny o wysokiej trafności (nasz pomiar: AUC ok. 0,7) |
| Największa niepewność | Czy Partner udostępni dane o projektach i czy da się je połączyć z umowami w BZP (numer projektu w rozpoznawalnym formacie ma tylko 16,5% ogłoszeń o zamówieniach unijnych) |

## TL;DR

- Założenie „w otwartych danych nie ma etykiet opóźnień" okazało się fałszywe. BZP publikuje wynik każdej umowy; API jest otwarte.
- Ryzyko rośnie z wartością i planowanym okresem: od 15% opóźnień poniżej 200 tys. zł (n=576) do 56% dla 5–20 mln zł (n=106). Umowy z projektów UE opóźniają się częściej (35% wobec 24%), ale głównie dlatego, że są większe: od 1 mln zł różnica w terminowości znika.
- Klasyczne czerwone flagi (jedna oferta, wolna ręka, niska cena) nie przewidują opóźnień. To argument odróżniający nas od Arachne.
- Zmierzona siła predykcji jest umiarkowana (AUC 0,71 na teście 129 umów, walidacja krzyżowa 0,66 ± 0,04), więc sprzedajemy częstości bazowe i sygnały, nie „AI przewidzi".
- Limit API to 30 zapytań na minutę na adres IP. Dane trzeba pobrać przed wyjazdem.

## Pierwsza godzina po publikacji pełnej treści (sobota 11:00–12:00)

1. Przeczytaj treść i kryteria; sprawdź sygnały „nie bierzemy". Skill `hn-godzina-zero` należy do pakietu wspólnego `prep/_wspolne/` (osobna sesja `00_wspolne`); jeśli go nie ma, wystarczą kroki 2–5.
2. Ustal, co daje Partner: tabela projektów z etykietą → wariant A i najpierw `baseline.py`; tabela bez etykiety → A z klasą referencyjną; mowa o planowaniu i wnioskach → B; dokumenty → C; treść ogólna → B plus widok portfela. Tabela decyzji: `research/06`.
3. Zadaj mentorowi Partnera 8 pytań o dane z `research/03`.
4. Sprawdź regulamin zadania: prawa autorskie, platforma zgłoszeń, wolno czy nie łączyć danych i używać zewnętrznego API.
5. O 12:00 decyzja: bierzemy i który wariant. Plan dalszych godzin: `research/07`.

## Pięć decyzji dla zespołu

1. Czy RISK MINER jest naszym pierwszym wyborem, skoro pula jest wysoka i konkurencja będzie mocna?
2. Kto do czwartku pobiera pełny zbiór z BZP i buduje tabelę referencyjną (1–2 GB, na czyim laptopie)?
3. Roboty budowlane jako jedyna dziedzina, czy dokładamy dostawy i usługi (osobne tabele, podwójny czas pobierania)?
4. Czy w demo pokazujemy nazwy zamawiających i wykonawców, czy je ukrywamy (plik 05)?
5. Czy klasyfikację przyczyn robimy modelem językowym (koszt, klucz API), czy zostajemy przy regułach z F1 0,71?

## Checklista przed 21.11

- [ ] Test na własnym laptopie: komenda z `.claude/skills/riskminer-dane-i-zrodla/references/test-run.md` (jeden dzień ogłoszeń; oczekiwane 215 rekordów).
- [ ] Pobrać z domu: ogłoszenia o wykonaniu umowy (roboty) z 12 miesięcy, o wyniku z 18 miesięcy, o zmianie umowy z 2026 r. Szacunek przy limicie 30 zapytań na minutę: kilkanaście do kilkudziesięciu minut na typ, razem 1–2 GB (niezmierzone z Pythona).
- [ ] Zbudować `dataset.csv` i nową tabelę referencyjną; przeliczyć liczby w scenariuszu demo.
- [ ] Środowisko: Python 3.10+, pandas, numpy, scikit-learn, streamlit, openpyxl.
- [ ] Klucz API Anthropic z budżetem; sprawdzić aktualne identyfikatory i ceny modeli.
- [ ] Przeczytać regulamin (PDF na hacknation.pl): limit zadań na zespół i termin wyboru zadania w HackTribe.
- [ ] Zapytać organizatorów na Discordzie, czy wolno użyć skryptów przygotowanych wcześniej.
- [ ] Jedna osoba przegląda 32 etykiety w `data-samples/bzp/change_reasons_holdout_32.jsonl`.
- [ ] Opcjonalnie: model lokalny (Bielik 11B v3.0, plik Q4_K_M 6,7 GB według strony Ollama) na wypadek danych, które nie mogą wyjść do API.

## DO WERYFIKACJI

- Termin wyboru zadania (20:00) i limit dwóch zadań: strona główna ich nie podaje, a zapowiedzi prasowe mówią o „dowolnej liczbie zadań". Prasa podaje też „17 wyzwań od 15 partnerów", strona pokazuje 10.
- Kto jest ministrem (zmiana w październiku 2026 r., powołanie niepotwierdzone).
- Status Arachne+: użycie dobrowolne, obowiązek przekazywania danych od 2028 r.; numer przepisu rozporządzenia 2024/2509.
- AI Act: przesunięcie obowiązków dla systemów wysokiego ryzyka na 2.12.2027 (rozporządzenie 2026/1744) i klasyfikacja naszego narzędzia; tekst w EUR-Lex nie był otwarty.
- Licencja ponownego użycia danych BZP; czy od 2027 r. limit strony spadnie do 100 rekordów (źródło wtórne).
- Art. 224 Pzp (próg 30% dla rażąco niskiej ceny) i próg stosowania ustawy (130 tys. zł): z pamięci.
- Ceny i identyfikatory modeli Claude; licencje i regulaminy Bielika i PLLuM.
- Endpointy TED, KRS, Białej listy, lista projektów FE: tylko dokumentacja, bez testu.
- Liczby z literatury oznaczone [~] w `research/04` i w załączniku o metodach.

## Materiały przygotowane przed wydarzeniem (do ujawnienia w zgłoszeniu)

Skrypty: `bzp_fetch.py`, `bzp_parse.py`, `bzp_join.py`, `sample_to_full.py`, `baseline.py`, `synth.py`, `refclass_build.py`, `refclass_forecast.py`, `flags.py`, `classify_reasons.py`, `validate_extraction.py`. Dane: próbka 500 umów, tabela referencyjna z 2 318 umów, 4 przykładowe ogłoszenia, dwa zbiory przyczyn z etykietami. Teksty: research 01–07, skille, prompty. Wszystko powstało z pomocą modelu Claude; pliki są w `prep/risk_miner/`.

## Mapa plików

- `research/01`–`07`: Partner, istniejące rozwiązania, dane, technologia i pomiar, prawo, warianty i rekomendacja, plan i demo; `research/zrodla.md`; `research/zalaczniki/` (szczegółowe notatki o API i metodach).
- `data-samples/`: próbki z opisem pochodzenia.
- `.claude/skills/riskminer-*`: wiedza-domenowa, dane-i-zrodla, ewaluacja, demo-i-pitch, klasa-referencyjna, czerwone-flagi, ekstrakcja-przyczyn. Każdy skill ze skryptami ma `references/test-run.md`.
- `PROGRESS.md`: założenia, korekty wskazówek, status. `.env.example`: nazwy zmiennych.
