# 01. Partner i problem: MFiPR / RISK MINER

Stan na 2026-11-16. Legenda: [✔] sprawdzone w źródle pierwotnym, które otworzyłem; [~] źródło wtórne (media, kopia dokumentu) lub niepełne; [?] hipoteza lub pamięć. Pełna lista źródeł: `zrodla.md` (sekcja B).

## Odpowiedź w skrócie

Partnerem jest Ministerstwo Funduszy i Polityki Regionalnej (MFiPR), czyli resort koordynujący fundusze UE (FEnIKS, programy regionalne 2021–2027, KPO) i politykę rozwoju. Na stronie [hacknation.pl](https://hacknation.pl/) zadanie RISK MINER ma pulę 25 000 i dotyczy wczesnego wykrywania ryzyk w inwestycjach publicznych [✔]. Pełna treść i kryteria nie są jeszcze znane (21.11, 11:00); nie znalazłem żadnej publicznej wypowiedzi MFiPR o tym zadaniu.

Najlepiej udokumentowany problem jest **spóźnione wykrywanie ryzyka realizacyjnego** (opóźnienia, droższe projekty, utrata środków), a nie brak kolejnego wskaźnika nadużyć. Ten nurt (Arachne, SKANER, kontrole) już istnieje (patrz plik 02). Recenzje NIK z 2026 r. powtarzają ten sam schemat: ryzyka widać dopiero po ich wystąpieniu, dane wejściowe są słabe, terminy dociskają. **Uwaga:** kierownictwo MFiPR jest w zmianie (patrz niżej), więc nie zakładaj nazwiska ministra w prezentacji.

## Hipotezy problemu → dowód → źródło → pewność

| # | Hipoteza | Dowód (parafraza) | Źródło | Pewność |
|---|---|---|---|---|
| H1 | Ryzyka są rozpoznawane po fakcie | NIK (8.06.2026), 8 projektów PKP PLK za 8,49 mld zł: koszty +ok. 500 mln zł (5,8%), opóźnienia do 5 lat; system monitorowania nieskuteczny, ryzyka stwierdzano dopiero po wystąpieniu | [tvn24](https://tvn24.pl/biznes/z-kraju/raport-nik-inwestycje-kolejowe-pkp-plk-z-opoznieniami-koszty-wzrosly-o-500-milionow-zlotych-st9086223) | [~] (raport NIK nieotwarty) |
| H2 | Dane wejściowe są złe i rozproszone | NIK o programie szerokopasmowym (11.08.2026): nieaktualne dane o adresach i infrastrukturze w osobnych systemach; w 16 z 17 projektów zmieniono 12,6% adresów; tylko 61 ze 118 beneficjentów realizowało projekty; środki UE obcięte ok. 60% (4,5 → 1,8 mld zł) | [Polskie Radio](https://www.polskieradio.pl/395/7786/Artykul/3717264,audit-finds-poland’s-broadband-rollout-hampered-by-bad-data-delays) | [~] |
| H3 | Ryzyko leży też w warunkach i reformach, nie tylko w budowie | NIK (11.09.2026): realne ryzyko utraty >4,9 mld euro z FENG, bo nie powstała ustawa o PAN (warunek podstawowy) | [money.pl](https://www.money.pl/gospodarka/te-opoznienia-moga-drogo-kosztowac-groza-utrata-prawie-5-mld-euro-z-ue-7328294349379680a.html) | [~] |
| H4 | KPO: presja terminu 31.08.2026 | NIK (wystąpienie P/26/001 do MFiPR): na 2.03.2026 27 wskaźników zagrożonych (18 w obszarach dotacyjnych); kamienie milowe 132/168, cele 36/105; „istotne ryzyko" utraty części dotacji | [NIK](https://www.nik.gov.pl/plik/id,32216.pdf) | [✔] |
| H5 | Rewizje KPO ujawniają typowe źródła ryzyka | Addendum do V rewizji (III 2026): mroźna zima, odwołania w przetargach (KIO), rosnące ceny usług, zmiany zakresu (np. platforma OZE, mieszkalnictwo 220→134 budynków) | [Addendum](https://www.solidarnosc.org.pl/wp-content/uploads/2026/03/Addendum-do-V-rewizji-Krajowego-Planu-Odbudowy-i-Zwiekszania-Odpornosci.pdf) | [~] (kopia dokumentu na stronie związku) |
| H6 | Tempo polityki spójności zostawia zaległości | NIK P/26/001: kontraktacja FP 2021–27 ok. 58,5%; n+3 za 2025 spełnione w 131,2%, ale plan certyfikacji tylko w 80,8%; rezerwy użyte w 38,3% | [NIK](https://www.nik.gov.pl/plik/id,32216.pdf) | [✔] |
| H7 | Regiony różnie wdrażają | Na koniec 2025 zakontraktowano 56% alokacji programów regionalnych (zakres 44,8–63,7%; kujawsko-pomorskie najwyżej) | [Grant Thornton](https://grantthornton.pl/wp-content/uploads/2026/03/Stan-wdrazania-Programow-Regionalnych-RAPORT-Grant-Thornton-2026.pdf) | [~] (dane doradcy, nie MFiPR) |
| H8 | Wąskie gardła są też po stronie instytucji | NFOŚiGW (NIK): 482 z 631 wniosków FEnIKS (76,4%) oceniono 2–277 dni po terminie | [NIK](https://www.nik.gov.pl/plik/id,32306.pdf) | [✔] |
| H9 | Wykonawcy i ich nadzór to źródło strat | PKP PLK: ponad 2 lata tolerowany nierzetelny wykonawca, 27,7 mln zł kar umownych nienałożonych | [tvn24](https://tvn24.pl/biznes/z-kraju/raport-nik-inwestycje-kolejowe-pkp-plk-z-opoznieniami-koszty-wzrosly-o-500-milionow-zlotych-st9086223) | [~] |
| H10 | MFiPR samo ma kłopot z realizacją inwestycji | Z 11 zadań inwestycyjnych własnych ukończono 1, 10 przeniesiono na 2026 | [NIK](https://www.nik.gov.pl/plik/id,32216.pdf) | [✔] |
| H11 | MFiPR kupuje AI, ale do oceny wniosków, nie ryzyka | Britenet (komunikat firmy z 24.02.2026): moduł AI grupuje podobne wnioski dla spójnej oceny; o ryzyku ani o nazwie systemu nic | [komunikat](https://britenetpro.prowly.com/442678-britenet-implements-ai-at-the-ministry-of-funds-a-revolution-in-the-verification-of-eu-applications) | [~] (źródło komercyjne) |

**Status KPO po 31.08.2026** (pytanie z zadania):
- Termin realizacji reform i inwestycji minął 31.08; ostatnie wnioski o płatność do 30.09.2026; KE ma 2 miesiące na ocenę, państwa miesiąc, płatności do 31.12.2026 [~] ([RMF24](https://www.rmf24.pl/fakty/polska/news-cale-kpo-zostalo-zainwestowane-pelczynska-nalecz-oglasza-suk,nIdn,1019844)).
- Minister mówiła 31.08, że inwestycje są „zrealizowane lub rozpoczęte" i że KE pozytywnie oceniła 7 wniosków (ok. 150 mld zł) [~] ([xyz.pl](https://xyz.pl/?p=243994), [superbiz](https://superbiz.se.pl/wiadomosci/final-kpo-w-polsce-do-kraju-trafi-ostatnie-90-mld-zlotych-aa-FqEP-o82s-A4sK.html)). Sformułowanie „rozpoczęte" kontrastuje z „w całości zainwestowane".
- Przedostatni wniosek (ok. 7,9 mld euro, ok. 33 mld zł) zatwierdzono ([xyz.pl](https://xyz.pl/?p=246619)); wpływ ok. 1.10.2026 [~] ([eurointegration](https://www.eurointegration.com.ua/rus/news/2026/10/1/7246744/)). Ostatni wniosek ok. 12,7 mld euro (ok. 54 mld zł), wpływ oczekiwany na przełomie roku [~].
- Rozbieżności: łączna kwota w zł to 233, ok. 240 lub ok. 270 mld zł zależnie od źródła (kurs); w euro wszędzie 54,7 mld. Liczba umów: 1,2 mln (RMF24, otwarty) vs 775 tys. (tytuł artykułu xyz.pl z wyników wyszukiwarki, nieotwarty, nieznana data) [~].
- **DO WERYFIKACJI:** czy KE obetnie część płatności za niezrealizowane kamienie milowe i co z projektami tylko „rozpoczętymi" (finansowanie krajowe?). Sprawdzić: komunikaty KE o ocenie ostatniego wniosku, gov.pl/web/fundusze-regiony, NIK.

## Kim jest Partner

- **Minister:** Pełczyńska-Nałęcz ogłosiła odejście z rządu 22.10.2026 [✔ relacja [OKO.press](https://oko.press/na-zywo/na-zywo-relacja/pelczynska-nalecz-odchodzi-z-rzadu-oficjalnie-przez-dwukadencyjnosc-faktycznie-przez-nominacje-domanskiego)]. 27.10 Tusk zapowiedział Agnieszkę Bartol (dotąd stałą przedstawicielkę RP przy UE) [✔ [money.pl](https://www.money.pl/polityka/tusk-namascil-ja-na-ministre-funduszy-to-kolosalna-odpowiedzialnosc-7344641878140960a.html), [TVP](https://www.tvp.info/96152037/kto-zastapi-katarzyne-pelczynska-nalecz-sylwetka-agnieszki-bartol-ambasadorka-ue-i-ekspertka)]. Żadne znalezione źródło nie potwierdza formalnego powołania. **DO WERYFIKACJI** (gov.pl/web/fundusze-regiony, Monitor Polski).
- **Struktura:** regulamin organizacyjny z 15.11.2024, zmieniony zarządzeniem z 23.07.2026 (w życie 25.07) o zadania wokół Planu Partnerstwa Krajowego i Regionalnego 2028–2034 (PPKR). Wymienia departamenty: Strategii, Koordynacji KPO, Koordynacji Wdrażania Funduszy UE [✔ [infor.pl](https://www.infor.pl/akt-prawny/U66.2026.205.0000022,zarzadzenie-ministra-funduszy-i-polityki-regionalnej-zmieniajace-zarzadzenie-w-sprawie-ustalenia-regulaminu-organizacyjnego-ministerstwa-funduszy-i-polityki-regionalnej.html)].
- **Nie ustaliłem** nazw departamentów od kontroli, nieprawidłowości, CST2021 i ryzyka nadużyć. Jedyna wskazówka: strona [Mapa Dotacji](https://mapadotacji.gov.pl/projekty/1674627/?lang=en) podaje jako beneficjenta projektu „IT Department" MFiPR [✔]. **DO WERYFIKACJI:** pełny tekst regulaminu w dziennikurzedowy.mfipr.gov.pl.
- **Zakres „inwestycji publicznych":** ustawa o zasadach prowadzenia polityki rozwoju definiuje politykę rozwoju szeroko (art. 2) i realizuje ją strategiami, programami i politykami publicznymi (art. 4), więc nie tylko funduszami UE [✔ [tekst jedn. Dz.U. 2023 poz. 225](https://eli.gov.pl/eli/DU/2023/225/ogl/pol/pdf)]. Opis zadania mówi „inwestycje publiczne", nie „projekty unijne" [✔ hacknation.pl]. Nie znalazłem „Rejestru dużych inwestycji" ani wieloletniego programu koordynowanego przez MFiPR [?]; Strategia rozwoju Polski do 2035 pojawia się w wynikach wyszukiwania, ale nie otworzyłem jej. **DO WERYFIKACJI** w treści zadania.
- **HackNation:** 2026 to druga edycja (21–22.11, 17 wyzwań od 15 partnerów) [✔ [android.com.pl](https://android.com.pl/tech/1102093-druga-edycja-najwiekszego-w-polsce-hackathonu-wdrozeniowego-odbedzie-sie-21-22-listopada-w-bydgoszczy/)]. Na liście zwycięzców 2025 nie ma zadania MFiPR [✔ [chip.pl](https://www.chip.pl/2025/12/hacknation-2025-relacja)], ale to lista zwycięzców, nie partnerów: czy MFiPR miało zadanie w 2025, **DO WERYFIKACJI** (strona gov.pl/web/cyfryzacja zablokowana dla mojego narzędzia).

## Jak Partner rozumie ryzyko projektu

- Wytyczne dot. kontroli programów polityki spójności 2021–2027 (MFiPR/2021-2027/6(1), z 26.10.2022; kopia z serwisu RPO Pomorskie, aktualną wersję sprawdzić) **nie definiują „ryzyka"**; proporcjonalność oznacza objęcie kontrolą projektów najbardziej ryzykownych [✔ [wytyczne](https://rpo.pomorskie.eu/wp-content/uploads/2023/11/Wytyczne-dotyczace-kontroli-w-programach-polityki-spojnosci.pdf)].
- Wymagają pisemnej analizy ryzyka, która określa zakres weryfikacji wniosku o płatność (Rozdz. 5.1 pkt 1); próba kontroli na miejscu ma odzwierciedlać poziom ryzyka (5.2 pkt 6); kontrole krzyżowe poza aplikacją: próba ryzyka plus losowa, co najmniej kwartalnie, min. 5% grupy ryzyka (5.3 pkt 6); Arachne „może być wykorzystywane" (Rozdz. 10 pkt 4) [✔].
- W KPO ryzyko to „wskaźnik zagrożony" (kamień milowy/cel) [✔ NIK P/26/001].
- „Projekt zagrożony / wysokiego ryzyka" w FEnIKS, CUPT, NFOŚiGW: **nie znalazłem definicji**. **DO WERYFIKACJI** w regulaminach naborów i wytycznych monitorowania na gov.pl/web/fundusze-regiony/wytyczne-na-lata-2021-2027 (wynik wyszukiwarki).

## Użytkownicy i decydenci (hipotezy)

- **Użytkownik [?]:** pracownicy instytucji zarządzających i pośredniczących (planowanie kontroli i prób, ocena wniosków o płatność); zespół koordynacji KPO (wskaźniki zagrożone); komórki odpowiedzialne za n+3 i certyfikację. Podstawa: wymogi analizy ryzyka w Wytycznych [✔] i kontekst NIK.
- **Decydent o wdrożeniu [?]:** dyrektor właściwego departamentu MFiPR oraz właściciel systemów informatycznych (CST2021, Mapa Dotacji). Realistyczna ścieżka to pilot na danych publicznych, nie zmiana w CST2021.
- **Odbiorcy pośredni [?]:** kierownictwo (widok portfelowy), kontrole NIK i KE (ślad decyzyjny).
- **Ograniczenie [✔]:** Arachne „wspiera decyzje, nie podejmuje automatycznych" ([KE](https://antifraud-knowledge-centre.ec.europa.eu/useful-tools/what-arachne_en)). Rozwiązanie scoringowe powinno robić to samo: rekomendacja i uzasadnienie, nie wyrok.

## Co Partner uzna za sukces (wnioski, wszystko [?])

1. Wczesne ostrzeżenie na realnym, znanym przypadku (np. PKP PLK, program szerokopasmowy), pokazane retrospektywnie: „sygnał X był widoczny N miesięcy przed problemem".
2. Wyjaśnialność: dla każdej flagi powód, dane źródłowe, proponowane działanie, w języku Wytycznych (analiza ryzyka, próba kontrolna).
3. Wdrażalność: działa na danych publicznych lub eksportach, bez dostępu do CST2021; jasno wskazane dane, które pilot by dodał.
4. Widok portfelowy (ranking, mapa, trend), nie tylko karta pojedynczego projektu.
5. Uczciwość: pokazane fałszywe alarmy i granice (mało etykiet; korelacja nie jest przyczyną).
6. Komplementarność wobec Arachne i SKANER, bez ich dublowania (plik 02).
7. Kryteria jury 2026 nie są opublikowane [✔ hacknation.pl]; tę listę zweryfikować o 11:00.

## Słownictwo Partnera

| Termin | Definicja jednym zdaniem | Źródło / pewność |
|---|---|---|
| IZ / IP | Instytucja zarządzająca programem / pośrednicząca, której IZ przekazała część zadań | Wytyczne kontroli (użycie) [✔ użycie; definicja ?] |
| Beneficjent | Podmiot realizujący projekt i otrzymujący dofinansowanie | Wytyczne [✔ użycie] |
| Wniosek o płatność (WoP) | Dokument beneficjenta rozliczający wydatki; weryfikacja pełna, częściowa lub minimalna zależnie od ryzyka | Wytyczne Rozdz. 5.1 [✔] |
| Nieprawidłowość | Naruszenie prawa lub umowy mogące szkodzić budżetowi UE; art. 2 pkt 31 rozp. 2021/1060 | [?] DO WERYFIKACJI w eur-lex |
| Korekta finansowa | Zmniejszenie dofinansowania z powodu nieprawidłowości | [?] pamięć |
| Kontraktacja | Wartość podpisanych umów jako % alokacji | NIK P/26/001 [✔ użycie] |
| n+3 / dezangażacja | Reguła terminu wydatkowania, po którym niewykorzystane środki przepadają | NIK P/26/001 [✔ użycie; definicja ?] |
| Certyfikacja | Potwierdzanie wydatków do rozliczenia z KE | NIK P/26/001 [✔ użycie] |
| RPK | Roczny plan kontroli, zawiera m.in. opis analizy ryzyka i prób | Wytyczne Zał. 1 [✔] |
| Kamienie milowe i cele (KPO) | Warunki rozliczenia płatności z KE; „wskaźnik zagrożony" to ten, któremu grozi niedotrzymanie | NIK P/26/001 [✔] |
| CST2021 / SL2021 | Centralny system teleinformatyczny / system lokalny 2021–2027 do obsługi projektów | [?] wyniki wyszukiwarki, nieotwarte |
| FEnIKS, FERC, FENG | Programy: infrastruktura i klimat; rozwój cyfrowy; nowoczesna gospodarka | NIK [✔ nazwy] |
| PPKR | Plan Partnerstwa Krajowego i Regionalnego 2028–2034 | [✔ infor.pl] |
| Projekt zagrożony | Termin używany w monitoringu; definicji nie znalazłem | **DO WERYFIKACJI** |
