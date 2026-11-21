# Wyniki uruchomień (2026-11-16)

## flags.py na 500 prawdziwych umowach (próbka przekonwertowana `sample_to_full.py`), z tabelą referencyjną
```
Umowy: 500; z co najmniej jednym sygnalem: 158; odsetek opoznionych ogolem: 26.9%
kod | nazwa | liczba | opoznione wsrod oflagowanych
C1 | Cena ponizej 70% szacunku | 18 | 2/18 = 11%
C2 | Cena powyzej szacunku | 2 | 1/2 = 50%
C3 | Duzy rozrzut cen ofert | 17 | 5/17 = 29%
H1 | Krotki termin przy duzej wartosci | 16 | 3/16 = 19%
H2 | Planowany koniec robot ziemnych/drogowych zima | 14 | 2/14 = 14%
K1 | Jedna oferta | 13 | 4/13 = 31%
K2 | Tryb niekonkurencyjny | 15 | 2/15 = 13%
R1 | Wysokie ryzyko w klasie referencyjnej | 80 | 38/80 = 48%
Z1 | Zamawiajacy: czeste opoznienia umow | 6 | 4/6 = 67%
wynik -> odsetek opoznionych: 0 pkt: n=341, 22.6% | 1-3 pkt: n=143, 37.1% | 4-6 pkt: n=15, 26.7%
```
Dane z ogłoszeń o wyniku (liczba ofert, ceny) ma tylko 161 z 500 umów, więc flagi K1 i C1–C3 liczone są na tej części.

## Sygnały w trakcie realizacji (S1, S2) z `--asof 2026-11-21`
Dane testowe: 60 umów z próbki z usuniętym wynikiem (udają umowy w toku) i dopisaną kolumną `n_change_notices` (0, 1 albo 2). To test ścieżki kodu, nie pomiar trafności.
```
Umowy: 60; z co najmniej jednym sygnalem: 48
S1 | Termin minal, brak ogloszenia o wykonaniu | 36 | brak etykiety
S2 | Ogloszenia o zmianie umowy w trakcie realizacji | 20 | brak etykiety
{"code": "S1", "severity": 2, "evidence": "planowany koniec minal 119 dni temu; ogloszenie o wykonaniu nalezy opublikowac w 30 dni (art. 448 Pzp)"}
```

## flags.py na 3 000 umów syntetycznych
Uruchomienie bez błędów: 1 986 umów z co najmniej jednym sygnałem.
