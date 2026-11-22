# RISK MINER: baza doświadczeń inwestycji publicznych, w której każdy wniosek ma źródło i akceptację eksperta

RISK MINER pozwala analitykowi instytucji wdrażającej w kilka minut zobaczyć, jak podobne zakończone inwestycje
wodno-kanalizacyjne przekroczyły koszt i termin oraz dlaczego. Dziś to wymaga ręcznego przeglądania setek ogłoszeń
BZP i dokumentów. Rozwiązanie zadania **RISK MINER** (Ministerstwo Funduszy i Polityki Regionalnej) na HackNation 2026.

**Wideo (3 min):** ⟨link do filmu⟩ · **Prezentacja:** [docs/prezentacja.pdf](docs/prezentacja.pdf) · **Działająca wersja:** ⟨link do aplikacji⟩ · **Repozytorium:** https://github.com/radbene/Hacknation2026_Risk_Miner

Konta demonstracyjne: bez logowania pracujesz jako analityk; panel eksperta: `ekspert` / `demo-riskminer` (w wersji demo jednym kliknięciem na stronie startowej). Pozostałe konta: `admin`, `analityk`, `gosc` (tylko odczyt), to samo hasło. Stan demo przywraca `POST /api/admin/reset-demo` (konto `admin`, tryb `DEMO_MODE`).

## Dla kogo i jaki problem rozwiązuje

- **Użytkownik:** analityk i ekspert instytucji przygotowującej lub oceniającej inwestycję wod-kan (IZ/IP, beneficjent).
- **Problem dziś:** wiedza o opóźnieniach, aneksach i ich przyczynach jest rozproszona w ogłoszeniach o zmianie i o
  wykonaniu umowy w BZP oraz w dokumentach, bez powiązań z projektami i bez kategorii ryzyka.
- **Co zmienia rozwiązanie:** automatycznie buduje łańcuch projekt → postępowania → ogłoszenia → umowa → zmiany →
  zdarzenia R01–R15 z cytatem i linkiem do źródła, a dla nowej inwestycji podaje podobne przypadki, zakresy odchyleń
  (z liczebnością próby), flagi, działania i klauzule. Ekspert zatwierdza każdy wynik.

## Jak spełniamy kryteria

| Kryterium | Waga | Co zrobiliśmy | Gdzie to zobaczyć |
|---|---|---|---|
| Pozyskanie i łączenie danych | 20% | import xlsx z dowodem dla każdej komórki; BZP na żywo (oficjalne API, 156 zapytań, 952 ogłoszenia dla 22 projektów) i kopia BZP organizatora (113 tys. ogłoszeń); dopasowanie po kluczach (KPO, BZP, NIP, OCID, odwołania 4.5), częściach i kandydatach z oceną; pułapki pokazane jako alternatywy; dziennik zapytań; wgrywanie dokumentów PDF/DOCX/XLSX/CSV | „Źródła danych”, `GET /api/ops/log`, [raport z testu](docs/raport_z_testu.md) §2, [źródła i dopasowanie](docs/zrodla_i_dopasowanie.md) |
| Dokumenty i zdarzenia | 20% | zdarzenia regułowe z pól ogłoszeń; przyczyny zmian umów (art. 455) klasyfikowane przez Bielika tylko z cytatem sprawdzonym w źródle; protokoły i aneksy PDF/DOCX: nowy termin, koszt i przyczyna z cytatem, sygnały ryzyka ze stroną lub akapitem | karta projektu → „Zdarzenia i przyczyny” → „Pokaż w źródle” otwiera oryginał z podświetlonym fragmentem |
| Nowa inwestycja | 25% | opis lub PDF → cechy z dowodem → podobne projekty z rozbiciem podobieństwa → zakresy kosztu i czasu (n, niepewność) → ocena budżetu i harmonogramu → flagi → działania, klauzule i wzorcowe przypadki zatwierdzone przez eksperta → eksport JSON/CSV/DOCX | „Nowa analiza”, [exports/przyklad/](exports/przyklad/) |
| Kontrola eksperta, edycja, modułowość | 20% | wszystko startuje jako „proponowane”; akceptuj / popraw / odrzuć / przepnij / oznacz jako wzorcowe; historia zmian; ponowne przetwarzanie nie nadpisuje decyzji; edytor wiedzy (R01–R15, podsektory, wagi) z wersjami; własny model językowy dodawany w konfiguracji | „Do zatwierdzenia”, „Wiedza ekspercka”, „Modele językowe” |
| UX, technologia, skalowalność | 15% | interfejs po polsku z rolami analityka i eksperta, objaśnieniami i słowniczkiem, działa na telefonie; poziom `auto` z 45 tys. postępowań; rejestr konektorów; routing LLM per zadanie (lokalny / UE / poza UE / bez LLM); monitoring z trybem `as_of`; docker compose | [architektura](docs/architektura.md), „Scenariusze testowe” |

## Wyniki

Liczby generuje `riskminer report` po przebiegu `riskminer demo` ([docs/raport_z_testu.md](docs/raport_z_testu.md)).

| Metryka | Wynik | Zbiór |
|---|---|---|
| Precyzja powiązań projekt → postępowanie | 1,0 | ręcznie zweryfikowany zbiór wzorcowy, 22 projekty, 95 wierszy (z pułapkami) |
| Kompletność (recall) powiązań | 1,0 | jw. |
| Powiązania poprawne / niepewne / błędne / brakujące | 22 / 0 / 0 / 0 | jw. |
| Błędy w danych organizatora wykryte automatycznie | 1 błędny numer ogłoszenia BZP (Wolin, RM-2026-022) i 161 braków danych | lista 22 projektów |
| Przyczyny zmian umów: zgodność z oznaczeniem ręcznym (reguły, F1) | 0,93 (zbiór wzorcowy) · 0,87 (zbiór kontrolny) | 26 przyczyn (zbiór wzorcowy) + 32 (zbiór kontrolny) |

