# Film demo i prezentacja wideo RISK MINER

Ten katalog to projekt, z którego powstają dwa filmy:

| Plik | Co to jest | Długość |
|---|---|---|
| `out/demo.mp4` | demo działającej aplikacji: baza przypadków, panel eksperta, nowa inwestycja | ok. 1:50 |
| `out/prezentacja.mp4` | 10 slajdów prezentacji z fragmentami nagrań zamiast zrzutów ekranu | ok. 1:20 |
| `out/prezentacja.pdf` | te same slajdy jako PDF (końcowa klatka każdego slajdu) | 10 stron |

Wszystkie trzy pliki są generowane i nie trafiają do repozytorium (`out/` jest w `.gitignore`).

Zasada: **nagranie jest prawdziwe**. Playwright klika w działającą aplikację, serwer i model językowy odpowiadają naprawdę.
Czekanie na serwer może być wycięte, ale każde cięcie jest podpisane na ekranie („pominięto N s czekania”).
Montaż (kamera, zbliżenia, kursor, napisy, karty) robi Remotion na podstawie dziennika zdarzeń z nagrania,
więc po zmianie interfejsu wystarczy nagrać scenę ponownie, bez ręcznej edycji.

Projekt powstał z zestawu `demo-video-kit` (Playwright + Remotion). Opis metody: `../../demo-video-kit/docs/METHOD.md`.

## Wymagania

- Node.js 20+, FFmpeg, ok. 1 GB na zależności i przeglądarki.
- Działająca aplikacja: API (`make api`, :8040), worker (`make worker`), frontend (`make web`, :5180),
  lokalny Bielik przez Ollama (bez niego analiza działa na regułach).
- **Wolne miejsce na dysku**: nagrywanie zapisuje klatki 2560×1440 do katalogu tymczasowego, ok. 1 GB na scenę.

```bash
cd video
npm install
npx playwright-core install chromium
npm run doctor            # musi skończyć się „Ready.”
```

## Nagrywanie

```bash
DEMO_BASE=http://localhost:5180 node capture/scenes.mjs              # wszystkie sceny
DEMO_BASE=http://localhost:5180 node capture/scenes.mjs analiza      # jedna scena
npm run events -- analiza                                             # znaczniki i ostrzeżenia
```

Sceny (`capture/scenes.mjs`) zapisują `public/captures/<scena>.mp4` i `.json`:

| Scena | Co nagrywa | Skutki uboczne w bazie |
|---|---|---|
| `baza` | karta projektu Nowogard (RM-2026-020): powiązanie z BZP, zdarzenie, źródło PDF | brak |
| `ekspert` | logowanie kontem demo, kolejka, zatwierdzenie jednego zdarzenia (RM-2026-004) | zatwierdzenie; cofa je `node capture/undo.mjs` |
| `analiza` | nowa analiza z przykładowym opisem: cechy, liczenie ryzyka, wynik, flagi | nowa analiza w „Moich analizach” (API nie ma usuwania; usuń w bazie: `DELETE FROM analysis WHERE id = …`) |
| `podobne` | zakładka „Podobne inwestycje” istniejącej analizy, jeden kafelek | brak |

Po nagraniu sceny `ekspert` zawsze uruchom `node capture/undo.mjs`.

## Składanie i render

```bash
npm run typecheck
npm run stills                                   # klatki kontrolne demo → out/stills/sheet-*.jpg
npm run stills -- --id Prezentacja --every 4     # klatki kontrolne prezentacji
npm run studio                                   # podgląd w przeglądarce
npm run render                                   # → out/demo.mp4
npm run render -- out/prezentacja.mp4 --id Prezentacja
npm run qa                                       # sprawdza plik i robi arkusze → out/qa/
```

PDF prezentacji to końcowe klatki slajdów (`npm run stills -- --id Prezentacja <klatki>`) złożone w jeden plik;
numery klatek wypisuje `npm run stills -- --id Prezentacja` (mapa części).

## Gdzie co jest

| Ścieżka | Zawartość |
|---|---|
| `capture/scenes.mjs` | skrypty scen (co kliknąć, jakie znaczniki zapisać) |
| `capture/lib.mjs` | rejestrator: zwolnione tempo, kursor, przewijanie, maks. 30 klatek na sekundę nagrania |
| `src/copy.ts` | wszystkie napisy demo (po polsku, jedna linia, do ok. 60 znaków) |
| `src/scenes/` | sceny demo: oś czasu, kamera, napisy, obramowania wyliczone ze znaczników |
| `src/deck/` | prezentacja: `copy.ts` (teksty slajdów), `Deck.tsx` (slajdy, przejścia), `Clip.tsx` (wycinek nagrania) |
| `src/theme.ts`, `src/chrome.tsx` | wygląd w stylu aplikacji: papier, tusz, akcent `#3d33f2`, Silkscreen / Archivo / JetBrains Mono |
| `public/fonts/` | fonty aplikacji (OFL-1.1, z `frontend/node_modules/@fontsource*`) |

## Zasady redakcyjne

- Pisz „wodno-kanalizacyjne” (albo „wodociągi i kanalizacja”), nigdy w skrócie.
- Liczby na slajdach tylko z bazy lub z `docs/raport_z_testu.md` i `docs/opis_rozwiazania.md`.
- „12 943” to zakończone **inwestycje** (postępowania) ze znanym wynikiem, z którymi analiza porównuje
  (15 806 umów); 26 363 to wszystkie zakończone lub unieważnione postępowania z umową.
- W kadrze widać dane z publicznych ogłoszeń BZP, w tym nazwy wykonawców.

## Znane problemy

- Animowane tło aplikacji przerysowuje stronę cały czas; bez limitu klatek nagranie zapełniało dysk (limit jest w `lib.mjs`).
- Aplikacja przewija treść w `main > div.overflow-auto`, nie w oknie; `rec.scrollBy(dy, ms, selektor)` to obsługuje.
- Ekran ładowania analizy („kopalnia_ryzyka.exe”) na przewiniętej stronie wychodzi poza górną krawędź;
  scena `analiza` przewija stronę w trakcie czekania.

Remotion jest bezpłatny dla osób prywatnych i firm do trzech osób; większe firmy potrzebują licencji.
