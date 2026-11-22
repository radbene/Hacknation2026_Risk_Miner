// Every word shown in the video, in one place, in Polish (the interface's language).
// One line each: a caption longer than about 60 characters is cut off.
const seconds = (s: number) => (s < 10 ? s.toFixed(1).replace('.', ',') : String(Math.round(s)));

export const COPY = {
  brand: 'RISK MINER',
  intro: {
    kicker: 'HackNation 2026 · zadanie MFiPR',
    lead: 'Baza doświadczeń inwestycji wodno-kanalizacyjnych.',
    sub: 'Co poszło nie tak w podobnych inwestycjach, ze źródłem i oceną eksperta.',
    chips: ['Baza przypadków', 'Panel eksperta', 'Nowa inwestycja'],
  },
  /** Shown on screen after every cut that skips waiting. Keep it: it is what makes the edit honest. */
  skipped: (s: number) => `pominięto ${seconds(s)} s czekania`,
  baza: {
    tag: '1/3 · BAZA',
    card: {no: '01', title: 'Baza przypadków', sub: '22 projekty organizatora, połączone z BZP.'},
    window: 'baza_przypadkow.exe',
    open: 'Karta zakończonej inwestycji: Nowogard – Konarzewo.',
    link: 'System sam znalazł jej postępowanie w BZP…',
    reasons: '…i pokazuje dlaczego: każdy warunek ma źródło.',
    event: 'Termin przesunięty o 37 dni: brak służebności przesyłu.',
    source: 'Pokaż w źródle: oryginał z podświetlonym pkt 5.3.',
  },
  ekspert: {
    tag: '2/3 · EKSPERT',
    card: {no: '02', title: 'Panel eksperta', sub: 'Każdy wynik systemu czeka na ocenę eksperta.'},
    window: 'panel_eksperta.exe',
    login: 'Ekspert wchodzi do panelu (konto demo).',
    queue: 'Wszystko, co system zbudował, jest propozycją.',
    proposal: 'Przyczyna sklasyfikowana przez model: R02.',
    accepted: 'Zatwierdzone. Przeliczenie nie nadpisze tej decyzji.',
  },
  analiza: {
    tag: '3/3 · NOWA',
    card: {no: '03', title: 'Nowa inwestycja', sub: 'Opis planu → ryzyko na tle zakończonych umów.'},
    window: 'nowa_analiza.exe',
    paste: 'Opis planu: 6,5 km kanalizacji, 9,8 mln zł, 18 miesięcy.',
    reading: 'Odczytujemy cechy: każda wartość z cytatem z opisu.',
    features: 'Do sprawdzenia, z pytaniem o to, czego brakuje w opisie.',
    mining: 'Liczymy ryzyko na tle podobnych zakończonych umów.',
    summary: 'Ile podobnych umów się spóźniło, z n i przedziałem.',
    flags: 'Na co uważać: flagi z kategorią ryzyka R01–R15.',
    exports: 'Wynik do pobrania: karta Word, dane JSON i CSV.',
  },
  outro: {
    title: 'Wniosek bez źródła',
    title2: 'nie istnieje.',
    rows: [
      ['Baza przypadków', 'projekt → BZP → zmiany umów → przyczyny'],
      ['Panel eksperta', 'zatwierdź, popraw, odrzuć'],
      ['Nowa inwestycja', 'podobne przypadki, flagi, eksport'],
    ],
    note: 'Nagranie działającej aplikacji z lokalnym modelem Bielik. Wyniki są prawdziwe; czekanie skrócono tylko tam, gdzie jest to oznaczone.',
  },
};
