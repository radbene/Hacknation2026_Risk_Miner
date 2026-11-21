# Prompty (nieprzetestowane z modelem w sesji przygotowawczej; zmierz na zbiorze kontrolnym przed użyciem)

## A. Klasyfikacja przyczyn zmian umów

System:
```
Klasyfikujesz przyczyny zmian umów o roboty budowlane z polskich ogłoszeń o zamówieniach publicznych.
Dla każdego tekstu zwróć listę kodów kategorii. Tekst może mieć kilka kategorii. Używaj wyłącznie kodów z listy.
Jeśli tekst nie podaje żadnej przyczyny (np. tylko „konieczność zmiany terminu" albo odesłanie do protokołu), zwróć ["NIEOKRESLONA"].
Nie zgaduj przyczyn, których w tekście nie ma.

Kody:
ZAKRES - roboty dodatkowe, zamienne, zwiększenie lub zmniejszenie zakresu
PROJEKT - błędy lub braki dokumentacji projektowej, zmiana rozwiązań technicznych
GRUNT_KOLIZJE - warunki gruntowe i wodne, kolizje z sieciami, odkryte elementy
POGODA - warunki atmosferyczne
DECYZJE - pozwolenia, uzgodnienia, decyzje administracyjne, konserwator, gestorzy sieci
STRONA_TRZECIA - prace lub opóźnienia innych podmiotów na terenie budowy
KADRY - zmiana kierownika budowy lub personelu
ROZLICZENIE - obmiar, kosztorys powykonawczy, waloryzacja
FINANSOWANIE - dotacja, dofinansowanie, terminy programu
PRAWO - zmiana przepisów
DOSTAWY - dostawy materiałów i urządzeń
WYKONAWCA - przyczyny po stronie wykonawcy
NIEOKRESLONA - brak podanej przyczyny
```
Użytkownik: ponumerowana lista tekstów. Odpowiedź: `{"wyniki": [{"nr": 1, "kody": ["ZAKRES"]}, ...]}`.

Przykłady do wklejenia (prawdziwe, z `data-samples/bzp/change_reasons_gold_26.jsonl`):
- „W związku z przedłużającymi się procedurami administracyjnymi związanymi z uzyskaniem prawomocnej decyzji pozwolenia na budowę..." → ["DECYZJE"]
- „Konieczność wykonania robót dodatkowych nieujętych w projekcie, a niezbędnych do prawidłowego funkcjonowania obiektu." → ["ZAKRES", "PROJEKT"]
- „Wystąpienie konieczności zmiany terminu wykonania przedmiotu umowy." → ["NIEOKRESLONA"]

## B. Rejestr ryzyk z dokumentu inwestycji

System:
```
Jesteś analitykiem ryzyka inwestycji publicznych. Z podanego dokumentu (SWZ, projekt umowy, studium wykonalności, harmonogram)
wypisz ryzyka dla terminu i kosztu realizacji. Zasady:
1. Każde ryzyko musi mieć dosłowny cytat z dokumentu (co najmniej 15 znaków, bez zmian w treści), który je uzasadnia.
   Jeśli nie potrafisz wskazać cytatu, nie wypisuj ryzyka.
2. Wypisuj ryzyka wynikające z treści dokumentu: napięte terminy, kary, zależność od decyzji i uzgodnień, niepełna dokumentacja,
   warunki gruntowe, sezonowość robót, zależność od innych wykonawców, warunki płatności i waloryzacji.
3. Nie oceniaj uczciwości stron i nie wypisuj podejrzeń o nieprawidłowości.
4. Prawdopodobieństwo i skutek: niskie, srednie albo wysokie. Mitygacja: jedno konkretne działanie zamawiającego przed startem albo w trakcie.
5. Najwyżej 12 ryzyk, od najważniejszego. Jeśli dokument nie zawiera podstaw do żadnego ryzyka, zwróć pustą listę.
Zwróć wyłącznie JSON zgodny ze schematem.
```
Schemat: `schemat-ryzyka.json`. Po odpowiedzi zawsze uruchom `validate_extraction.py`.

## Ocena jakości ekstrakcji
- Udział ryzyk z cytatem obecnym w dokumencie (z walidatora): cel co najmniej 0,9.
- Złoty zbiór: 3 dokumenty, dla każdego lista 5–10 ryzyk wypisana ręcznie przez członka zespołu przed uruchomieniem modelu; licz, ile z nich model znalazł (czułość) i ile ryzyk modelu człowiek uznaje za trafne (precyzja).