## Uruchomienie

Wymagania: Docker. Klucz API nie jest potrzebny: bez klucza działa profil reguł, a zapisane odpowiedzi modelu są
odtwarzane (`LLM_MODE=replay`).

```bash
git clone https://github.com/radbene/Hacknation2026_Risk_Miner.git risk-miner && cd risk-miner
cp .env.example .env && cp config/settings.example.yaml config/settings.yaml
DOMAIN=:80 HTTP_PORT=8088 docker compose --profile prod up -d --build    # http://localhost:8088
docker compose exec api riskminer demo                                   # dane demo, eksport, raport
```

Tryb deweloperski (`make up migrate api worker web`) i wdrożenie na serwer: [docs/uruchomienie.md](docs/uruchomienie.md).
Tryb z modelem: domyślnie lokalny Bielik 11B v3.0 przez Ollama (`docker compose --profile bielik`, wymaga GPU, [docs/hosting.md](docs/hosting.md)); zapasowo `ANTHROPIC_API_KEY` w `.env`; bez modelu działają same reguły.

## Architektura

FastAPI + Postgres 16 (pgvector) + kolejka zadań w bazie + React 19. Konektory zapisują surowe odpowiedzi i dziennik
zapytań; parser DOM rozbija ogłoszenia BZP na sekcje z offsetami; moduł dopasowania buduje łańcuch z wyjaśnieniem;
ekstrakcja tworzy zdarzenia z cytatem; analiza nowej inwestycji używa klasy referencyjnej z bazy. Model językowy jest
opcjonalny i wymienny w konfiguracji: lokalny Bielik przez Ollama (domyślnie), dowolny model zgodny z API OpenAI, Anthropic, Gemini albo bez LLM. Diagram: [docs/architektura.md](docs/architektura.md),
ERD: [docs/erd.md](docs/erd.md).

## Dane

Publiczne ogłoszenia BZP (informacja publiczna), lista projektów, dokumenty i materiały eksperckie
organizatora. Dowodem jest trwały link `ezamowienia.gov.pl`, a lustro organizatora zapisujemy tylko jako miejsce pobrania. Wykonawcy
będący osobami fizycznymi są maskowani. Do modelu językowego trafiają tylko fragmenty publicznych ogłoszeń i
dokumentów po usunięciu danych osobowych; miejsce przetwarzania pokazuje pasek w interfejsie i `config/settings.example.yaml`.

## Ograniczenia

Co działa, a co jest tylko zaprojektowane: [docs/status.md](docs/status.md) i [docs/opis_rozwiazania.md](docs/opis_rozwiazania.md).
- Dokumenty z platform zakupowych nie są pobierane automatycznie (logowanie, HTTP 429), więc trzeba je wgrać lub podać URL.
- OCR skanów oraz źródła TED, Biała lista VAT, KRS, KIO, BK2021 i raporty NIK są zaprojektowane, ale nie wdrożone; skan bez warstwy tekstowej jest zapisywany i oznaczany do OCR.
- Zakresy odchyleń dla rzadkich podsektorów mają małe n; system to pokazuje i poszerza przedział.

## Wdrożenie i koszty

Jeden serwer w UE (Hetzner CX32, ok. 8 EUR/mies.) z docker compose. Możliwy serwer w urzędzie i model lokalny
(`data_location: local`). Koszt LLM na analizę: 0 zł przy lokalnym Bieliku (płacimy tylko za serwer z GPU, np. Scaleway L4 w Warszawie, [docs/hosting.md](docs/hosting.md)); zużycie: `GET /api/ops/llm-usage`. Nowy sektor to nowe
pliki wiedzy (`knowledge/<sektor>/`) generowane z dokumentów eksperta.

## Ujawnienie

- **Co powstało podczas hackathonu:** cała aplikacja (backend, frontend, schemat, konektory, parser, dopasowanie,
  ekstrakcja, analiza, monitoring, wdrożenie), zbiór wzorcowy powiązań i dokumentacja.
- **Materiały przygotowane przed wydarzeniem:** pakiet umiejętności (skills) zespołu w `.claude/skills/`:
  `riskminer-dane-i-zrodla`, `riskminer-klasa-referencyjna`, `riskminer-czerwone-flagi`, `riskminer-ekstrakcja-przyczyn`,
  `riskminer-ewaluacja`, `riskminer-wiedza-domenowa`, `riskminer-demo-i-pitch`, `hn-*`. Z nich zaadaptowano:
  pobieranie BZP (`bzp_fetch.py`), wyrażenia z `bzp_parse.py`, łączenie po 4.5 (`bzp_join.py`), szkic klasy
  referencyjnej, wzór flag, klasyfikację przyczyn i walidację cytatów, projekt klienta LLM i test prompt injection;
  fixtures `notices_fixture_4.json` i zbiory przyczyn 26/32. Wszystko zostało przepisane na model danych tego projektu.
- **Narzędzia AI użyte przy tworzeniu:** Claude Code (model Claude Opus 5.5), 6 równoległych sesji w osobnych
  worktree, do kodu, testów i dokumentacji. Kod przeglądał i scalał autor. W działaniu aplikacji model wybiera
  konfiguracja (domyślnie lokalny Bielik, zapasowo Anthropic API, na końcu same reguły).
- **Kod i zasoby stron trzecich:** zależności z licencjami w [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md)
  (bez GPL/AGPL).

## Zespół

⟨imię i nazwisko⟩: całość (zespół jednoosobowy).

## Licencja

Apache-2.0 (`LICENSE`). Zależności: [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md).
