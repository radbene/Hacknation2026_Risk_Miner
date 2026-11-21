# RISK MINER – notatki metodyczne (HackNation 2026)

Stan na 2026-11-16. Legenda pewności: **[✔]** sprawdzone w źródle pierwotnym, które otworzyłem (uwaga: treść strony przechodziła przez automatyczne streszczanie, więc liczby warto jeszcze raz zerknąć w oryginał przed pitchem); **[~]** źródło wtórne lub tylko abstrakt/streszczenie/metadane; **[?]** z pamięci, niepotwierdzone; **DO WERYFIKACJI** = nie udało się potwierdzić, podano jak sprawdzić.
Tabela źródeł: `../zrodla.md`.

---

## 1. Czerwone flagi w zamówieniach publicznych

### 1.1 Fazekas & Kocsis – Corruption Risk Index (CRI)

| Twierdzenie / liczba | Źródło | Pewność |
|---|---|---|
| Artykuł proponuje dwie obiektywne miary „high-level corruption": single bidding na rynkach konkurencyjnych oraz złożony indeks czerwonych flag w przetargu. Dane: 2,8 mln kontraktów, 28 krajów europejskich, 2009–2014. Korupcja operacjonalizowana jako „nieuzasadnione ograniczenie dostępu do kontraktów w celu sprzyjania wybranemu oferentowi". | Fazekas M., Kocsis G. (2020), *Uncovering High-Level Corruption: Cross-National Objective Corruption Risk Indicators Using Public Procurement Data*, British Journal of Political Science 50(1):155–164, DOI 10.1017/S0007123417000461; https://www.cambridge.org/core/product/8A1742693965AA92BE4D2BA53EADFDF0 ; dane replikacyjne doi:10.7910/DVN/6XYZOD | [~] abstrakt; pełny tekst za paywallem, nie omijałem |
| Wersja robocza (Cambridge repository): https://www.repository.cam.ac.uk/handle/1810/266257 – ta sama treść abstraktu, dane na http://digiwhist.eu/resources/data/ | j.w. | [~] |
| CRI = prosta średnia arytmetyczna 9 wskaźników elementarnych w zakresie 0–1: (1) brak publikacji ogłoszenia o przetargu (0/1), (2) zmiana ogłoszenia po publikacji (0/1), (3) tryb nieotwarty (0/1), (4) długość kryteriów kwalifikacji względem średniej rynku, (5) okres składania ofert (dni od publikacji do terminu, weekendy odliczane przy krótkich okresach), (6) łączna waga kryteriów niecenowych, (7) okres decyzji (od terminu ofert do udzielenia; flagowane bardzo krótkie lub ustawowo wydłużone), (8) single bidder (0/1), (9) udział zwycięzcy = wartość jego kontraktów z danym zamawiającym w 12 mies. / całkowita wartość udzielona przez zamawiającego. | Fazekas M., King L.P. (2017/2019), Regulation & Governance (tekst otwarty przez core.ac.uk; opis wskaźników i średnia 9 proxy) – odnośnik do definicji wzorcowej: Fazekas, Tóth, King (2016), *An Objective Corruption Risk Index Using Public Procurement Data*, European Journal on Criminal Policy and Research 22(3):369–397; https://core.ac.uk/download/131381322.pdf ; https://research.ceu.edu/en/publications/an-objective-corruption-risk-index-using-public-procurement-data/ | [~] (tekst otwarty, ale to praca King/Fazekas, a nie pierwotna definicja z 2016; rok i numer tomu Regulation & Governance DO WERYFIKACJI) |
| Progi dni: tekst podaje tylko zasadę (np. 30–40 dni = mało informacji o ryzyku, 5–10 dni = skok ryzyka). Kategorie regresyjne okresu składania ofert: Węgry: >20 dni referencja, 17–20, 5–14, 0–5; Czechy: >60 referencja, 40–60, 37–40, 19–37, 0–19. To kategorie w regresji, **nie potwierdzone jako progi flagi CRI**. | j.w. (Appendix B, Table B1) | [~]; DO WERYFIKACJI: Supplementary Appendix do BJPS (PDF 768,7 KB) na stronie Cambridge Core oraz Fazekas, Tóth, King 2016 |
| Wersja IMF z konkretnymi progami (inna implementacja CRI): 7 flag – single bidder (0/1), tryb nieotwarty (wysokie ryzyko=1, średnie=0,5, brak=0 wg związku z single bidding i koncentracją), brak publikacji ogłoszenia, okres składania ofert, okres decyzji, koncentracja wydatków, udział dostawców z rajów podatkowych; CRI = średnia 7 flag w skali 0/0,5/1. Progi dni są **krajowe** (np. Rumunia, okres decyzji: <32 dni wysokie, 33–53 średnie, >50 brak flagi; Uganda, okres składania ofert: <17 wysokie, 17–41 średnie, >41 brak). Autorzy podkreślają, że CRI mierzy ryzyko, nie potwierdzoną korupcję. | IMF Working Paper WP/22/94 (2022), *Assessing Vulnerabilities to Corruption in Public Procurement and Their Price Impact*; https://www.imf.org/-/media/files/publications/wp/2022/english/wpiea2022094-print-pdf.pdf.md | [✔] (autorzy nie wymienieni w otwartej treści – DO WERYFIKACJI) |
| Wniosek praktyczny: progi dni muszą być **kalibrowane na danych polskich** (minimum ustawowe wg trybu i progu unijnego), a nie kopiowane z Rumunii czy Ugandy. | wniosek własny z porównania powyższych | – |

### 1.2 DIGIWHIST / Opentender

| Twierdzenie | Źródło | Pewność |
|---|---|---|
| Opentender to publiczny portal DIGIWHIST (projekt Horyzont 2020 nr 645852) z sekcjami „Integrity indicators" i „Transparency indicators" (definicja i obliczanie); strona „About" ma tylko nagłówki. Sekcji „administrative capacity" na tej stronie nie znalazłem. | https://ug.opentender.eu/about/about-opentender ; https://cordis.europa.eu/project/id/645852 | [✔] (stan: brak definicji w treści strony) |
| Dokładne nazwy i definicje wskaźników integrity / transparency / administrative capacity: **DO WERYFIKACJI**. Jak: opentender.eu → About → „Definition of Integrity Indicators" i „Calculation of Integrity Indicators" (analogicznie transparency); alternatywnie deliverable DIGIWHIST o wskaźnikach i publikacje Fazekasa. Nie podaję listy z pamięci. | – | **DO WERYFIKACJI** |
| Prezentacja Fazekas/Czibik wymienia elementarne wskaźniki na poziomie przetargu (single bidder, brak ogłoszenia, długość kryteriów kwalifikacji, długość okresu ogłoszenia, waga kryteriów niecenowych, unieważniony i ponownie ogłoszony, wzrost wartości kontraktu po fakcie), dostawcy (wiele firm pod jednym adresem, wiek firmy, firma założona tuż przed wygraną, niemożliwy do ustalenia beneficjent rzeczywisty) i zamawiającego (relacja trybów otwarty/nieotwarty, wydatki w trybie awaryjnym, odwołania). Przykład EIB: ponad 250 000 przetargów z 10 dostosowanymi flagami. | https://store.proebiz.com/02-aczibik_corr_measurement_ostrava__short_191106_16_9.pdf | [~] slajdy |

### 1.3 Single Market Scoreboard (KE) – zamówienia publiczne

