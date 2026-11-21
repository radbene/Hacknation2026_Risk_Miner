# Wyniki uruchomień (2026-11-16)

Środowisko: Python 3.13, pandas 3.0.5, numpy 2.5.3. Powłoka tej sesji nie miała dostępu do ezamowienia.gov.pl (proxy odrzuca połączenie), więc żywe API odpytano z przeglądarki, a skrypty Pythona uruchomiono na zapisanych prawdziwych odpowiedziach i na lokalnej atrapie API.

## Co sprawdzono na żywym API (przeglądarka, fetch z origin ezamowienia.gov.pl)
- Ten sam wzorzec zapytań, którego używa `bzp_fetch.py`: `NoticeType`, `OrderType=Works`, `PublicationDateFrom/To`, `PageSize=500`, `SearchAfter=<objectId>`. Pobrano 2 318 ogłoszeń o wykonaniu umowy (5 stron) i 16 362 ogłoszenia o wyniku (33 strony) bez błędów, z odstępem 0,4–0,5 s między zapytaniami.
- Potwierdzono: `PageSize=1000` → HTTP 400; brak `NoticeType` lub dat → HTTP 400; `PageNumber` ignorowany.

## bzp_fetch.py — atrapa API na 127.0.0.1 (1 203 rekordy sklonowane z prawdziwych, 3 strony, jeden wymuszony HTTP 403)
```
2026-11-11 pobrano 0
  HTTP 403, proba 1/5, czekam 65s        (w teście z BZP_MIN_INTERVAL_S=0 bez faktycznego czekania)
2026-11-12 pobrano 1203
Razem 1203 ogloszen w /tmp/mocktest/raw/ContractPerformingNotice_Works
# drugie uruchomienie:
2026-11-11 cache (0)
2026-11-12 cache (1203)
```
NIE sprawdzono: wywołania z Pythona przeciw prawdziwemu serwerowi (TLS, nagłówki, rzeczywiste czasy). Test do wykonania na laptopie przed 21.11:
```bash
python3 scripts/bzp_fetch.py --type ContractPerformingNotice --order-type Works --from 2026-11-12 --to 2026-11-12 --out /tmp/bzp_test
python3 scripts/bzp_parse.py /tmp/bzp_test/ContractPerformingNotice_Works/2026-11-12.jsonl --out /tmp/bzp_test/c.csv
# oczekiwane: 215 ogłoszeń; odsetek label_late w okolicy 25%
```

## bzp_parse.py — 4 prawdziwe ogłoszenia z data-samples/bzp/notices_fixture_4.json
```
Zapisano 2 rekordow do /tmp/t_perf.csv (pominieto 2).
Zapisano 1 rekordow do /tmp/t_res.csv (pominieto 3).
Zapisano 1 rekordow do /tmp/t_chg.csv (pominieto 3).
```
Wybrane wartości (zgodne z treścią ogłoszeń i z niezależnym parserem w JavaScripcie użytym do zbudowania próbki):
- 2026/BZP 00534981: value 897204.9, paid 949764.56, period_days 90, on_time 0, n_changes 1, sum_changes 52559.66, label_late 1, label_cost_up 1.
- 2026/BZP 00535773: eu_funded 1, value 4410000.0, period_days 300, done 0, label_failed 1.
- 2026/BZP 00536300 (wynik): procedure_result uniewaznienie, est_value 1769286.54, n_offers 2, price_min 2127026.39, price_max 2431341.0.
- 2026/BZP 00535376 (zmiana): change_date 2026-11-02, change_basis „art. 455 ust. 1 pkt 3 ustawy", change_reason „konieczność realizacji dodatkowych robót", price_up 1.
Uwaga: ogłoszenia w próbce mają usunięte CSS i atrybuty HTML, więc białe znaki różnią się od oryginału. Parser toleruje oba warianty, ale na pełnym, niezmienionym HTML z API nie był uruchamiany.

## bzp_join.py i sample_to_full.py
```
Dolaczono cechy z ogloszen o wyniku dla 0 z 1203 umow.      (atrapa: brak pasujących numerów, ścieżka łączenia wykonana)
Zapisano 1203 wierszy, 58 kolumn do /tmp/mocktest/dataset.csv
Zapisano 500 wierszy, 38 kolumn do /tmp/dataset_sample.csv   (sample_to_full.py na prawdziwej próbce)
```
Łączenie umów z wynikami na prawdziwych danych wykonano w przeglądarce: 936 z 2 076 numerów ogłoszeń o wyniku znaleziono w oknie 25.06–25.09.2026, z czego 205 miało wiele części.
