---
name: riskminer-demo-i-pitch
description: Scenariusz demo, pitch i odpowiedzi na pytania jury specyficzne dla zadania RISK MINER i Ministerstwa Funduszy i Polityki Regionalnej: zdanie otwierające, kolejność ekranów, słowa do użycia i do unikania, argumenty o wdrażalności. Użyj, gdy zespół prosi „przygotuj demo", „napisz pitch dla ministerstwa", „jakie pytania zada jury", „jak to powiedzieć urzędnikowi", „scenariusz wideo".
---

# riskminer-demo-i-pitch

## Cel
Jury ma kilka minut na rozwiązanie. Ma zapamiętać jedno zdanie i jedną liczbę oraz zobaczyć, że narzędzie działa na prawdziwych danych. Ogólne zasady pitchu i zgłoszenia są w skillach wspólnych `hn-pitch-final` i `hn-zgloszenie`; tu jest tylko to, co dotyczy tego Partnera.

## Źródła
Scenariusz wideo, plan finału i 10 pytań z odpowiedziami: `research/07_plan_24h_i_demo.md`. Problem Partnera i jego słownictwo: `research/01`. Kontrargumenty: `research/06`. Czerwone linie języka: `research/05`, sekcja (c).

## Kroki
1. **Odśwież liczby.** Wszystkie liczby w narracji pochodzą z tabeli referencyjnej. Po przebudowie tabeli na pełnym zbiorze uruchom prognozę dla przykładu demo i podmień liczby w scenariuszu (plik 07 ma wersję z listopadowej próbki).
2. **Zdanie otwierające** (wariant do dopasowania): „Co czwarta umowa na roboty budowlane w Polsce kończy się po terminie, a przy umowach za kilka milionów złotych prawie co druga. To wiadomo z publicznych ogłoszeń. Pokazujemy to planującemu, zanim podpisze harmonogram."
3. **Kolejność ekranów:** kreator inwestycji → przyczyny z przykładami → portfel umów w toku → „Skąd te liczby". Nigdy nie zaczynaj od architektury.
4. **Inwestycja od jury.** W finale poproś jury o wartość i okres dowolnej inwestycji i policz na żywo. To najmocniejszy dowód, że to nie makieta.
5. **Pytania.** Przećwicz 10 pytań z pliku 07 na głos. Odpowiedź ma dwie części: liczba albo fakt, potem ograniczenie.
6. **Na koniec prośba o konkret:** wyciąg z CST2021 z NIP beneficjenta i datami dla jednego programu, miesiąc pilotażu w jednej instytucji zarządzającej.

## Słowa
| Mów | Nie mów |
|---|---|
| sygnał do przejrzenia, podwyższona uwaga | podejrzany, nieuczciwy, wyłudzenie |
| zadeklarowano opóźnienie | wykonawca zawalił termin |
| w podobnych zakończonych umowach | przewidujemy, że ten projekt się opóźni |
| ryzyko realizacyjne (termin, koszt) | ryzyko korupcji |
| uzupełnia Arachne i kontrole krzyżowe | zastępuje Arachne |
| instytucja zarządzająca, beneficjent, analiza ryzyka, próba kontrolna | „urząd", „klient", „scoring" |

## Argumenty o wdrażalności (specyficzne dla tego Partnera)
- Działa na danych publicznych, więc pilotaż nie wymaga integracji z CST2021 ani zgód na dane.
- Wytyczne dotyczące kontroli wymagają pisemnej analizy ryzyka i prób opartych na ryzyku (plik 01); narzędzie daje do niej liczby z odesłaniem do źródeł.
- Rdzeń nie używa modelu językowego, więc nie ma problemu z miejscem przetwarzania danych (plik 05).
- Licencje zależności są permisywne (BSD, MIT, Apache-2.0), co ułatwia przekazanie praw.
- Uczciwie zmierzona jakość i jawne ograniczenia budują zaufanie bardziej niż obietnica „AI przewidzi".

## Przykład wejście → wyjście
Prośba: „Napisz 20 sekund o tym, czym różnimy się od Arachne." Odpowiedź: „Arachne szuka ryzyka nadużyć i konfliktu interesów na danych instytucji. My pokazujemy ryzyko terminu i kosztu na danych publicznych. Sprawdziliśmy na prawdziwych umowach, że klasyczne flagi nadużyć, takie jak jedna oferta, nie przewidują opóźnień, więc to dwa różne pytania i dwa uzupełniające się narzędzia."

## Kiedy nie używać
Do README rozwiązania, opisu w HackTribe i listy materiałów przygotowanych wcześniej: `hn-zgloszenie`.

## Pułapki
- Liczby z próbki 12 dni nie mogą trafić do finału jako „dane o Polsce": najpierw pełny zbiór.
- Nie pokazuj nazw wykonawców będących osobami fizycznymi; w demo używaj umów spółek i jednostek publicznych albo ukryj nazwy.
- Czas pitchu nie jest podany przez organizatora; przygotuj wersję na 3 i na 5 minut.
- Relacja z 2025 r. mówi, że jury prosiło o demo na żywo (plik 02): miej aplikację uruchomioną lokalnie bez sieci.

## Zależności
Brak (sam tekst).