| Twierdzenie / liczba | Źródło | Pewność |
|---|---|---|
| Wersja 2019 (PDF KE) ma **12 wskaźników** z progami „satysfakcjonujący / przeciętny / niesatysfakcjonujący": single bidder ≤10% / >20%; brak ogłoszenia (no calls for bids) ≤5% / ≥10%; publication rate >5% / <2,5% (PKB); zamówienia wspólne ≥10% / <10%; kryterium wyłącznie cena ≤80% / >80%; szybkość decyzji ≤120 dni / >120; wykonawcy MŚP >60% / <45%; oferty MŚP >80% / <60%; podział na części >40% / <25%; brakujące ogłoszenia ≤3% / >3%; brak numerów rejestrowych sprzedawcy i kupującego ≤3% / >3%. | https://ec.europa.eu/internal_market/scoreboard/_docs/2019/performance_per_policy_area/public_procurement_en.pdf | [✔] |
| Edycja z danymi za 2024 pokazuje 8 wskaźników dostępu do zamówień (te same progi zielony/czerwony dla pierwszych 8; żółty = między). | https://single-market-scoreboard.ec.europa.eu/node/264_pl | [✔]; liczba wskaźników zmieniła się między edycjami |
| **Polska 2024** vs średnia UE: single bidder **56%** (UE 28%); brak ogłoszeń 7% (5%); publication rate 7,6% PKB (5,8%); cena jako jedyne kryterium 56% (54%); szybkość decyzji 54 dni (74); wykonawcy MŚP 64% (71%); oferty MŚP 60% (72%); podział na części 47% (32%). „Średnia UE" to typowy kraj ze środka rankingu. | https://single-market-scoreboard.ec.europa.eu/index.php/node/322_pl | [✔] (strona zwróciła tabelę; uwaga: sąsiedni węzeł 321_pl zwrócił Holandię – używać 322_pl i sprawdzić tytuł strony) |

### 1.4 UZP – Sprawozdanie Prezesa UZP z funkcjonowania systemu zamówień publicznych w 2024 r.

URL: https://www.gov.pl/attachment/4be61d70-3729-402e-aa9c-94fb9d4db98f (opublikowane czerwiec 2025). Otwarto tylko pierwsze ~200 tys. z 500 tys. znaków dokumentu.

