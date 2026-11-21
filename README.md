# RISK MINER: baza doświadczeń inwestycji publicznych, w której każdy wniosek ma źródło i akceptację eksperta

RISK MINER pozwala analitykowi instytucji wdrażającej w kilka minut zobaczyć, jak podobne zakończone inwestycje
wodno-kanalizacyjne przekroczyły koszt i termin oraz dlaczego. Dziś to wymaga ręcznego przeglądania setek ogłoszeń
BZP i dokumentów. Rozwiązanie zadania **RISK MINER** (Ministerstwo Funduszy i Polityki Regionalnej) na HackNation 2026.

**Wideo (3 min):** {{DEMO_URL}} · **Prezentacja:** [docs/prezentacja.pdf](docs/prezentacja.pdf) · **Działająca wersja:** {{APP_URL}} · **Repozytorium:** {{REPO_URL}}

Konta demonstracyjne: {{KONTA_DEMO: ekspert / analityk / admin – hasła}} (piaskownica, przycisk „Przywróć stan demo”).

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
| Pozyskanie i łączenie danych | 20% | import xlsx z dowodem dla każdej komórki; BZP (lustro + oficjalne API) i paczka 113 tys. ogłoszeń; Biała lista VAT; dopasowanie po kluczach (KPO, BZP, OCID, odwołania 4.5), częściach i kandydatach z oceną; pułapki pokazane jako alternatywy; dziennik zapytań | „Źródła”, `GET /api/ops/log`, [raport z testu](docs/raport_z_testu.md) §2, [źródła i dopasowanie](docs/zrodla_i_dopasowanie.md) |
| Dokumenty i zdarzenia | 20% | zdarzenia regułowe z pól ogłoszeń; przyczyny zmian umów (art. 455) z cytatem; fragmenty PDF/DOCX ze stroną lub akapitem; lekcje z raportów NIK | karta projektu → oś czasu → kliknięcie zdarzenia podświetla źródło |
| Nowa inwestycja | 25% | opis lub PDF → cechy z dowodem → podobne projekty z rozbiciem podobieństwa → zakresy kosztu i czasu (n, niepewność) → ocena budżetu i harmonogramu → flagi → działania i klauzule → eksport JSON/CSV/DOCX | „Nowa inwestycja”, [exports/przyklad/](exports/przyklad/) |
| Kontrola eksperta, edycja, modułowość | 20% | wszystko startuje jako „proponowane”; akceptuj / popraw / odrzuć / przepnij; historia zmian; ponowne przetwarzanie nie nadpisuje decyzji; edytor wiedzy (R01–R15, podsektory, wagi) z wersjami | „Kolejka”, „Wiedza” |
| UX, technologia, skalowalność | 15% | 5 obszarów w języku polskim; poziom `auto` z tysiącami postępowań; rejestr konektorów; routing LLM per zadanie (lokalny / UE / poza UE / bez LLM); monitoring z trybem `as_of`; docker compose na serwerze w UE | [architektura](docs/architektura.md), „Jak testować” |

## Wyniki

Liczby generuje `riskminer report` po przebiegu `riskminer demo` ([docs/raport_z_testu.md](docs/raport_z_testu.md)).

| Metryka | Wynik | Zbiór |
|---|---|---|
| Precyzja powiązań projekt → postępowanie | {{PRECYZJA}} | ręcznie zweryfikowany zbiór wzorcowy, 22 projekty, 95 wierszy (z pułapkami) |
| Kompletność (recall) powiązań | {{RECALL}} | jw. |
| Powiązania poprawne / niepewne / błędne / brakujące | {{C/U/W/M}} | jw. |
| Błędy w danych organizatora wykryte automatycznie | {{N_BLEDOW}} | lista 22 projektów |
| Przyczyny zmian umów: zgodność z oznaczeniem ręcznym | {{TRAFNOSC_PRZYCZYN}} | 26 przyczyn (zbiór wzorcowy) + 32 (zbiór kontrolny) |

## Uruchomienie

Wymagania: Docker. Klucz API nie jest potrzebny: bez klucza działa profil reguł, a zapisane odpowiedzi modelu są
odtwarzane (`LLM_MODE=replay`).

```bash
git clone {{REPO_URL}} risk-miner && cd risk-miner
cp .env.example .env && cp config/settings.example.yaml config/settings.yaml
DOMAIN=:80 HTTP_PORT=8088 docker compose --profile prod up -d --build    # http://localhost:8088
docker compose exec api riskminer demo                                   # dane demo, eksport, raport
```

Tryb deweloperski (`make up migrate api worker web`) i wdrożenie na serwer: [docs/uruchomienie.md](docs/uruchomienie.md).
Tryb z prawdziwym modelem: `ANTHROPIC_API_KEY` w `.env` i `LLM_MODE=cache`.

## Architektura

FastAPI + Postgres 16 (pgvector) + kolejka zadań w bazie + React 19. Konektory zapisują surowe odpowiedzi i dziennik
zapytań; parser DOM rozbija ogłoszenia BZP na sekcje z offsetami; moduł dopasowania buduje łańcuch z wyjaśnieniem;
ekstrakcja tworzy zdarzenia z cytatem; analiza nowej inwestycji używa klasy referencyjnej z bazy. Model językowy jest
opcjonalny i wymienny (Anthropic, OpenAI, Gemini, lokalny Bielik/PLLuM, bez LLM). Diagram: [docs/architektura.md](docs/architektura.md),
ERD: [docs/erd.md](docs/erd.md).

## Dane

Publiczne ogłoszenia BZP (informacja publiczna), Biała lista VAT, raporty NIK, lista projektów i materiały eksperckie
organizatora. Dowodem jest trwały link `ezamowienia.gov.pl`, a lustro organizatora zapisujemy tylko jako miejsce pobrania. Wykonawcy
będący osobami fizycznymi są maskowani. Do modelu językowego trafiają tylko fragmenty publicznych ogłoszeń i
dokumentów po usunięciu danych osobowych; miejsce przetwarzania pokazuje pasek w interfejsie i `config/settings.example.yaml`.

## Ograniczenia

Co działa, a co jest tylko zaprojektowane: [docs/status.md](docs/status.md) i [docs/opis_rozwiazania.md](docs/opis_rozwiazania.md).
- Dokumenty z platform zakupowych nie są pobierane automatycznie (logowanie, HTTP 429), więc trzeba je wgrać lub podać URL.
- OCR skanów i konektory TED/KRS/KIO/BK2021 są zaprojektowane, ale nie wdrożone w pełni.
- Zakresy odchyleń dla rzadkich podsektorów mają małe n; system to pokazuje i poszerza przedział.

## Wdrożenie i koszty

Jeden serwer w UE (Hetzner CX32, ok. 8 EUR/mies.) z docker compose. Możliwy serwer w urzędzie i model lokalny
(`data_location: local`). Koszt LLM na analizę: {{KOSZT_ANALIZY}} (`GET /api/ops/llm-usage`). Nowy sektor to nowe
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
  konfiguracja (domyślnie Anthropic API, profil `rules` bez LLM).
- **Kod i zasoby stron trzecich:** zależności z licencjami w [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md)
  (bez GPL/AGPL).

## Zespół

{{IMIE_NAZWISKO}}: całość (zespół jednoosobowy).

## Licencja

Apache-2.0 (`LICENSE`). Zależności: [LICENSES-THIRD-PARTY.md](LICENSES-THIRD-PARTY.md).
