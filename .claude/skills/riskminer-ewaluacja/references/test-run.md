# Wyniki uruchomień (2026-11-16, scikit-learn 1.9.1)

## baseline.py --preset bzp-sample na 500 prawdziwych umowach
```
- Wiersze: 499 (trening 370, test 129); podzial: losowy 75/25 grupowany po 'bid'
- Odsetek klasy 1: trening 27.0%, test 26.4%
- Cechy liczbowe: eu, period_days, value, below_eu, has_eu_no, n_offers, est_net, p_min, p_max, subc, joint, signed_month
- Cechy kategoryczne: prov, cpv, mode, size
- Wykluczone jako przeciek: done, n_changes, paid, price_up, proper, pub_day, signed
| Model | AUC | PR-AUC | Brier (baza) | P@10% | P@20% | Lift@20% | CV AUC (trening) |
| logreg | 0.632 | 0.365 | 0.194 (0.1941) | 0.385 | 0.385 | 1.46 | 0.623 +/- 0.071 |
| gboost | 0.709 | 0.461 | 0.176 (0.1941) | 0.538 | 0.385 | 1.46 | 0.66 +/- 0.039 |
Najwazniejsze cechy (gboost): period_days (+0.095), signed_month (+0.067), value (+0.044), p_min (+0.027), est_net (+0.022)
```
Pierwsze uruchomienie z podziałem czasowym po dacie zawarcia umowy dało odsetek klasy 1: trening 33,2%, test 8,0% i AUC 0,61–0,64. Stąd zmiana presetu na podział grupowany (pułapka opisana w SKILL.md).

## baseline.py --preset bzp-full
Na próbce przekonwertowanej `sample_to_full.py` (z `--group-col buyer_nip`): gboost AUC 0.701, CV 0.683 +/- 0.051; logreg AUC 0.63.
Na 3 000 umów syntetycznych (podział czasowy po `pub_date`): trening 21,7% klasy 1, test 40,4%, logreg AUC 0.576. Ten sam efekt selekcji co wyżej: umowy opóźnione są ogłaszane później.
Na danych z atrapy API (klony dwóch rekordów) skrypt zatrzymał się z komunikatem „Jedna klasa w zbiorze treningowym lub testowym", zgodnie z zamierzeniem.

## synth.py
```
Zapisano 3000 umow syntetycznych do /tmp/synth.csv; opoznione 26.4%, wzrost kosztu 26.9%
```
(prawdziwe częstości: 25,4% i 26,4%).

NIE sprawdzono: plików XLSX i Parquet (ścieżka wczytywania istnieje, ale nie była uruchomiona), danych Partnera.
