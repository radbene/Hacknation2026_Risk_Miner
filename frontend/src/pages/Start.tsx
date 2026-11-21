import { Link } from '@tanstack/react-router'
import { ArrowRight } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { BlockLabel } from '@/components/BlockLabel'
import { Card, CardContent } from '@/components/ui'
import { useAuth } from '@/lib/auth'

function Step({ n, title, children, to, cta }: { n: number; title: string; children: React.ReactNode; to?: string; cta?: string }) {
  return (
    <Card>
      <CardContent className="flex gap-3 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">{n}</div>
        <div className="min-w-0 space-y-1">
          <h2 className="font-semibold">{title}</h2>
          <div className="text-sm text-slate-600">{children}</div>
          {to && <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline">{cta}<ArrowRight size={14} aria-hidden /></Link>}
        </div>
      </CardContent>
    </Card>
  )
}

export default function Start() {
  const { isExpert } = useAuth()
  return isExpert ? <ExpertGuide /> : <UserGuide />
}

function Labels() {
  return (
    <Card className="mt-6">
      <CardContent className="space-y-2 py-4 text-sm">
        <h2 className="font-semibold">Jak czytać wyniki</h2>
        <ul className="space-y-1.5">
          <li><BlockLabel label="dane_zrodlowe" /> Fakt z dokumentu. „Źródło” otwiera dokument z zaznaczonym miejscem.</li>
          <li><BlockLabel label="obliczenia" /> Wynik policzony z bazy podobnych inwestycji, zawsze z liczbą przypadków.</li>
          <li><BlockLabel label="wniosek_modelu" /> Propozycja modelu językowego Bielik. Wymaga oceny eksperta.</li>
        </ul>
      </CardContent>
    </Card>
  )
}

function UserGuide() {
  return (
    <div className="max-w-4xl">
      <PageHeader title="Jak zacząć" description="RISK MINER pokazuje, co poszło nie tak w podobnych zakończonych inwestycjach wodno-kanalizacyjnych, i na tej podstawie ocenia ryzyko planowanej inwestycji. Dane pochodzą z Biuletynu Zamówień Publicznych." />
      <div className="space-y-3">
        <Step n={1} title="Opisz planowaną inwestycję" to="/nowa-inwestycja" cta="Nowa analiza">
          Wklej opis albo wgraj dokument (PDF, Word), np. opis z wniosku o dofinansowanie. Podaj zakres, długość sieci, wartość, czas realizacji i stan przygotowania terenu oraz decyzji.
        </Step>
        <Step n={2} title="Sprawdź odczytane cechy">
          Popraw cechy, które system źle odczytał, i odpowiedz na jego pytania, np. czy kwota jest netto czy brutto.
        </Step>
        <Step n={3} title="Przeczytaj wynik">
          Dostaniesz podobne zakończone inwestycje, częstość opóźnień i zmian umów, ocenę budżetu i harmonogramu, czerwone flagi oraz zalecane zapisy umowne. Wynik pobierzesz jako dokument Word.
        </Step>
        <Step n={4} title="Przeglądaj bazę przypadków" to="/projekty" cta="Baza przypadków">
          Każda inwestycja z bazy ma przebieg zamówień, zmiany umów, opóźnienia i ich przyczyny z odnośnikami do ogłoszeń.
        </Step>
      </div>
      <Labels />
    </div>
  )
}

function ExpertGuide() {
  return (
    <div className="max-w-4xl">
      <PageHeader title="Jak pracować w panelu eksperta" description="Powiązania, zdarzenia, przyczyny i braki danych zbudowane automatycznie są propozycjami. Do bazy jako wiarygodne trafiają po Twojej decyzji, a ponowne przeliczenie ich nie nadpisuje." />
      <div className="space-y-3">
        <Step n={1} title="Zatwierdzaj propozycje" to="/kolejka" cta="Do zatwierdzenia">
          Lista zaczyna się od pozycji, których system jest najmniej pewny. Pozycje pewne, np. powiązania po numerze ogłoszenia, zatwierdzisz hurtowo.
        </Step>
        <Step n={2} title="Poprawiaj bazę przypadków" to="/projekty" cta="Baza przypadków">
          Na karcie projektu wskażesz inne postępowanie, poprawisz kategorię ryzyka, dodasz aneks i przeliczysz zdarzenia. Każda zmiana trafia do historii.
        </Step>
        <Step n={3} title="Prowadź wiedzę ekspercką" to="/wiedza" cta="Wiedza ekspercka">
          Katalog ryzyk, listy kontrolne, zapisy umowne i wagi podobieństwa. System używa ich w każdej analizie. Każdy zapis tworzy nową wersję, którą można cofnąć.
        </Step>
        <Step n={4} title="Odświeżaj dane" to="/zrodla" cta="Źródła danych">
          Pobieranie nowych ogłoszeń z BZP, dziennik zapytań i trafność dopasowania projektów do ogłoszeń.
        </Step>
        <Step n={5} title="Wybieraj modele językowe" to="/modele" cta="Modele językowe">
          Domyślnie działa Bielik na naszym serwerze. Możesz dodać własny model bez zmian w programie.
        </Step>
      </div>
      <Labels />
    </div>
  )
}
