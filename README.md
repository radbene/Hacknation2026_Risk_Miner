# RISK MINER: baza doświadczeń inwestycji publicznych, w której każdy wniosek ma źródło i akceptację eksperta

RISK MINER pozwala analitykowi instytucji wdrażającej w kilka minut zobaczyć, jak podobne zakończone inwestycje
wodno-kanalizacyjne przekroczyły koszt i termin oraz dlaczego. Dziś to wymaga ręcznego przeglądania setek ogłoszeń
BZP i dokumentów. Rozwiązanie zadania **RISK MINER** (Ministerstwo Funduszy i Polityki Regionalnej) na HackNation 2026.

**Film demo (ok. 2 min):** ⟨link do filmu⟩ · **Prezentacja:** [docs/prezentacja.pdf](docs/prezentacja.pdf) ·
**Działająca wersja:** ⟨link do aplikacji⟩ · **Repozytorium:** https://github.com/radbene/Hacknation2026_Risk_Miner

Film demo, prezentacja wideo i PDF slajdów powstają z nagrań działającej aplikacji: [video/README.md](video/README.md).

## Dla kogo i jaki problem rozwiązuje

- **Użytkownik:** analityk i ekspert instytucji przygotowującej lub oceniającej inwestycję wodno-kanalizacyjną (IZ/IP, beneficjent).
- **Problem dziś:** co piąta umowa w BZP ma ogłoszoną zmianę terminu (7 719 z 39 094). Przyczyny są opisane w
  ogłoszeniach o zmianie i o wykonaniu umowy, w aneksach i protokołach, ale nikt nie łączy ich z projektami ani nie
  przypisuje im kategorii ryzyka.
- **Co zmienia rozwiązanie:** automatycznie buduje łańcuch projekt → postępowania → ogłoszenia → umowa → zmiany →
  zdarzenia R01–R15 z cytatem i linkiem do źródła, a dla nowej inwestycji podaje podobne przypadki, zakresy odchyleń
  (z liczebnością próby), flagi, działania i zapisy umowne. Ekspert zatwierdza każdy wynik.

## Jak spełniamy kryteria

| Kryterium | Waga | Co zrobiliśmy | Gdzie to zobaczyć |
|---|---|---|---|
| Pozyskanie i łączenie danych | 20% | import xlsx z dowodem dla każdej komórki; BZP na żywo (oficjalne API, 156 zapytań, 952 ogłoszenia dla 22 projektów) i kopia BZP organizatora (113 tys. ogłoszeń); dodatkowe źródła publiczne: KPOŚK (aglomeracja, RLM, skanalizowanie), TED, Biała lista VAT i KRS; dopasowanie po kluczach (KPO, BZP, NIP, OCID, odwołania 4.5), częściach i kandydatach z oceną; pułapki pokazane jako odrzucone alternatywy; dziennik wszystkich zapytań | „Źródła danych”, karta projektu → „Inne źródła publiczne”, `GET /api/ops/log`, [raport z testu](docs/raport_z_testu.md) §2, [źródła i dopasowanie](docs/zrodla_i_dopasowanie.md) |
| Dokumenty i zdarzenia | 20% | zdarzenia regułowe z pól ogłoszeń; przyczyny zmian umów (art. 455) klasyfikowane przez Bielika tylko z cytatem sprawdzonym w źródle; protokoły i aneksy PDF/DOCX (także skany przez OCR): nowy termin, koszt i przyczyna z cytatem, sygnały ryzyka ze stroną lub akapitem; dokumenty z pliku albo z linku | karta projektu → „Zdarzenia i przyczyny” → „Pokaż w źródle” otwiera oryginał z podświetlonym fragmentem |
| Nowa inwestycja | 25% | opis albo dokument (PDF, DOCX, skan) → cechy z cytatem → 12 najbardziej podobnych z 12 943 zakończonych inwestycji, z rozbiciem podobieństwa → zakresy kosztu i czasu (n, przedział) → ocena budżetu i harmonogramu → flagi R01–R15 → działania, zapisy umowne i wzorcowe przypadki zatwierdzone przez eksperta → eksport DOCX/JSON/CSV | „Nowa analiza”, [exports/przyklad/](exports/przyklad/) |
| Kontrola eksperta, edycja, modułowość | 20% | wszystko startuje jako „proponowane”; akceptuj / popraw / odrzuć / przepnij / oznacz jako wzorcowe; historia zmian; ponowne przetwarzanie nie nadpisuje decyzji; edytor wiedzy (R01–R15, podsektory, wagi) z wersjami; własny model językowy dodawany w konfiguracji | „Panel eksperta” → „Do zatwierdzenia”, „Wiedza ekspercka”, „Modele językowe” |
| UX, technologia, skalowalność | 15% | interfejs po polsku z rolami analityka i eksperta, objaśnieniami i słowniczkiem, działa na telefonie; poziom `auto` z 45 tys. postępowań; rejestr konektorów; routing LLM per zadanie (lokalny / UE / poza UE / bez LLM); monitoring trwających inwestycji z trybem `as_of`; docker compose | [architektura](docs/architektura.md), „Scenariusze testowe” |

