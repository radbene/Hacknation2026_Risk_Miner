// Every word of the presentation, taken from "RISK MINER – prezentacja.pdf" (numbers checked against
// docs/opis_rozwiazania.md and docs/raport_z_testu.md). Write "wodno-kanalizacyjne" in full, never the short form.
import {C} from '../theme';

export const D = {
  repo: 'github.com/radbene/Hacknation2026_Risk_Miner',
  slides: {
    title: {
      kicker: 'HackNation 2026 · wyzwanie MFiPR',
      lead: 'Cyfrowa pamięć instytucjonalna inwestycji publicznych: wydobywamy ryzyka z tego, co już się wydarzyło.',
      pilot: 'Pilotaż: wodociągi i kanalizacja · dane BZP i MFiPR',
    },
    problem: {
      kicker: 'Problem',
      head: 'Co piąta umowa zmienia termin.',
      body: '7\u00a0719 z 39\u00a0094 umów w BZP ma ogłoszoną zmianę terminu. Dlaczego, wiemy z aneksów, protokołów i ogłoszeń, ale nikt nie łączy ich z projektami ani nie korzysta z nich przy następnej inwestycji.',
      source: 'Źródło: ogłoszenia o zmianie umowy w BZP 2021–2026, policzone w bazie RISK MINER',
    },
    solution: {
      kicker: 'Rozwiązanie',
      title: 'Jedno narzędzie, trzy zadania',
      cards: [
        ['Buduje bazę sama', 'Z listy projektów odpytuje BZP, łączy postępowania, ogłoszenia, umowy i zmiany, liczy terminy i koszty.'],
        ['Znajduje zdarzenia i przyczyny', 'Opóźnienia, aneksy i kary z cytatem i kategorią R01–R15. Każda pozycja czeka na decyzję eksperta.'],
        ['Ocenia nową inwestycję', 'Podobne zakończone inwestycje, zakresy opóźnień i kosztów, czerwone flagi, działania i zapisy umowne.'],
      ] as [string, string][],
    },
    pathA: {
      kicker: 'Ścieżka A · baza doświadczeń',
      title: 'Od listy 22 projektów do bazy przypadków',
      steps: [
        ['Plik organizatora', '22 projekty KPO z numerami i NIP'],
        ['BZP na żywo', '156 zapytań do API, 952 ogłoszenia'],
        ['Łączenie', 'nr KPO, nr BZP, NIP, OCID; gdy brak: nazwa, miejsce, data, wartość'],
        ['Zdarzenia', 'reguły i Bielik, przyczyna tylko z cytatem'],
        ['Ekspert', 'zatwierdza, poprawia, odrzuca'],
      ] as [string, string][],
      numbers: [['113 tys.', 'ogłoszeń BZP'], ['45 tys.', 'postępowań'], ['39 tys.', 'umów'], ['27 tys.', 'zmian umów']] as [string, string][],
      note: '22 projekty są opracowane szczegółowo z API BZP. Pozostałe postępowania z lat 2021–2026 trafiają do bazy automatycznie i służą jako tło do porównań.',
    },
    linking: {
      kicker: 'Test łączenia',
      title: 'Każde powiązanie z uzasadnieniem',
      n1: 'projektów powiązanych z postępowaniami w BZP',
      n2: 'precyzja i kompletność na zbiorze wzorcowym: 76 ogłoszeń, 17 pułapek',
      note: 'Najpierw wspólne identyfikatory. Gdy ich brak: podobieństwo nazwy, miejsca, daty i wartości, z pewnością i listą sprawdzonych warunków.',
    },
    source: {
      kicker: 'Test źródłowy',
      title: 'Każdy fakt prowadzi do źródła',
      p1: 'Nowogard, zmiana umowy nr 1: termin +37 dni, kategoria R03 (dostęp do terenu).',
      p2: 'Przyczyna to dosłowny cytat z pkt 5.3 ogłoszenia o zmianie umowy. Kliknięcie otwiera oryginalny PDF z e-Zamówień z podświetlonym fragmentem.',
      p3: 'Bielik klasyfikuje przyczynę tylko wtedy, gdy jego cytat zgadza się ze źródłem. W bazie jest 872\u00a0tys. odnośników do źródeł.',
    },
    expert: {
      kicker: 'Człowiek w procesie',
      title: 'Ekspert ma ostatnie słowo',
      points: [
        'Najmniej pewne pozycje na górze, pewne zatwierdzisz hurtowo.',
        'Zatwierdź, popraw, odrzuć albo wskaż inne postępowanie.',
        'Ponowne przeliczenie nie nadpisuje decyzji, tylko proponuje zmianę.',
        'Katalog ryzyk, zapisy umowne i wagi edytujesz bez programisty.',
      ],
      note: 'Wszystko, co system zbudował sam, jest propozycją, dopóki ekspert jej nie oceni.',
    },
    pathB: {
      kicker: 'Ścieżka B · nowa inwestycja',
      title: 'Opis inwestycji, a w wyniku ryzyko na tle podobnych',
      steps: [
        'Wklej opis albo wgraj dokument z wniosku. Nie musi mieć warstwy tekstowej: skan odczyta OCR.',
        'Popraw cechy, które system odczytał, każdą z cytatem.',
        'Dostajesz 12 najbardziej podobnych z 12\u00a0943 zakończonych inwestycji, a przy każdej liczbie liczbę przypadków i przedział.',
      ],
    },
    similar: {
      kicker: 'Test nowej inwestycji',
      title: 'Podobieństwo, flagi i zapisy z uzasadnieniem',
      labels: [
        ['[Dane źródłowe]', '#0f766e', 'Fakt z dokumentu, zawsze z odnośnikiem.'],
        ['[Obliczenia]', '#6d28d9', 'Wynik z bazy, zawsze z liczbą przypadków.'],
        ['[Wniosek modelu]', '#b45309', 'Propozycja Bielika do akceptacji eksperta.'],
        ['Eksport', C.ink, 'Karta analizy w Word, dane w JSON i CSV.'],
      ] as [string, string, string][],
    },
    rollout: {
      kicker: 'Wdrożenie',
      title: 'Co działa i co dalej',
      cards: [
        ['Działa', ['Obie ścieżki na żywo, z eksportem.', 'Monitoring trwających inwestycji: alert po nowym ogłoszeniu w BZP.', 'Panel eksperta i wiedza ekspercka z wersjami.', 'OCR skanów (Tesseract, lokalnie).']],
        ['Bezpiecznie', ['Bielik 11B na naszym serwerze, dokumenty nie wychodzą na zewnątrz.', 'Model zmieniasz w konfiguracji; bez modelu działają same reguły.', 'Licencja Apache 2.0, bez zależności GPL.']],
        ['Dalej', ['TED, Biała lista VAT, KRS, KIO i NIK.', 'Pobieranie dokumentów z platform zakupowych.', 'Nowy sektor to nowe pliki wiedzy. Pilotaż na danych CST2021.']],
      ] as [string, string[]][],
    },
  },
};
