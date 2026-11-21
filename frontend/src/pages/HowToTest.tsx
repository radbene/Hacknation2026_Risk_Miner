import { Link } from '@tanstack/react-router'
import { useProjects } from '@/api/cases'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Card, CardContent, CardHeader } from '@/components/ui'

function ProjectLink({ code, tab, children }: { code: string; tab?: string; children?: React.ReactNode }) {
  const q = useProjects({ q: code, tier: 'deep' })
  const p = q.data?.items.find((x) => x.code === code)
  if (!p) return <span className="font-mono">{code}</span>
  return <Link to="/projekty/$projectId" params={{ projectId: p.id }} search={{ tab }} className="font-mono text-brand hover:underline">{children ?? code}</Link>
}

const STEP = 'list-decimal space-y-1.5 pl-5 text-sm'

export default function HowToTest() {
  return (
    <div className="max-w-4xl">
      <PageHeader title="Scenariusze testowe" description="Scenariusze odpowiadające kryteriom oceny. Część kroków wykonuje użytkownik (bez logowania), część ekspert – zaloguj się przyciskiem „Zaloguj jako ekspert” w lewym dolnym rogu (wersja demonstracyjna: login ekspert, hasło demo-riskminer)." />
      <div className="space-y-4">
        <Card>
          <CardHeader title={<>1. Integracja danych <Badge>20%</Badge></>} />
          <CardContent><ol className={STEP}>
            <li>Jako ekspert: <Link to="/projekty" search={{}} className="text-brand hover:underline">Baza przypadków</Link> → „Importuj listę projektów (Excel)” – raport: ile wierszy, nowe / zmienione / bez zmian oraz wartości do sprawdzenia. Ponowny import tego samego pliku niczego nie dubluje.</li>
            <li>Jako ekspert: „Pobierz aktualne dane z BZP” – zapytania na żywo do Biuletynu Zamówień Publicznych; każde zapytanie widać w <Link to="/zrodla" search={{ tab: 'log' }} className="text-brand hover:underline">Źródła danych → Dziennik zapytań</Link>.</li>
            <li>Na karcie projektu zakładka „Ogłoszenia BZP tej inwestycji”: jak dopasowano (po numerze projektu KPO, numerze ogłoszenia, odwołaniach między ogłoszeniami albo po podobieństwie) i lista warunków ✓/✗ ze źródłami. Trafność względem ręcznie sprawdzonego zbioru: <Link to="/zrodla" search={{ tab: 'jakosc' }} className="text-brand hover:underline">Źródła danych → Trafność dopasowania</Link>.</li>
            <li>Kompletność łańcucha: <ProjectLink code="RM-2026-001" tab="os" /> (Oława), część zamówienia: <ProjectLink code="RM-2026-008" tab="powiazania" />, dwie zmiany umowy: <ProjectLink code="RM-2026-020" tab="umowy" /> (Nowogard).</li>
            <li>Błąd w danych organizatora: <ProjectLink code="RM-2026-022" tab="powiazania" /> (Wolin) – numer z xlsx nie istnieje w BZP; powiązanie przez łańcuch ogłoszeń, wabik pokazany jako odrzucona alternatywa.</li>
          </ol></CardContent>
        </Card>
        <Card>
          <CardHeader title={<>2. Dokumenty i zdarzenia <Badge>20%</Badge></>} />
          <CardContent><ol className={STEP}>
            <li><ProjectLink code="RM-2026-020" tab="zdarzenia">Nowogard → Zdarzenia</ProjectLink>: zmiana 1 – służebność przesyłu (R03), zmiana 2 – warunki gruntowe i wody gruntowe (R02), wykonanie 185 dni po terminie; każda pozycja z cytatem i źródłem (link stały do e-Zamówień, sekcja ogłoszenia).</li>
            <li>„Źródło” przy każdej wartości: cytat, lokalizacja (sekcja / strona / akapit / komórka xlsx), data pobrania; przy obliczeniach – dane wejściowe i wzór.</li>
            <li>Jako ekspert, zakładka „Dokumenty”: dodaj PDF/DOCX (np. aneks, SWZ) – tekst z numerami stron i fragmenty ryzyka; „Przelicz zdarzenia” pokazuje, co nowego, co bez zmian, co zmienione.</li>
            <li>„Braki i sprzeczności”: cztery stany eksperta (nie ma w paczce / dokument nie wspomina / brak potwierdzenia / potwierdzono, że nie wykonano) i co uzupełnić.</li>
          </ol></CardContent>
        </Card>
        <Card>
          <CardHeader title={<>3. Kontrola eksperta <Badge>20%</Badge></>} />
          <CardContent><ol className={STEP}>
            <li>Zaloguj się jako ekspert → <Link to="/kolejka" search={{}} className="text-brand hover:underline">Do zatwierdzenia</Link>: najmniej pewne pozycje na górze; kliknij pozycję, zobacz źródło z zaznaczonym fragmentem, zatwierdź / popraw / odrzuć z uzasadnieniem; „Zatwierdź pewne pozycje hurtowo”.</li>
            <li>Na karcie <ProjectLink code="RM-2026-022" tab="powiazania">Wolin</ProjectLink> „Wskaż inne postępowanie” – decyzja eksperta przetrwa ponowne pobranie danych z BZP.</li>
            <li>Popraw kategorię ryzyka zdarzenia – po ponownej analizie system nie nadpisze decyzji, pokaże najwyżej „propozycję zmiany”.</li>
            <li><Link to="/wiedza" search={{}} className="text-brand hover:underline">Wiedza ekspercka</Link>: edytuj tabelę (np. wagi podobieństwa, klauzule) → nowa wersja; „Wersje” → przywróć. Zakładka „Historia” na karcie projektu.</li>
          </ol></CardContent>
        </Card>
        <Card>
          <CardHeader title={<>4. Analiza nowej inwestycji <Badge>25%</Badge></>} />
          <CardContent><ol className={STEP}>
            <li>Jako użytkownik: <Link to="/nowa-inwestycja" className="text-brand hover:underline">Nowa analiza</Link> – wklej opis lub wgraj dokument → „Odczytaj cechy” (każda z cytatem; pytanie o netto/brutto, gdy nie podano).</li>
            <li>„Analizuj ryzyko” → podsumowanie (czy zdąży na czas, o ile dni bywały opóźnienia, czy budżet jest realny); „Podobne inwestycje” z wyjaśnieniem podobieństwa cecha po cesze; „Pomiń w porównaniu” przelicza wyniki.</li>
            <li>„Budżet i harmonogram”: percentyl budżetu i czasu na tle sąsiadów, koszt na km / RLM, rezerwa P80; „Zakresy z bazy” z poziomem odniesienia (sąsiedzi → podsektor → wod-kan).</li>
            <li>„Czerwone flagi” – każda z uzasadnieniem (historia sąsiadów, zakresy, zdania z opisu, lista kontrolna eksperta) i „Działania i klauzule” (podstawa prawna). Eksport karty: DOCX, JSON, CSV.</li>
          </ol></CardContent>
        </Card>
        <Card>
          <CardHeader title={<>5. Skalowalność <Badge>15%</Badge></>} />
          <CardContent><ul className="list-disc space-y-1.5 pl-5 text-sm">
            <li>Baza porównawcza: ok. 34 tys. postępowań wod-kan 2021–2026 z kopii BZP (w Bazie przypadków wybierz „Postępowania pobrane z BZP”).</li>
            <li>Nowy sektor = nowy katalog <code>knowledge/&lt;sektor&gt;/</code> (import z dokumentu eksperta), bez zmian w kodzie; rejestr konektorów; routing modeli z trybem bez modelu.</li>
            <li>Wiersz poleceń: <code>riskminer demo</code> odtwarza cały przebieg od pustej bazy; drugi przebieg nie tworzy duplikatów.</li>
          </ul></CardContent>
        </Card>
      </div>
    </div>
  )
}
