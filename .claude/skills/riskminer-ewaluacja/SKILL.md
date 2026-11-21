---
name: riskminer-ewaluacja
description: Mierzy jakość rozwiązania RISK MINER: baseline end-to-end na dowolnej tabeli (CSV, XLSX, JSON) z etykietą, metryki AUC, PR-AUC, precyzja w górnych 10% i kalibracja, plus generator danych syntetycznych. Użyj, gdy zespół prosi „policz baseline", „jaka jest trafność", „sprawdź model na danych Partnera", „zmierz, czy to działa", „wygeneruj dane testowe", „testy akceptacyjne przed demo" albo gdy jury zapowiada metrykę.
---

# riskminer-ewaluacja

## Cel
W kilka minut odpowiedzieć liczbą na pytanie „czy to działa" i mieć jeden plik `metrics.json`, z którego pochodzą wszystkie liczby na ekranie jakości i w pitchu. Definicje etykiet, wyniki bazowe i pułapki: `research/04_technologia_i_ewaluacja.md`.

## Ścieżki
Komendy uruchamiaj z katalogu głównego repozytorium, w którym leży `.claude/skills/`; dane robocze trzymaj w `data/` (utwórz katalog). Pliki `research/...` i `data-samples/...` są w pakiecie `prep/risk_miner/` repozytorium setup: instalując skille w repozytorium rozwiązania, skopiuj oba katalogi obok (np. do `docs/riskminer/`), inaczej odwołania do nich będą puste.

## Kroki
1. **Dane Partnera w nieznanym formacie** (najpierw skill wspólny `hn-dane-od-partnera`, żeby poznać kolumny):
   ```bash
   python3 .claude/skills/riskminer-ewaluacja/scripts/baseline.py --data dane.xlsx --label <kolumna_etykiety> --time-col <data> --drop <identyfikatory> --leak <kolumny_znane_po_fakcie> --out out/
   ```
   Etykieta może być 0/1 albo Tak/Nie. Skrypt sam rozpoznaje liczby (także z przecinkiem) i kategorie.
2. **Nasz zbiór z BZP:** `python3 .claude/skills/riskminer-ewaluacja/scripts/baseline.py --data data/dataset.csv --preset bzp-full --out out/`
3. **Próbka z pakietu:** `python3 .claude/skills/riskminer-ewaluacja/scripts/baseline.py --data data-samples/bzp/contracts_works_sample_500.csv --preset bzp-sample --out out/`
4. **Przeczytaj `out/report.md`.** Zanim uwierzysz w AUC powyżej 0,85, sprawdź listę cech: prawie zawsze oznacza to przeciek etykiety (kolumna znana dopiero po zakończeniu umowy).
5. **Dane syntetyczne** do testów interfejsu albo gdy nie ma sieci:
   `python3 .claude/skills/riskminer-ewaluacja/scripts/synth.py --n 5000 --table .claude/skills/riskminer-klasa-referencyjna/references/reference_table_bzp_works_2026-11.json --out data/synth.csv`
6. **Testy akceptacyjne przed demo** (lista w `research/04`, sekcja „Wystarczająco dobre do demo"): przejdź pięć punktów i zapisz wynik każdego w README rozwiązania.

## Przykład wejście → wyjście
Wejście: próbka 500 prawdziwych umów, `--preset bzp-sample`. Wyjście (`report.md`):
```
Wiersze: 499 (trening 370, test 129); podzial: losowy 75/25 grupowany po 'bid'
| gboost | AUC 0.709 | PR-AUC 0.461 | Brier 0.176 (baza 0.1941) | P@10% 0.538 | P@20% 0.385 | CV AUC 0.66 +/- 0.039 |
Najwazniejsze cechy: period_days, signed_month, value
```

## Co jest czym
- `metrics.json`: liczby do cytowania; `predictions.csv`: wiersze testowe z prawdopodobieństwami (do rankingu i wykresu kalibracji); `report.md`: tabela dla ludzi.
- Presety: `bzp-sample` (schemat skrócony z `data-samples`), `bzp-full` (wynik `bzp_join.py`, podział czasowy po dacie publikacji).

## Kiedy nie używać
- Do oceny ekstrakcji z dokumentów: tam miarą jest udział ryzyk z poprawnym cytatem i zgodność ze złotym zbiorem (`riskminer-ekstrakcja-przyczyn`).
- Gdy danych jest mniej niż około 200 wierszy z etykietą: wynik będzie szumem; pokaż tabelę referencyjną zamiast modelu.

## Pułapki
- **Podział czasowy przy krótkim oknie danych jest obciążony.** Na próbce z 12 dni podział po dacie zawarcia umowy dał 33% opóźnień w treningu i 8% w teście. Przy pełnym zbiorze używaj kohort (umowy zawarte w kwartale, obserwowane 12–18 miesięcy) albo podziału grupowanego po zamawiającym (`--group-col buyer_nip`).
- Kolumny znane po fakcie (`paid`, `n_changes`, `done_date`, `price_up`, `proper`) są w presetach wykluczone. Przy danych Partnera wskaż je sam przez `--leak`.
- AUC na 129 wierszach testowych ma błąd rzędu ±0,05. Podawaj razem z liczebnością.
- Dane syntetyczne mają realistyczne częstości, ale uproszczone zależności: model wyuczony na nich nie mówi nic o świecie.

## Zależności
pandas (BSD-3-Clause), numpy (BSD-3-Clause), scikit-learn (BSD-3-Clause); `openpyxl` (MIT) tylko do plików XLSX. Wyniki uruchomień: `references/test-run.md`.
