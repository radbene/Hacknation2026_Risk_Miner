# Katalog sygnałów ryzyka

Kolumna „Związek z opóźnieniem" pochodzi z próbki 500 prawdziwych umów (odsetek ogólny 26,9%); przy małych liczebnościach to obserwacja, nie wniosek. Źródła literaturowe i przepisy: `research/zalaczniki/notatki_metody.md`, `research/05_prawo_etyka_ryzyka.md`.

| Kod | Sygnał | Reguła | Waga | Podstawa | Związek z opóźnieniem w próbce |
|---|---|---|---|---|---|
| K1 | Jedna oferta | `n_offers == 1` | 2 | Wskaźnik konkurencji: Single Market Scoreboard (Polska 2024: 56% wg KE, 35% poniżej progów wg UZP); Fazekas i Kocsis | 4 z 13 (31%) |
| K2 | Tryb niekonkurencyjny | tryb zawiera „wolnej ręki" lub „negocjacje bez ogłoszenia" | 2 | Wskaźnik CRI | 2 z 15 (13%) |
| C1 | Cena poniżej 70% szacunku | wartość umowy / (szacunek netto × 1,23) < 0,70 | 2 | Art. 224 ust. 2 Pzp: obowiązek wyjaśnień przy cenie niższej o co najmniej 30% [?: brzmienie z pamięci, sprawdź w ustawie] | 2 z 18 (11%) |
| C2 | Cena powyżej szacunku | ten sam iloraz > 1,10 | 1 | Obserwacja z danych połączonych (n=28: 25% opóźnień przy 15% ogółem w tej podgrupie) | 1 z 2 |
| C3 | Duży rozrzut cen | najwyższa/najniższa ≥ 2 przy co najmniej 3 ofertach | 1 | Hipoteza zespołu: niejasny opis przedmiotu zamówienia | 5 z 17 (29%) |
| C4 | Oferty z rażąco niską ceną | pole 6.1.7 > 0 | 1 | Art. 224 Pzp | brak w próbce |
| H1 | Krótki termin przy dużej wartości | wartość ≥ 1 mln zł i okres ≤ 90 dni | 2 | Hipoteza; w tabeli referencyjnej komórka 1–5 mln zł, 61–120 dni ma 41% opóźnień (n=92), ale do 60 dni tylko 10% (n=31) | 3 z 16 (19%) |
| H2 | Koniec robót ziemnych lub drogowych zimą | planowany koniec w XII–II, CPV 4511, 4523, 4524 | 1 | Warunki atmosferyczne jako przyczyna zmian w ogłoszeniach | 2 z 14 (14%) |
| R1 | Wysokie ryzyko w klasie referencyjnej | prognoza z tabeli ≥ 40% (waga 3 od 55%) | 2–3 | Częstość w podobnych zakończonych umowach | 38 z 80 (48%) |
| W1 | Wykonawca: częste opóźnienia | ≥ 3 inne zakończone umowy i ≥ 50% opóźnionych | 2 | Historia z ogłoszeń o wykonaniu | brak w próbce (za krótkie okno) |
| Z1 | Zamawiający: częste opóźnienia | ≥ 5 innych umów i ≥ 50% opóźnionych | 1 | Jakość przygotowania inwestycji (hipoteza) | 4 z 6 (67%) |
| S1 | Termin minął, brak ogłoszenia o wykonaniu | data oceny − planowany koniec > 30 dni i brak wyniku | 2–3 | Art. 448 Pzp: ogłoszenie w 30 dni od wykonania | nie dotyczy (próbka to umowy zakończone) |
| S2 | Ogłoszenia o zmianie umowy | liczba ogłoszeń o zmianie > 0 | 1–2 | Art. 455 Pzp; w zakończonych umowach zmiana współwystępuje z opóźnieniem | nie dotyczy |

Poziomy: 0 punktów „bez sygnałów", 1–3 „do przejrzenia", 4–6 „podwyższona uwaga", od 7 „pilne do przejrzenia".

Wniosek z próbki: sygnały konkurencji i ceny (K, C) opisują ryzyko dla uczciwości i gospodarności postępowania, a nie dla terminu. W interfejsie warto rozdzielić dwie osie: „ryzyko realizacyjne" (R, H, S, W, Z) i „sygnały z postępowania" (K, C).