## Wyniki

Liczby generuje `riskminer report` po przebiegu `riskminer demo` ([docs/raport_z_testu.md](docs/raport_z_testu.md)).

| Metryka | Wynik | Zbiór |
|---|---|---|
| Precyzja powiązań projekt → ogłoszenia BZP | 1,0 | zbiór wzorcowy: 22 projekty, 76 ogłoszeń do powiązania, 17 pułapek (13 ogłoszeń tego samego zamawiającego o podobnym tytule, 4 inne części tego samego postępowania), 2 ogłoszenia, których nie ma w BZP |
| Kompletność (recall) powiązań | 1,0 | jw. |
| Powiązania projektów poprawne / niepewne / błędne / brakujące | 22 / 0 / 0 / 0 | jw. |
| Błędy w danych organizatora wykryte automatycznie | 1 błędny numer ogłoszenia BZP (Wolin, RM-2026-022) i 161 braków danych | lista 22 projektów |
| Przyczyny zmian umów: zgodność z oznaczeniem ręcznym (reguły, F1) | 0,93 (zbiór wzorcowy) · 0,87 (zbiór kontrolny) | 26 przyczyn (zbiór wzorcowy) + 32 (zbiór kontrolny) |

Precyzja to trafione ogłoszenia podzielone przez wszystkie powiązane przez system, kompletność to trafione podzielone
przez 76 (`riskminer.link.quality.evaluate`). Zbiór wzorcowy ([backend/tests/fixtures/gold/](backend/tests/fixtures/gold/))
zespół oznaczył ręcznie, czytając ogłoszenia; dopasowanie było rozwijane na tych samych 22 projektach, więc wynik 1,0
nie jest pomiarem na niezależnym zbiorze.

## Uruchomienie

Wymagania: Docker z Docker Compose. Klucz API nie jest potrzebny: bez klucza działa profil reguł, a zapisane
odpowiedzi modelu są odtwarzane (`LLM_MODE=replay`).

```bash
git clone https://github.com/radbene/Hacknation2026_Risk_Miner.git risk-miner && cd risk-miner
cp .env.example .env && cp config/settings.example.yaml config/settings.yaml
DOMAIN=:80 HTTP_PORT=8088 docker compose --profile prod up -d --build    # http://localhost:8088
docker compose exec api riskminer demo                                   # dane demo, eksport, raport
docker compose exec api riskminer sources                                # KPOŚK, TED, Biała lista VAT, KRS
```

**Konta:** bez logowania pracujesz jako analityk. Panel eksperta: `ekspert` / `demo-riskminer`; w wersji demo
wystarczy przycisk „Wejdź jako ekspert (demo)” w oknie logowania. Pozostałe konta: `admin`, `analityk`, `gosc`
(tylko odczyt), to samo hasło. Stan demo przywraca `POST /api/admin/reset-demo` (konto `admin`, tryb `DEMO_MODE`).

**Od czego zacząć:** „Baza przypadków” → karta projektu Nowogard (RM-2026-020): „Ogłoszenia BZP tej inwestycji”,
„Zdarzenia i przyczyny” → „Pokaż w źródle”, „Inne źródła publiczne”. Potem „Nowa analiza” → „Wstaw przykładowy opis”
→ „Odczytaj cechy” → „Analizuj ryzyko”, a na koniec „Panel eksperta” → „Do zatwierdzenia”. Kroki do każdego
kryterium oceny są w zakładce „Scenariusze testowe”.

Tryb deweloperski (`make up migrate`, potem `make api`, `make worker`, `make web` → http://localhost:5180;
testy: `make test`) i wdrożenie na serwer: [docs/uruchomienie.md](docs/uruchomienie.md).
Model językowy: domyślnie lokalny Bielik 11B v3.0 przez Ollama (`docker compose --profile bielik`, wymaga GPU,
[docs/hosting.md](docs/hosting.md)); zapasowo `ANTHROPIC_API_KEY` w `.env`; bez modelu działają same reguły.
OCR skanów: Tesseract lokalnie (obraz `deploy/ocr/`, ustawienie `ocr.command`).

## Architektura

FastAPI + Postgres 16 (pgvector) + kolejka zadań w bazie + React 19. Konektory zapisują surowe odpowiedzi i dziennik
zapytań; parser DOM rozbija ogłoszenia BZP na sekcje z offsetami; moduł dopasowania buduje łańcuch z wyjaśnieniem;
ekstrakcja tworzy zdarzenia z cytatem; analiza nowej inwestycji używa klasy referencyjnej z bazy (podobieństwo cech,
tekstu i embeddingów liczonych lokalnie). Model językowy jest opcjonalny i wymienny w konfiguracji: lokalny Bielik
przez Ollama (domyślnie), dowolny model zgodny z API OpenAI, Anthropic, Gemini albo bez LLM.
Diagram: [docs/architektura.md](docs/architektura.md), ERD: [docs/erd.md](docs/erd.md).