| Liczba | Pewność |
|---|---|
| Średnia liczba ofert (wszystkie postępowania) **2,84** (2023: 2,41); poniżej progów UE 2,89; w progach UE i powyżej 2,48. | [✔] |
| Jedna oferta: **35,17%** postępowań poniżej progów UE; **49,1%** powyżej progów UE (odczyt ze streszczenia – zweryfikować w oryginale, rozdział o konkurencji). | [✔]/[~] |
| Unieważnienia: ok. **21%** postępowań poniżej progów unieważnionych w całości lub części w 2024 (2023: 24%). Wartość dla powyżej progów: nie znalazłem w przeczytanym fragmencie – **DO WERYFIKACJI**. | [✔] / DO WERYFIKACJI |
| Zmiany umów: w 2024 opublikowano **10 001** ogłoszeń o zmianie umowy (BZP + Dz.U. UE) wobec 15 572 w 2023; 60% roboty budowlane, 23% usługi, 17% dostawy. 94% ogłoszeń o zamówieniu zawierało informację o możliwości zmiany umowy. **Odsetek umów zmienionych** (mianownik = liczba udzielonych zamówień) nie jest podany w przeczytanym fragmencie – DO WERYFIKACJI (rozdz. I.3.4 „Zmiany postanowień zawartej umowy"). | [✔] / DO WERYFIKACJI |
| Kontrola uprzednia Prezesa UZP: 108 kontroli w 2024 (78 w 2023), 54 (50%) bez naruszeń; progi: >10 mln EUR dostawy/usługi, >20 mln EUR roboty. | [✔] |
| **Rozbieżność:** Scoreboard (TED, tylko postępowania ogłaszane w TED, definicja single bidder z danych o udzielonych zamówieniach) daje 56% dla Polski, a UZP 49,1% powyżej progów. Różnica populacji i definicji – na pitchu podawać oba z etykietą „źródło/definicja". | wniosek własny |

### 1.5 OCP – flagi

| Twierdzenie | Źródło | Pewność |
|---|---|---|
| **73 flagi**: OCP (2024), *Red flags in public procurement: A guide to using data to detect and mitigate risks* (Camila Salazar i in.). Kategorie typu ryzyka: low transparency 6, low competition 5, fraud 12, collusion risks 19, bid-rigging 31 (suma 73). Etapy: planowanie, przetarg, udzielenie, realizacja; jednostki analizy: oferent, zamawiający, postępowanie, rynek. | https://open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf | [✔] (przeczytano ~100 tys. z 170 tys. znaków) |
| Przykłady z definicją: R003 okres składania ofert krótszy niż minimum ustawowe dla trybu; R011 dzielenie zakupów (dwa zakupy tej samej kategorii w ~3 mies. tuż poniżej progu, przykład 999 i 995 przy progu 1000); R013 wysoki udział trybów niekonkurencyjnych u zamawiającego (przykładowo >30% lub górny płot Q3+1,5·IQR); R018 jedna oferta; R022 duża rozpiętość cen ofert; R024 cena zwycięzcy bliska drugiej; R028 identyczne ceny; R029 odchylenie od prawa Benforda (wymaga dobrej jakości danych). | j.w. | [✔] |
| Starszy raport OCP 2016 *Red flags for integrity: Giving the green light to open data solutions* ma inne liczby: 36 flag liczonych z bieżącego OCDS, +75 po drobnych rozszerzeniach (111 razem); fazy: planowanie 1, przetarg 16, udzielenie 10, kontrakt 4, realizacja 5. **Nie myl z „73 flagami" (2024).** | https://www.open-contracting.org/wp-content/uploads/2016/11/Red-flags-for-integrity-Giving-the-green-light-to-open-data-solutions-shared.pdf | [✔] |
| OECD: w wynikach wyszukiwania pojawił się dokument OECD Toolbox „indicators-procurement-risk" (https://t4.oecd.org/governance/procurement/toolbox/search/indicators-procurement-risk.pdf); nie otwierałem. | – | [?] / DO WERYFIKACJI |

### 1.6 Wniosek dla prototypu
Minimalny, obronny zestaw flag liczonych z BZP/TED: single bidder; tryb bez ogłoszenia/niekonkurencyjny; okres składania ofert vs minimum ustawowe dla trybu; okres decyzji; zmiana ogłoszenia; kryteria niecenowe; zmiany umowy (wartość po/przed); koncentracja zwycięzcy u zamawiającego (12 mies.); dzielenie zakupów tuż pod progiem. Każda flaga z definicją, mianownikiem i odniesieniem do tabeli powyżej.

---

## 2. Arachne (KE)

| Twierdzenie / liczba | Źródło | Pewność |
|---|---|---|
| Arachne (legacy): **107 wskaźników** w 7 kategoriach: Procurement 6, Contract Management 11, Eligibility 9, Performance 18, Concentration 15, Reasonability 15, Reputation & Fraud 33 (suma 107). Przykłady: kontrahent z nieważnym VAT, wartość umowy vs obrót wykonawcy, koszt aneksów vs kwota umowy, wypłaty poza okresem kwalifikowalności, powiązania beneficjent–wykonawca, PEP, nowo utworzone firmy, dyrektorzy z wieloma mandatami. | KE, *Arachne introduction and demo*, https://evropskasredstva.si/app/uploads/2025/04/Arachne-introduction-and-demo.pdf | [✔] (slajdy) |
| Punktacja: każdy wskaźnik ma maksymalną wagę (na slajdach 5, 10, 20); wynik kategorii jest **ograniczony do 50** i liczony ze średniej z 3, 5 lub 10 najwyższych wskaźników; wynik ogólny = średnia wyników kategorii (przykład 39); kolory od „no risk" po „very high". Dane: dane operacyjne państw (106 pól, 15 obowiązkowych), Orbis (~450 mln firm, ~458 mln osób), WorldCompliance (PEP, sankcje), VIES, FTS. | j.w. | [✔] (mapowanie wag na konkretne wskaźniki niejasne na slajdach) |
| Arachne+ (następca): **78 wskaźników**, dane Orbis i World Compliance (Moody's); legacy zastępowany 28.04–30.06.2026; pełna wersja planowana na koniec 2027; państwa dostarczają dane od 2028. Narzędzie „nie podejmuje automatycznych decyzji". Strona nie podaje formalnej taksonomii kategorii dla Arachne+. | https://antifraud-knowledge-centre.ec.europa.eu/useful-tools/what-arachne_en | [✔] |
| Pełna lista wskaźników z oficjalnej dokumentacji („Arachne risk indicators"/Charter): **DO WERYFIKACJI** (nie znalazłem otwartego dokumentu z listą). Jak: dokumenty „Arachne Risk Indicators" w Centrum Wiedzy KE ds. zwalczania nadużyć lub materiały IP (mmr.gov.cz hostuje „ARACHNE-Difference-between-V1-2-4-and-V2-0.pdf" – nie otwierałem). | – | DO WERYFIKACJI |
| Krytyka ETO, SR **06/2023** *Conflict of interest in EU cohesion and agricultural spending – Framework in place but gaps in transparency and detection measures* (marzec 2023): ankieta 160 respondentów/501 instytucji; **26%** używa Arachne do wykrywania konfliktów interesów, **49%** nie używa, 25% nie wie/nie chce powiedzieć; użycie dobrowolne; Arachne „nie pokazuje faktycznych konfliktów, tylko flagi"; zbiory danych nie obejmują urzędników zatwierdzających wnioski; brak połączenia z EDES; jakość zależy od jakości danych; Węgry, Malta, Rumunia wolą bazy krajowe, Niemcy nie używają (ochrona danych i wątpliwości co do trafności). | https://op.europa.eu/webpub/eca/special-reports/conflict-of-interest-06-2023/en/index.html ; https://www.eca.europa.eu/Lists/ECADocuments/INSR-2023-06/INSR-2023-06_EN.pdf | [✔] |
| ETO SR **06/2026** *Tackling fraud in the RRF* (przyjęte 16.12.2025): spośród 86 instytucji audytowych/wdrażających 65% używa Arachne, 16% narzędzi krajowych, 19% żadnych; użycie „nie jest obowiązkowe na poziomie UE"; nikt nie używał funkcji „Alert Me"; Włochy załadowały ok. 97% projektów (>275 tys.); państwa zgłosiły 51 podejrzeń nadużyć do DG ECFIN (2021–2024) wobec 307 spraw RRF badanych przez EPPO; ETO nie oceniało skuteczności Arachne, tylko użycie. | https://www.eca.europa.eu/ECAPublications/SR-2026-06/SR-2026-06_EN.pdf | [✔] |
| Dodatkowo (tylko z wyników wyszukiwania): ETO SR 06/2019 o nadużyciach w polityce spójności (op.europa.eu/webpub/eca/special-reports/fraud-in-cohesion-6-2019) – nie otwierałem. | – | [?] |

Lekcja dla prototypu: Arachne to **wskaźniki + wagi + agregacja z ograniczeniem kategorii**, wynik jest priorytetyzacją, nie dowodem. Krytyka (jakość danych, brak urzędników w danych, flagi ≠ konflikt interesów) dotyczy też nas – wpisać do slajdu „ograniczenia".

---

## 3. Prognozowanie opóźnień i kosztów

### 3.1 Flyvbjerg i klasa referencyjna

| Liczba / twierdzenie | Źródło | Pewność |
|---|---|---|
| Średnie przekroczenie kosztów budowy (ceny stałe): **kolej 44,7%** (N=58, SD 38,4), **mosty i tunele 33,8%** (N=33, SD 62,4), **drogi 20,4%** (N=167, SD 29,9). „9 na 10 projektów transportowych ma przekroczenie kosztów." | Flyvbjerg B. (2005), *Policy and Planning for Large Infrastructure Projects: Problems, Causes, Cures*, World Bank Policy Research WP 3781; https://arxiv.org/pdf/1303.7400 (wersja robocza tej samej pracy). Zbiór 258 projektów pochodzi z Flyvbjerg, Holm, Buhl 2002 (JAPA 68(3):279–295) i 2003 (Transport Reviews 23(1)); dane bibliograficzne tych dwóch z pamięci **[?]**, DOI **DO WERYFIKACJI** | liczby [✔]; bibliografia 2002/2003/2004 [?] |
| Prognozy popytu: kolej – ruch pasażerski średnio 51,4% poniżej prognozy (N=25, SD 28,1), 84% prognoz błędnych o ponad ±20%; drogi – ruch +9,5% ponad prognozę (N=183, SD 44,3), 50% błędnych o ponad ±20%. | j.w. | [✔] |
| Megaprojekty (zwykle ≥1 mld USD): ok. 1 na 10 mieści się w budżecie, 1 na 10 w terminie, 1 na 10 dostarcza korzyści; ok. 1 na 1000 spełnia wszystkie trzy; 9 na 10 ma przekroczenie kosztów; kolej 44,7% i niedobór popytu 51,4%; drogi 20,4%; duże projekty ICT: ok. 1 na 6 to „cost outlier" ze średnim przekroczeniem 200% realnie; tamy: opóźnienia średnio 45% (plan 10 lat, faktycznie ~14,5); rok opóźnienia koreluje ze wzrostem przekroczenia o 4,64 pp. Termin „fat tail" nie występuje w tej pracy (jest „black swans"). | Flyvbjerg B. (2014), *What You Should Know About Megaprojects and Why: An Overview*, Project Management Journal 45(2):6–19 [?]; arXiv: https://arxiv.org/pdf/1409.0003 | [✔] (numer tomu/stron i DOI z pamięci – DO WERYFIKACJI) |
| IT: rozkład przekroczeń o strukturze potęgowej (fat tail); próba 5 392 projektów IT; abstrakt: „mała liczba projektów z ekstremalnymi przekroczeniami". Średnia i udział ogona nie są w abstrakcie. | Flyvbjerg, Budzier, Lee, Keil, Lunn, Bester (2022), *The Empirical Reality of IT Project Cost Overruns: Discovering A Power-Law Distribution*, arXiv:2210.01573; publikacja w Journal of Management Information Systems (wg wyników wyszukiwania: https://jmis-web.org/articles/1579) | [~] (abstrakt; publikacja JMIS niepotwierdzona) |
| Tabela z *How Big Things Get Done* (Flyvbjerg & Gardner 2023) – średnie przekroczenia: składowiska jądrowe 238%, igrzyska olimpijskie 157%, elektrownie jądrowe 120%, IT 73%, wiatr 13%, słońce 1%; w IT ok. 18% projektów z przekroczeniem ≥50% (zgodne z „1 na 6" z 2014). Tabela pełna (drogi, kolej, budynki, mosty – 20 typów) **DO WERYFIKACJI w książce** (Flyvbjerg & Gardner, *How Big Things Get Done*, Currency/Macmillan 2023, ISBN do sprawdzenia). | blog-streszczenie: https://lewis-lin-website.pages.dev/posts/the-sobering-reality-of-project-cost-overruns-what-the-data-tells-us | [~] źródło wtórne |
| Cantarelli, Flyvbjerg i in. (lock-in jako przyczyna przekroczeń w transporcie, Environment and Planning B 2010 37(5):792–807); Love i in. (przekroczenia w projektach IT) – wyszukane, nie otwierałem treści. arXiv: https://arxiv.org/abs/1307.2177 | – | [?] / DO WERYFIKACJI |

### 3.2 UK Green Book – optimism bias uplifts (Mott MacDonald 2002)

Tabela startowych poprawek (U = górna, L = dolna granica; wartości orientacyjne, nie absolutne maksima/minima):

| Typ projektu | Czas robót U / L (%) | CAPEX U / L (%) |
|---|---|---|
| Non-standard buildings | 39 / 2 | 51 / 4 |
| Standard buildings | 4 / 1 | 24 / 2 |
| Non-standard civil engineering | 25 / 3 | 66 / 6 |
| Standard civil engineering | 20 / 1 | 44 / 3 |
| Equipment/development | 54 / 10 | 200 / 10 |
| Outsourcing | – | 41 / 0 (OPEX) |

Źródło: Mott MacDonald (2002), *Review of Large Public Procurement in the UK* (HM Treasury) – tabela 2/4 z kopii raportu: https://www.parliament.vic.gov.au/49e91a/globalassets/sections-shared/get-involved/historical-inquiries/inquiry-into-budget-estimates-2010-11/mott_mcdonald_flyvberg_blake_dawson_waldron_studies.pdf **[✔]** (kopia raportu w materiałach parlamentu stanu Victoria). Strona HM Treasury „Green Book supplementary guidance: optimism bias" potwierdza istnienie poprawek procentowych w osobnym PDF; status (czy zastąpione nowszymi wskazówkami) i bieżące wartości **DO WERYFIKACJI**: https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias [~]. Metoda: poprawka maleje wraz z udokumentowanym ograniczaniem czynników ryzyka (dlatego zakres U–L).

### 3.3 Europejski Trybunał Obrachunkowy – megaprojekty UE

| Liczba | Źródło | Pewność |
|---|---|---|
| SR **10/2020**: 8 flagowych projektów infrastruktury transportowej (TFI) w 13 państwach + 17 działań; koszt szacowany 54,0 mld EUR; **wszystkie 8 TFI opóźnione**, 16 z 17 działań za planem; średnie opóźnienie wejścia do eksploatacji głównych części **11 lat**; czas budowy z planowanych 12 do 15 lat; średnie opóźnienie działania 34 mies. (>68% planowanego czasu); wzrost kosztów **17,3 mld EUR, tj. 47%** ponad szacunki początkowe; Canal Seine-Nord +199%, Lyon–Turyn +85%; wycofane dofinansowanie UE 1,4 mld EUR. | https://op.europa.eu/webpub/eca/special-reports/transport-flagships-10-2020/en | [✔] |
| SR **02/2026** (aktualizacja): koszt 8 TFI z 36,5 mld EUR (szacunki początkowe, stałe ceny 2019) do 66,5 mld EUR (**+82%**); +24% realnie od raportu 2020; dla 5 projektów z danymi średnie opóźnienie **17 lat** (w 2020: 11); trzy projekty zakończą się po 2030. (Odczyt z wersji PL, tytuł PL: „Unijna infrastruktura transportowa – w projektach wystąpiły dalsze opóźnienia i wzrosty kosztów…"). | https://www.eca.europa.eu/ECAPublications/SR-2026-02/SR-2026-02_PL.pdf | [✔] |
| SR **13/2024** *Absorption of funds from the RRF: progressing with delays, and risks remain for completing measures* (lipiec 2024): 73 z 104 wniosków o płatność (70%) złożono w terminie, spadek terminowości z 56% (1. wniosek) do 27% i 9,5%; niezrealizowane w terminie kamienie milowe 24% (X 2023); przyczyny podawane przez koordynatorów: zmiana okoliczności zewnętrznych 81%, niedoszacowany czas wdrożenia 77%, zamówienia publiczne **54%**, pomoc publiczna 42%; **Polska ma 70% inwestycji do realizacji w 2026 r.**; 27 z 42 próbkowanych środków (64%) zmieniono (głównie obniżenie celów, przesunięcie terminów, usunięcie). | https://www.eca.europa.eu/ECAPublications/SR-2024-13/SR-2024-13_EN.pdf | [✔] |
| Nowsze sprawozdania o polityce spójności 2021–2027 / dalsze o RRF (2025–2026): występują w wynikach wyszukiwania (m.in. SR 2025-13, OP 2026-09) – nie otwierałem. | – | DO WERYFIKACJI |

### 3.4 Polska

| Twierdzenie | Źródło | Pewność |
|---|---|---|
| NIK, P/24/052 *Realizacja zadań związanych z budową obwodnic* (GDDKiA O/Olsztyn, S51 Olsztyn Wschód–Południe): termin umowy przedłużony o 224 dni; 10 aneksów; zamówienia uzupełniające 100,5 mln zł brutto (11,01% ceny bazowej); maks. wartość umowy wzrosła do ok. 1,09 mld zł (119,93% pierwotnej); wykonawca złożył 55 zgłoszeń roszczeń, część uznana (48,3 mln zł); szacunek kosztu całości z 1 093 mln zł (XII 2014) do 1 194,5 mln zł wydatków (+9,2% wg moich obliczeń). To **jedna** kontrola, nie statystyka populacji. | https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,lol~p_24_052_202406070932121717745532~id0~01,typ,kj.pdf | [✔] |
| NIK P/25/001 (wykonanie budżetu 2024, część 39 Transport, kontrola GDDKiA): brak danych o przekroczeniach i aneksach; podano niedowykonanie – oddano 127,9 km dróg krajowych wobec 162,9 km planowanych (motorways i expressways 95,2 vs 129,4 km); wskazano m.in. przedłużające się procedury przetargowe jako przyczynę opóźnień. PKP PLK nie jest objęte. | https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kin~p_25_001_202502181310531739880653~id4~01,typ,kj.pdf | [✔] |
| Ranking czynników ryzyka czasu realizacji (ankieta, 91 poprawnych ankiet): 1) zima przy robotach zewnętrznych i stanie surowym, 2) opady, 3) późne przekazanie frontów robót, 4) trudność z pozyskaniem wykwalifikowanych pracowników, 5) błędy/niedokładność dokumentacji technicznej, 6) opóźnienia decyzji inwestora, 7) rozszerzenie zakresu przez zmiany projektowe… 20) nieprzewidziane warunki gruntowe (ranking wg ważności = wpływ × częstość). Rok i czasopismo nieznane (referencje z lat 2008–2009). | Jaśkowski P., Biruk S., *Analiza czynników ryzyka czasu realizacji przedsięwzięć budowlanych*, Politechnika Lubelska; https://repozytorium.biblos.pk.edu.pl/redo/resources/32761/file/suwFiles/JaskowskiP_AnalizaCzynnikow.pdf | [✔] treść; rok/czasopismo DO WERYFIKACJI |
| Rzetelnych populacyjnych statystyk opóźnień/przekroczeń kosztów dla GDDKiA i PKP PLK (np. raporty NIK o całych programach, dane z Programu Budowy Dróg Krajowych) nie zdążyłem potwierdzić – **DO WERYFIKACJI** (szukać: NIK „Program Budowy Dróg Krajowych" i „Krajowy Program Kolejowy", dane GDDKiA o aneksach). | – | DO WERYFIKACJI |

---

## 4. Monte Carlo na harmonogramie

Poniższe formuły są standardowe i podane **z pamięci [?]** (próba otwarcia Wikipedii nie powiodła się); są elementarne, ale przed pitchem sprawdzić np. w podręczniku (Vose, *Risk Analysis*) lub dokumentacji `scipy.stats.beta`/`PERT` w używanej bibliotece.

| Element | Treść | Pewność |
|---|---|---|
| Szacunek trójpunktowy (a = optymistyczny, m = najbardziej prawdopodobny, b = pesymistyczny) | PERT: średnia = (a + 4m + b)/6, odchylenie ≈ (b − a)/6. Trójkątny: średnia = (a + m + b)/3. Beta-PERT (λ=4): α = 1 + 4(m−a)/(b−a), β = 1 + 4(b−m)/(b−a), skalowany na [a, b]. | [?] |
| Wybór rozkładu | Trójkątny – prosty, ale przecenia ogon; beta-PERT – wygładzony, ograniczony; **lognormalny/potęgowy** – dla przekroczeń kosztów z fat tail (por. Flyvbjerg i in. 2022 dla IT, rozdz. 3.1). Beta-PERT ma ścisłą górną granicę, więc **nie modeluje ekstremów** – uwaga na pitch. | [~]/[?] |
| Korelacje | Zadania i ryzyka nie są niezależne (wspólna przyczyna: pogoda, wykonawca, decyzje inwestora). Niezależne próbkowanie zaniża rozrzut sumy. Metody: kopuła gaussowska, Iman–Conover; w prototypie wystarczy wspólny czynnik (jedna zmienna „klimat projektu" mnożąca czasy). | [?] |
| Rejestr ryzyk (risk drivers) | Każde ryzyko: prawdopodobieństwo p, skutek (rozkład trójpunktowy w dniach/PLN), zadania dotknięte. W symulacji: Bernoulli(p) × skutek. Zachować osobno „niepewność czasu trwania zadań" i „zdarzenia ryzyka", żeby nie liczyć dwa razy. | [?] |
| Raportowanie | P50 (mediana) i P80 (zwykle poziom rezerwy) całego projektu, histogram + dystrybuanta, **tornado** (korelacja Spearmana driver–wynik), udział w wariancji. Podawać rezerwę = P80 − baseline. Nie podawać jednej liczby bez przedziału. | [?] |
| Walidacja z klasą referencyjną | Skalibrować rozrzut przekroczeń do klasy referencyjnej (np. drogi: średnia 20,4%, SD 29,9 pp wg Flyvbjerg 2005; Mott MacDonald dla „non-standard civil engineering" CAPEX U=66%) – por. rozdz. 3. | [✔] liczby |

### Licencje bibliotek (PyPI JSON API sprawdzone 2026-11-16 z powłoki)

| Pakiet | Wersja na PyPI | Licencja | URL | Uwagi |
|---|---|---|---|---|
| numpy | 2.5.5 | BSD-3-Clause (plus 0BSD/MIT/Zlib/CC0 dla elementów) | https://pypi.org/project/numpy/ | [✔] permisywna |
| scipy | 1.18.1 | BSD (classifier „BSD License") | https://pypi.org/project/scipy/ | [✔] |
| pandas | 3.1.1 | BSD-3-Clause | https://pypi.org/project/pandas/ | [✔] |
| scikit-learn | 1.9.1 | BSD-3-Clause | https://pypi.org/project/scikit-learn/ | [✔] |
| lifelines | 0.30.3 | MIT | https://pypi.org/project/lifelines/ | [✔] |
| **scikit-survival** | 0.28.0 | **GPL-3.0-or-later** | https://pypi.org/project/scikit-survival/ | [✔] **nie jest permisywna** – wyklucza użycie, jeśli licencja kodu ma być permisywna |
| xgboost | 3.4.1 | Apache-2.0 | https://pypi.org/project/xgboost/ | [✔] |
| lightgbm | 4.7.0 | metadane PyPI puste; repo przeniesione na https://github.com/lightgbm-org/LightGBM ; licencja MIT z pamięci | https://pypi.org/project/lightgbm/ | [?] **DO WERYFIKACJI** (plik LICENSE w repo; API GitHub nie zwróciło pola licencji) |
| shap | 0.54.1 | MIT | https://pypi.org/project/shap/ | [✔] |
| networkx | 3.7 | BSD-3-Clause | https://pypi.org/project/networkx/ | [✔] |
| rapidfuzz | 3.14.6 | MIT | https://pypi.org/project/rapidfuzz/ | [✔] |
| pydantic | 2.14.3 | MIT | https://pypi.org/project/pydantic/ | [✔] |
| streamlit | 1.67.0 | Apache-2.0 | https://pypi.org/project/streamlit/ | [✔] |
| fastapi | 0.163.1 | MIT | https://pypi.org/project/fastapi/ | [✔] |
| duckdb | 2.0.0 | MIT (classifier; pole license puste) | https://pypi.org/project/duckdb/ | [✔]/[~] |

Do Monte Carlo wystarczą numpy/scipy (bez dodatkowych zależności).

---

## 5. ML dla ryzyka projektów/zamówień z danych o zamówieniach

| Praca | Dane | Etykieta | Cechy / model | Wynik | Pewność |
|---|---|---|---|---|---|
| Gallego J., Rivero G., Martínez J. (2021), *Preventing rather than punishing: An early warning model of malfeasance in public procurement*, International Journal of Forecasting 37(1):360–377, DOI 10.1016/j.ijforecast.2020.06.006; https://pure.urosario.edu.co/en/publications/preventing-rather-than-punishing-an-early-warning-model-of-malfea/ ; wersja robocza (2018): https://repository.urosario.edu.co/bitstream/handle/10336/18525/dt222.pdf | Kolumbia, SECOP 2011–2015, ok. 2,24 mln kontraktów, 188 cech (320 z cechami gmin) | trzy: (a) **aneksy w czasie lub kwocie** jako proxy nieefektywności (ok. 251 tys. pozytywnych), (b) wykonawcy sankcjonowani przez Contraloría (ok. 38,8 tys.), (c) czarna lista Confecámaras (ok. 23,6 tys.) | lasso logit, drzewo, **GBM** (najlepszy); 200 tys. próba, 25% walidacja, CV 5-krotna; wagi kosztów i SMOTE w CV | ROC AUC (zbiór wstrzymany): Confecámaras ok. 0,92–0,93, CGR ok. 0,80–0,81, **aneksy ok. 0,78–0,80**; autorzy wskazują PR zamiast ROC przy niezbalansowanych klasach; wśród predyktorów: wartość i czas trwania, opóźnienie między udzieleniem a wprowadzeniem do systemu, odległość do wyborów | [✔] (WP) |
| Decarolis F., Giorgiantonio C. (2022), *Corruption red flags in public procurement: new evidence from Italian calls for tenders*, EPJ Data Science 11:16, DOI 10.1140/epjds/s13688-022-00325-x; https://link.springer.com/content/pdf/10.1140/epjds/s13688-022-00325-x.pdf | Włochy, ok. 12,8 tys. przetargów drogowych 2009–2015 (ANAC) + ok. 3,5 tys. z dokumentów | zwycięzca ma właściciela/menedżera objętego dochodzeniem policji (ok. 15% kontraktów) – **nie dowód korupcji** | 18 flag, OLS/LASSO/Ridge/las losowy; CV 10-krotna, OOB | precision/recall (nie AUC w tekście): las losowy, dane główne P=0,876 R=0,453; po dodaniu wskaźników z dokumentów P=0,971 R=0,808; modele liniowe P≈0,23–0,26 | [✔] |
| De Jaegher K., Šoltés M., Titl V. (2023), *Easing Renegotiation Rules in Public Procurement: Evidence from a Policy Reform*, CERGE-EI WP 757; https://www.cerge-ei.cz/pdf/wp/Wp757.pdf | Czechy, 18 874 kontrakty 2014–2017 (ok. 22 mld EUR) | renegocjacja po reformie przepisów (X 2016) | modele ekonometryczne, nie ML predykcyjny; nie modeluje opóźnień | po reformie ok. **40%** kontraktów budowlanych renegocjowanych vs ok. 5% w innych branżach; cena po renegocjacji średnio +7,9% względem oferty; oferty spadły o ok. 3 pp | [✔] |
| VigIA (*VigIA: prioritizing public procurement oversight with machine learning models and risk indices*, Data & Policy, Cambridge UP, 2024): Kolumbia SECOP, ML + wskaźniki ryzyka; URL z wyszukiwania: https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/34D04747A94A7099E3CD8B91221338ED/S263232492400083Xa.pdf/vigia-prioritizing-public-procurement-oversight-with-machine-learning-models-and-risk-indices.pdf | – | – | – | autorzy, DOI i metryki **DO WERYFIKACJI** (otwarcie strony Cambridge zablokowane przez allowlistę) | [?] |
| Portugalia: *Predicting construction project compliance with machine learning model: case study using Portuguese procurement data*, Emerald, DOI-segment w URL: 10.1108/ECAM-09-2023-0973; https://emerald.com/insight/content/doi/10.1108/ECAM-09-2023-0973/full/html | – | – | – | tylko z wyników wyszukiwania; **DO WERYFIKACJI** | [?] |
| Decarolis i in. o opóźnieniach i przekroczeniach na danych włoskich oraz Titl & Fazekas o ML na danych czeskich: poza powyższymi nie znalazłem potwierdzonej pracy z AUC; Bank of Italy QEF 544/2020 (wersja robocza Decarolis–Giorgiantonio): https://www.bancaditalia.it/pubblicazioni/qef/2020-0544/index.html (nie otwierałem). | – | – | – | **DO WERYFIKACJI** | [?] |

**Etykiety zastępcze – wnioski z literatury (z powyższych prac):**
- Aneksy/zmiany umów (Gallego): proxy nieefektywności, ale zależne od reżimu prawnego – Titl i in. pokazują skok renegocjacji z ~5% do ~40% w budownictwie po zmianie przepisów (etykieta „dryfuje" z prawem, nie tylko z jakością projektu). W Polsce reżim zmian umów to art. 454–455 Pzp: trzeba oznaczyć daty wejścia przepisów i nie uczyć na mieszanym okresie bez cechy „reżim".
- Sankcje/dochodzenia (Gallego, Decarolis): obserwowana jest aktywność organów, nie sam fakt nadużycia (selekcja, brak pewności, że brak sankcji = brak nadużycia). Autorzy Decarolisa piszą wprost, że dochodzenie nie jest dowodem.
- Unieważnienie: w BZP to często skutek ubocznych przyczyn (cena powyżej budżetu, błędy formalne); traktować jako osobny typ zdarzenia, nie jako „zły projekt".
- Wszystkie trzy etykiety są **zaobserwowane po zdarzeniu**; cechy muszą być ograniczone do informacji dostępnych w momencie ogłoszenia/udzielenia (Gallego: cecha „opóźnienie wprowadzenia do systemu" jest legalna tylko jeśli znana ex ante – to przykład ryzyka przecieku).

---

## 6. LLM do ekstrakcji ryzyk z dokumentów

### 6.1 Publikacje i wdrożenia

| Twierdzenie | Źródło | Pewność |
|---|---|---|
| TCU (Brazylia) **ALICE360**: generatywne AI + wyszukiwanie wektorowe + statystyka do monitorowania zakupów z PNCP; LLM wyciąga opisy z PDF-ów, indeksuje pozycje w bazach wektorowych, statystyka (IQR, z-score, percentyle) wykrywa nadcenę; wyjście JSON z alertami; dane 25.07.2023–25.07.2024; potencjalny wolumen ok. 591 mld R$, z indykacjami ryzyka ok. 133 mld R$ (20–25%); trafność ekstrakcji opisów ok. 98% (testy wewnętrzne); **pilotaż: precision 94,1%, accuracy 96,7%** (próba ograniczona; lepiej w kategoriach standardowych – leki, IT; gorzej w heterogenicznych); recall dopiero planowany. Rok publikacji nieznany. | de Mendonça A.F., Ramos F.M., Castro L.R.A., Boaventura R.S., *ALICE360: Inteligência Artificial como ferramenta para avaliar compras públicas*, https://revista.tcu.gov.br/ojs/index.php/sifap/article/download/2452/2118/7235 | [✔] (rok DO WERYFIKACJI) |
| ContractEval: benchmark LLM do identyfikacji ryzyk prawnych na poziomie klauzul (CUAD), 4 modele własnościowe i 15 otwartych; modele własnościowe lepsze; modele otwarte częściej zwracają „brak klauzuli" mimo jej istnienia; tryb rozumowania poprawia przydatność, ale obniża poprawność; kwantyzacja obniża jakość; większość LLM porównywalna z młodszym asystentem prawnym. | Liu S., Li Z., Ma R., Zhao H., Du M. (2025), arXiv:2508.03080; https://arxiv.org/abs/2508.03080 (także ACL NLLP 2025: https://preview.aclanthology.org/setup/2025.nllp-1.19) | [~] abstrakt |
| Bank Światowy / EBI / hiszpańskie i ukraińskie narzędzia do ekstrakcji ryzyk LLM: nie znalazłem potwierdzonych publikacji. Jedynie przykład EIB: 250 tys. przetargów z 10 flagami (nie LLM). | – | **DO WERYFIKACJI** |

### 6.2 Dobre praktyki (wniosek z źródeł + inżynieria; część [?])
1. **Schemat wyjścia**: stały JSON (kategoria ryzyka z zamkniętej listy, poziom, uzasadnienie, `cytat`, `strona`). Walidacja pydantic.
2. **Dowód z dokumentu**: każde ryzyko musi mieć dosłowny cytat i lokalizację; flaga bez cytatu odrzucana (w API Claude można użyć mechanizmu cytowań – patrz 6.3).
3. **Ocena na złotym zbiorze**: ręcznie oznaczone 30–50 dokumentów (SWZ/OPZ/umowy), precision/recall per kategoria; osobno metryka „czy cytat faktycznie zawiera twierdzenie". ALICE360 podaje precision, a recall dopiero planuje – pitch powinien podać oba.
4. Modele otwarte mogą zwracać „brak klauzuli" zbyt często (ContractEval) – mierzyć recall.
5. Dane wrażliwe: SWZ i umowy publiczne zwykle jawne, ale przy pracy lokalnej (Bielik/PLLuM) łatwiej uzasadnić prywatność.

### 6.3 Aktualne modele i funkcje API Anthropic (stan na 2026-11-16, platform.claude.com)

| Informacja | Źródło | Pewność |
|---|---|---|
| Najnowsze identyfikatory API (dosłownie): `claude-fable-5-2` (1M kontekstu, 128K wyjścia; $8/$40 za MTok), `claude-opus-5-5` ($4/$20), `claude-sonnet-5-5` ($2/$10), `claude-haiku-5-5` (od $0,10/$0,50). Strona zaleca Opus 5.5 do większości zadań, Fable 5.2 do najtrudniejszego rozumowania. Aktualną listę dostać z `GET /v1/models` (pole `lifecycle`). Starsze modele wymienione są bez ID na stronie. | https://platform.claude.com/docs/en/about-claude/models/overview | [✔] |
| **Structured outputs**: obsługiwane przez wszystkie modele w Messages API; parametr `output_config.format` z `type: "json_schema"`; nagłówek beta niepotrzebny; stary `output_format` jest przestarzały (wymaga nagłówka `structured-outputs-2025-11-13`); `strict: true` dla narzędzi; ograniczenia: `additionalProperties: false`, brak prefillingu, `stop_reason: "refusal"`/`"max_tokens"` mogą dać niezgodny wynik. | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | [✔] |
| **Citations**: obsługują wszystkie aktywne modele; włączane `citations: {"enabled": true}` w bloku `document`; typy: tekst (indeksy znaków), PDF (numery stron), własna treść (indeksy bloków); `cited_text` nie liczy się do tokenów wyjścia; PDF skanowane bez tekstu nie dają cytowań. **Citations nie można łączyć z structured outputs – API zwraca błąd 400.** Obejście z dokumentacji: model zwraca „jedno pole na linię", które parsujemy w kodzie. | https://platform.claude.com/docs/en/build-with-claude/citations | [✔] |
| **PDF**: wszystkie aktywne modele; do 128 MB żądania; do 600 stron (100, gdy okno <1M); wysyłka: URL, base64 lub `file_id` (Files API); ok. 1500–3000 tokenów tekstu na stronę plus obraz strony. | https://platform.claude.com/docs/en/build-with-claude/pdf-support | [✔] |
| Konsekwencja dla Risk Miner: albo (A) citations + parsowanie linii, albo (B) structured outputs + weryfikacja cytatów po stronie kodu (sprawdzenie, że `cytat` jest podciągiem tekstu dokumentu). B jest prostsze do testowania. | wniosek własny z dwóch stron powyżej | – |

### 6.4 Modele polskie do pracy lokalnej

| Model | Fakty | Źródło | Pewność |
|---|---|---|---|
| **Bielik 11B v3.0 Instruct** (SpeakLeash/ACK Cyfronet): 11 mld parametrów, licencja **Apache 2.0** (+ osobne Bielik Terms of Use, bielik.ai/terms), format ChatML, dotrenowany z Bielik-11B-v3-Base-20250730; raport techniczny arXiv:2601.11579 (30.12.2025; architektura: depth up-scaling z Mistral 7B v0.2, SFT+DPO+RL; „32 języki europejskie"). Kontekst **32K** (strona Ollama). | https://huggingface.co/speakleash/bielik-11b-v3.0-instruct ; https://arxiv.org/abs/2601.11579 ; https://ollama.com/SpeakLeash/bielik-11b-v3.0-instruct | [✔] |
| Ollama: `ollama run SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` – rozmiary: Q4_K_M 6,7 GB, Q5_K_M 7,9 GB, Q6_K 9,2 GB, Q8_0 12 GB, bf16 22 GB. | https://ollama.com/SpeakLeash/bielik-11b-v3.0-instruct | [✔] |
| Nowsza **Bielik-11B-v3.1** (kolekcja na HF, m.in. Instruct, FP8, GGUF, AWQ; aktualizacja „6 dni temu" wg strony) oraz mniejsze v3.0: 4.5B, 1.5B (warianty AWQ/MLX/NVFP4). Licencja i kontekst v3.1: **DO WERYFIKACJI** (strona modelu nie była dostępna z mojego środowiska). Bielik ma także GGUF dla v3.0 (https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-GGUF wg wyników wyszukiwania). | https://huggingface.co/speakleash | [~] |
| **PLLuM** (rodzina 2512, grudzień 2025; Ministerstwo Cyfryzacji, dalej HIVE AI; praca arXiv:2511.03823, 5.11.2025): 4B (baza gemma-3-4b-pt, **Apache 2.0**), 8B Llama-PLLuM (baza Llama-3.1-8B, licencja **Llama 3.1**), 12B (Mistral-Nemo-Base-2407, **Apache 2.0**), 70B (Llama-3.1-70B, licencja **Llama 3.1**; brak wersji base 70B); warianty base/instruct/chat; „chat" = dostrojony do preferencji. Wcześniejsze wersje 2412 i 2508 też istnieją, w tym warianty „nc" (niekomercyjne) – licencje wersji 2412/2508 **DO WERYFIKACJI**. | https://huggingface.co/CYFRAGOVPL/Llama-PLLuM-70B-chat-2512 ; lista: https://huggingface.co/CYFRAGOVPL/models | [✔] (2512) |

---

## 7. Standardy zarządzania ryzykiem – słownictwo jury

| Standard | Co wziąć | Pewność |
|---|---|---|
| ISO 31000:2018 *Risk management – Guidelines* | Zasady, ramy, **proces**: komunikacja i konsultacje; zakres, kontekst, kryteria; ocena ryzyka (identyfikacja → analiza → wartościowanie); postępowanie z ryzykiem; monitorowanie i przegląd; rejestrowanie i raportowanie. Kryteria ryzyka (apetyt, tolerancja). Nie otwierałem tekstu normy (płatna); zakres z pamięci. | [?] DO WERYFIKACJI: https://www.iso.org/standard/65694.html |
| PMBOK Guide (PMI) | Rejestr ryzyk, ocena jakościowa (macierz prawdopodobieństwo × skutek), ilościowa (analiza wrażliwości, Monte Carlo, drzewa decyzyjne), plan reakcji na ryzyko, ryzyko rezydualne i wtórne. Wersja (7. ed. 2021 / nowsza) DO WERYFIKACJI. | [?] |
| **EGESIF_14-0021-00** *Fraud Risk Assessment and Effective and Proportionate Anti-Fraud Measures* (KE, 16.06.2014) | Samoocena w 5 krokach: (1) ryzyko brutto (wpływ × prawdopodobieństwo), (2) ocena skuteczności istniejących kontroli, (3) ryzyko netto/rezydualne, (4) wpływ planowanych dodatkowych kontroli, (5) ryzyko docelowe (akceptowalne). Trzy procesy: wybór wnioskodawców, realizacja i weryfikacja, certyfikacja i płatności; arkusz dla zamówień prowadzonych bezpośrednio. Wymienia Arachne (użycie dobrowolne). Skala wpływu/prawdopodobieństwa jest w załączniku, którego nie widziałem (często 1–4, **DO WERYFIKACJI**). Dokument nie wspomina okresu 2021–2027. | https://sfc.ec.europa.eu/system/files/documents/sfc-files/egesif-14-0021-00-fraud-risk-assessment.pdf – **[✔]** |
| Następca na 2021–2027 | Nie potwierdziłem. Sprawdzić: Centrum Wiedzy KE ds. zwalczania nadużyć i wytyczne dla IZ w perspektywie 2021–2027 (art. 74(2) rozporządzenia 2021/1060 – z pamięci, DO WERYFIKACJI). | DO WERYFIKACJI |
| KE, *Guide to Cost-Benefit Analysis of Investment Projects for Cohesion Policy 2014–2020* (19.12.2014) | „Obowiązkowy dla wszystkich dużych projektów ESIF 2014–2020"; ocena ryzyka w sekcji 2.8 przewodnika (analiza wrażliwości, rozkłady prawdopodobieństwa/ocena ryzyka – szczegóły sekcji 2.8 **DO WERYFIKACJI**). W 2014–2020: CBA z oceną ryzyka był obowiązkowy do zatwierdzenia dużych projektów (art. 101 rozp. 1303/2013). | https://ec.europa.eu/regional_policy/en/information/publications/guides/2014/guide-to-cost-benefit-analysis-of-investment-projects-for-cohesion-policy-2014-2020 ; Vademecum, tabela 1 | [✔] (strona i Vademecum) |
| KE, *Economic Appraisal Vademecum 2021–2027* (20.09.2021) | Dla 2021–2027 **brak wymogu prawnego** CBA dla „major projects" z ex ante zatwierdzeniem; zalecenie, aby nadal stosować przewodnik z 2014 dla dużej infrastruktury; ryzyka projektu mają być opisane w ocenie ryzyka (jakościowej i/lub ilościowej) wg sekcji 2.8 przewodnika 2014, a ryzyka systemowe testowane analizą wrażliwości zamiast korekty stopy dyskonta; „review the impact of risks, uncertainties and inherent biases" w trakcie przygotowania. Vademecum samo nie omawia oceny ryzyka (poza zakresem). | https://ec.europa.eu/regional_policy/en/information/publications/guides/2021/economic-appraisal-vademecum-2021-2027-general-principles-and-sector-applications ; https://jaspers.eib.org/LibraryNP/EC%20Reports/Economic%20Appraisal%20Vademecum%202021-2027%20-%20General%20Principles%20and%20Sector%20Applications.pdf | [✔] |
| Polskie wytyczne MFiPR dot. przygotowania projektów inwestycyjnych (2021–2027): tytuł, wersja i wymogi analizy ryzyka **nie potwierdzone** (strona gov.pl z listą wytycznych niedostępna – blokada robots). Jak sprawdzić: https://www.gov.pl/web/fundusze-regiony/wytyczne-na-lata-2021-2027 → „Wytyczne dotyczące zagadnień związanych z przygotowaniem projektów inwestycyjnych, w tym projektów generujących dochód i projektów hybrydowych na lata 2021–2027" (tytuł z pamięci); w Monitorze Polskim wytyczne zwykle ogłasza się jako komunikat (wyniki wyszukiwania zwróciły eli.gov.pl MP/2023/292 – nie wiadomo czy to ta wytyczna). | – | DO WERYFIKACJI |
| Poglądowy wzorzec analizy ryzyka w studium wykonalności (nie jest wytyczną MFiPR!): instrukcja zakresu studium dla projektu EOG (geotermia) – analiza wrażliwości NPV/IRR, wskazanie procentowej zmiany zmiennej zerującej NPV (switching value), ryzyka w czterech grupach (formalno-instytucjonalne, ekologiczno-techniczne, społeczne, finansowe), macierz 5×5 (prawdopodobieństwo marginalne…bardzo wysokie × skutek nieistotny…poważny), środki zapobiegawcze i ryzyko rezydualne. | https://www.gov.pl/attachment/fe806896-001e-4025-a80f-d0151710d8c1 | [✔] treść; [?] relewantność do wytycznych MFiPR |

---

## 8. Dziesięć liczb, które warto znać na pamięć (każda ze źródłem)

1. **56%** postępowań w Polsce z jedną ofertą (2024) vs **28%** średnia UE; próg czerwony Scoreboardu >20%. – Single Market Scoreboard, https://single-market-scoreboard.ec.europa.eu/index.php/node/322_pl [✔]
2. **2,84** – średnia liczba ofert w Polsce w 2024 (2,41 w 2023); **35,17%** postępowań poniżej progów UE z jedną ofertą. – Sprawozdanie Prezesa UZP za 2024, https://www.gov.pl/attachment/4be61d70-3729-402e-aa9c-94fb9d4db98f [✔]
3. **44,7% / 33,8% / 20,4%** – średnie przekroczenie kosztów: kolej / mosty i tunele / drogi (N=58/33/167). – Flyvbjerg 2005, https://arxiv.org/pdf/1303.7400 [✔]
4. **9 na 10** projektów z przekroczeniem kosztów; ok. **1 na 1000** megaprojektów spełnia budżet, termin i korzyści jednocześnie. – Flyvbjerg 2014, https://arxiv.org/pdf/1409.0003 [✔]
5. **+47%** kosztów i **11 lat** średniego opóźnienia 8 flagowych projektów UE (SR 10/2020); w aktualizacji SR 02/2026 koszt **+82%**, opóźnienie **17 lat**. – ETO, https://op.europa.eu/webpub/eca/special-reports/transport-flagships-10-2020/en ; https://www.eca.europa.eu/ECAPublications/SR-2026-02/SR-2026-02_PL.pdf [✔]
6. **66%** i **200%** – górne poprawki CAPEX Mott MacDonald dla „non-standard civil engineering" i „equipment/development". – https://www.parliament.vic.gov.au/49e91a/globalassets/sections-shared/get-involved/historical-inquiries/inquiry-into-budget-estimates-2010-11/mott_mcdonald_flyvberg_blake_dawson_waldron_studies.pdf [✔]
7. **70%** inwestycji z KPO Polski miało zostać zrealizowanych w 2026 r.; **54%** koordynatorów wskazało zamówienia publiczne jako przyczynę opóźnień RRF. – ETO SR 13/2024, https://www.eca.europa.eu/ECAPublications/SR-2024-13/SR-2024-13_EN.pdf [✔]
8. **107** wskaźników w **7** kategoriach Arachne (legacy); wynik kategorii ograniczony do 50; Arachne+ ma 78. – KE, https://evropskasredstva.si/app/uploads/2025/04/Arachne-introduction-and-demo.pdf ; https://antifraud-knowledge-centre.ec.europa.eu/useful-tools/what-arachne_en [✔]
9. **73** czerwone flagi w przewodniku OCP 2024 (31 bid-rigging, 19 collusion, 12 fraud, 6 low transparency, 5 low competition). – https://open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf [✔]
10. **AUC 0,78–0,80** dla prognozy aneksów (czas/kwota) w Kolumbii (GBM, 2,24 mln kontraktów) vs 0,92–0,93 dla czarnej listy wykonawców – etykieta determinuje wynik. – Gallego i in., https://repository.urosario.edu.co/bitstream/handle/10336/18525/dt222.pdf [✔] (WP 2018; wersja IJF 2021 DOI 10.1016/j.ijforecast.2020.06.006)

Rezerwa: **40% vs 5%** – udział renegocjowanych kontraktów budowlanych w Czechach po poluzowaniu przepisów vs inne branże (Titl i in., CERGE-EI WP 757) [✔]; **26%** instytucji używało Arachne do konfliktu interesów (ETO SR 06/2023) [✔].

---

## 9. Pięć najczęstszych błędów metodycznych w takich prototypach

1. **Przeciek etykiety (data leakage).** Cechy znane dopiero po udzieleniu/realizacji (liczba aneksów, data wprowadzenia do rejestru, wartość końcowa) trafiają do modelu przewidującego aneks lub opóźnienie. Przykład z literatury: cecha „opóźnienie między udzieleniem a wprowadzeniem do systemu" w Gallego i in. jest legalna tylko jeśli dostępna w momencie decyzji. Zasada: tabela cech z datą „as-of" = data ogłoszenia lub udzielenia.
2. **Ocena na danych treningowych lub losowy podział zamiast czasowego.** Obowiązkowy podział czasowy (trenuj na latach ≤ T, testuj na T+1), grupowanie po zamawiającym; raportuj AUC *i* precision@k/PR (nierównowaga klas; Gallego sami zalecają PR). Uwaga: reżim prawny zmienia etykietę w czasie (Titl: 5%→40%).
3. **Mylenie flagi/korelacji z nadużyciem.** CRI, Arachne i flagi OCP mierzą ryzyko, a nie dowód; ETO (06/2023) wprost: Arachne „nie pokazuje faktycznych konfliktów"; Decarolis: dochodzenie ≠ korupcja. Język prototypu: „ryzyko do weryfikacji", nigdy „korupcja/oszustwo".
4. **Zła podstawa (mianownik) i niekalibrowane progi.** Single bidder liczony na wszystkich postępowaniach vs tylko konkurencyjnych (UZP 35%/49% vs Scoreboard 56%); progi dni z cudzego kraju (IMF: Rumunia/Uganda) zamiast ustawowych minimów polskich; ignorowanie wielkości zamawiającego (mała próba → ekstremalne odsetki; użyj przedziałów ufności lub shrinkage).
5. **Monte Carlo z niezależnymi, ograniczonymi rozkładami.** Niezależne próbkowanie i beta-PERT/trójkątny z twardym maksimum zaniżają ogon (Flyvbjerg: fat tails, rozkład potęgowy dla IT); brak korelacji (wspólne ryzyka) zaniża P80. Rozwiązanie: wspólny czynnik, ogon z klasy referencyjnej, walidacja zakresu względem Mott MacDonald/Flyvbjerg, raportowanie P50 *i* P80.

(Dodatkowo, drobiazgi do prototypu LLM: brak złotego zbioru i brak weryfikacji, że cytat jest w dokumencie; patrz 6.2.)