## Dane

| Źródło | Co z niego bierzemy |
|---|---|
| BZP / e-Zamówienia (API i kopia organizatora) | ogłoszenia, postępowania, umowy, zmiany umów, wykonanie |
| Lista projektów i materiały eksperckie organizatora | 22 projekty, katalog ryzyk R01–R15, porady i zapisy umowne |
| KPOŚK (sprawozdanie z dane.gov.pl) | aglomeracja projektu, RLM, stopień skanalizowania, długość sieci |
| TED (API v3) | ogłoszenia robót tych samych zamawiających na poziomie UE |
| Biała lista VAT, KRS | status VAT i stan w KRS beneficjentów i wykonawców (likwidacja, upadłość, restrukturyzacja) |
| Dokumenty (plik albo link) | protokoły, aneksy, wnioski; skany odczytuje OCR |

Dowodem jest trwały link do źródła (dla BZP `ezamowienia.gov.pl`; lustro organizatora zapisujemy tylko jako miejsce
pobrania). Wykonawcy będący osobami fizycznymi są maskowani; z Białej listy nie zapisujemy numerów kont, a dla osób
fizycznych także nazwy i adresu. Do modelu językowego trafiają tylko fragmenty publicznych ogłoszeń i dokumentów po
usunięciu danych osobowych; miejsce przetwarzania pokazuje pasek w interfejsie i `config/settings.example.yaml`.

## Ograniczenia

Co działa, a co jest tylko zaprojektowane: [docs/status.md](docs/status.md) i [docs/opis_rozwiazania.md](docs/opis_rozwiazania.md).
- KIO (wyszukiwarka orzeczeń dostępna tylko przez formularz), Baza Konkurencyjności 2021 (API wymaga logowania)
  i raporty NIK są zaprojektowane, ale nie wdrożone.
- Dokumenty z platform zakupowych nie są pobierane automatycznie (logowanie, HTTP 429), więc trzeba je wgrać lub podać link.
- Zakresy odchyleń dla rzadkich podsektorów mają małe n; system to pokazuje i poszerza przedział.
- Ekran „Nowa analiza” przyjmuje plik; dokument z linku można dodać na karcie projektu albo przez API
  (`POST /api/documents/from-url`).

## Wdrożenie i koszty

Jeden serwer w UE (Hetzner CX32, ok. 8 EUR/mies.) z docker compose. Możliwy serwer w urzędzie i model lokalny
(`data_location: local`). Koszt LLM na analizę: 0 zł przy lokalnym Bieliku (płacimy tylko za serwer z GPU, np.
Scaleway L4 w Warszawie, [docs/hosting.md](docs/hosting.md)); zużycie: `GET /api/ops/llm-usage`. Nowy sektor to nowe
pliki wiedzy (`knowledge/<sektor>/`) generowane z dokumentów eksperta.

## Ujawnienie

- **Co powstało podczas hackathonu:** cała aplikacja (backend, frontend, schemat, konektory, parser, dopasowanie,
  ekstrakcja, OCR, analiza, monitoring, wdrożenie), zbiór wzorcowy powiązań, dokumentacja, film demo i prezentacja.
- **Materiały przygotowane przed wydarzeniem:** pakiet umiejętności (skills) zespołu w `.claude/skills/`:
  `riskminer-dane-i-zrodla`, `riskminer-klasa-referencyjna`, `riskminer-czerwone-flagi`, `riskminer-ekstrakcja-przyczyn`,
  `riskminer-ewaluacja`, `riskminer-wiedza-domenowa`, `riskminer-demo-i-pitch`, `hn-*`. Z nich zaadaptowano:
  pobieranie BZP (`bzp_fetch.py`), wyrażenia z `bzp_parse.py`, łączenie po 4.5 (`bzp_join.py`), szkic klasy
  referencyjnej, wzór flag, klasyfikację przyczyn i walidację cytatów, projekt klienta LLM i test prompt injection;
  fixtures `notices_fixture_4.json` i zbiory przyczyn 26/32. Wszystko zostało przepisane na model danych tego projektu.
  Film demo powstał z zestawu `demo-video-kit` (Playwright + Remotion) przygotowanego wcześniej; sceny, napisy,
  slajdy i wygląd w `video/` powstały podczas wydarzenia.
- **Narzędzia AI użyte przy tworzeniu:** Claude Code (model Claude Opus 5.5), 6 równoległych sesji w osobnych
  worktree, do kodu, testów, dokumentacji, filmu i prezentacji. Kod przeglądał i scalał autor. W działaniu aplikacji
  model wybiera konfiguracja (domyślnie lokalny Bielik, zapasowo Anthropic API, na końcu same reguły).
- **Kod i zasoby stron trzecich:** zależności z licencjami w [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md)
  (bez GPL/AGPL); fonty w filmie: Silkscreen, Archivo, JetBrains Mono (OFL-1.1).

## Zespół

⟨imię i nazwisko⟩: całość (zespół jednoosobowy).

## Licencja

Apache-2.0 (`LICENSE`). Zależności: [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md).
