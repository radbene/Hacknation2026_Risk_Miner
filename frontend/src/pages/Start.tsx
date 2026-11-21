import { Link } from '@tanstack/react-router'
import { ArrowRight, BookOpen, CheckCircle2, ClipboardCheck, Cpu, Database, FileSearch, FileText, ListChecks, Plug, Sparkles } from 'lucide-react'
import { PageHeader } from '@/components/PageHeader'
import { BlockLabel } from '@/components/BlockLabel'
import { Card, CardContent } from '@/components/ui'
import { useAuth } from '@/lib/auth'

function Step({ n, icon: Icon, title, children, to, cta }: { n: number; icon: typeof Sparkles; title: string; children: React.ReactNode; to?: string; cta?: string }) {
  return (
    <Card>
      <CardContent className="flex gap-3 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">{n}</div>
        <div className="min-w-0 space-y-1">
          <h2 className="flex items-center gap-2 font-semibold"><Icon size={16} className="text-brand" />{title}</h2>
          <div className="text-sm text-slate-600">{children}</div>
          {to && <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline">{cta}<ArrowRight size={14} /></Link>}
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
        <h2 className="font-semibold">Jak czytać wyniki – trzy rodzaje informacji</h2>
        <p className="text-slate-600">Każdy blok w aplikacji ma etykietę, żebyś wiedział, na ile możesz na nim polegać:</p>
        <ul className="space-y-1.5">
          <li><BlockLabel label="dane_zrodlowe" /> fakt odczytany z dokumentu – kliknij „Źródło”, a zobaczysz oryginalny dokument z zaznaczonym miejscem.</li>
          <li><BlockLabel label="obliczenia" /> wynik policzony z bazy podobnych inwestycji – zawsze z liczbą przypadków i wyjaśnieniem „Jak to policzono?”.</li>
          <li><BlockLabel label="wniosek_modelu" /> propozycja modelu językowego (Bielik, działa na naszym serwerze) – pomocnicza, wymaga oceny eksperta.</li>
        </ul>
      </CardContent>
    </Card>
  )
}

function UserGuide() {
  return (
    <div className="max-w-4xl">
      <PageHeader title="Jak zacząć" description="RISK MINER podpowiada, co może pójść nie tak w planowanej inwestycji wodno-kanalizacyjnej – na podstawie tego, co wydarzyło się w tysiącach podobnych, już zakończonych inwestycji (dane z Biuletynu Zamówień Publicznych)." />
      <div className="space-y-3">
        <Step n={1} icon={FileText} title="Opisz planowaną inwestycję" to="/nowa-inwestycja" cta="Rozpocznij nową analizę">
          Wklej opis własnymi słowami albo wgraj dokument (PDF, DOCX) – np. opis z wniosku o dofinansowanie, program funkcjonalno-użytkowy. Im więcej szczegółów (zakres, długość sieci, wartość, czas, stan przygotowania terenu i decyzji), tym trafniejsze porównanie.
        </Step>
        <Step n={2} icon={ListChecks} title="Sprawdź odczytane cechy">
          System wypisze cechy inwestycji (podsektor, skala, wartość, czas realizacji…) – każdą z cytatem z Twojego opisu. Popraw to, co się nie zgadza, i odpowiedz na pytania (np. czy kwota jest netto czy brutto).
        </Step>
        <Step n={3} icon={Sparkles} title="Przeczytaj wynik">
          Zobaczysz najbardziej podobne zakończone inwestycje (z wyjaśnieniem, dlaczego są podobne), jak często podobne umowy się opóźniały lub drożały, czy budżet i harmonogram są realne, czerwone flagi oraz zalecane działania i zapisy umowne. Wynik pobierzesz jako dokument Word.
        </Step>
        <Step n={4} icon={Database} title="Zajrzyj do bazy przypadków" to="/projekty" cta="Przeglądaj bazę">
          Możesz obejrzeć każdą inwestycję z bazy: przebieg zamówień, zmiany umów, opóźnienia i ich przyczyny – zawsze z odnośnikiem do oryginalnego ogłoszenia.
        </Step>
      </div>
      <Labels />
      <p className="mt-4 text-xs text-slate-500">Zatwierdzanie danych, poprawki i wiedzę ekspercką obsługuje ekspert w osobnym panelu (przycisk „Zaloguj jako ekspert” w lewym dolnym rogu).</p>
    </div>
  )
}

function ExpertGuide() {
  return (
    <div className="max-w-4xl">
      <PageHeader title="Jak pracować w panelu eksperta" description="Wszystko, co system zbudował automatycznie – powiązania projektów z ogłoszeniami, zdarzenia, przyczyny, braki danych – jest propozycją. Trafia do bazy jako wiarygodne dopiero po Twojej decyzji. Twoje decyzje nie są nadpisywane, gdy system przelicza dane na nowo." />
      <div className="space-y-3">
        <Step n={1} icon={ClipboardCheck} title="Zatwierdzaj propozycje" to="/kolejka" cta="Otwórz listę do zatwierdzenia">
          Lista „Do zatwierdzenia” zaczyna od pozycji, których system jest najmniej pewny. Kliknij pozycję, aby zobaczyć podsumowanie i źródło, a potem zatwierdź, popraw lub odrzuć. Pozycje pewne (np. powiązanie po numerze ogłoszenia) zatwierdzisz hurtowo.
        </Step>
        <Step n={2} icon={FileSearch} title="Poprawiaj dane w bazie przypadków" to="/projekty" cta="Otwórz bazę przypadków">
          Na karcie projektu możesz wskazać inne postępowanie, poprawić kategorię ryzyka zdarzenia, dodać dokument (np. aneks) i przeliczyć zdarzenia. Każda zmiana trafia do historii.
        </Step>
        <Step n={3} icon={BookOpen} title="Prowadź wiedzę ekspercką" to="/wiedza" cta="Otwórz wiedzę ekspercką">
          Katalog ryzyk, listy kontrolne, klauzule umowne, wagi podobieństwa – system używa ich w każdej analizie. Zmiany zapisujesz jako nowe wersje; starą wersję można przywrócić.
        </Step>
        <Step n={4} icon={Plug} title="Odświeżaj dane ze źródeł" to="/zrodla" cta="Otwórz źródła danych">
          Pobieranie nowych ogłoszeń z BZP, dziennik zapytań i jakość dopasowania projektów do ogłoszeń.
        </Step>
        <Step n={5} icon={Cpu} title="Wybieraj modele językowe" to="/modele" cta="Otwórz modele językowe">
          Domyślnie działa Bielik na naszym serwerze. Możesz dodać własny model (np. inny serwer w instytucji) bez zmian w programie.
        </Step>
      </div>
      <Labels />
      <p className="mt-4 flex items-center gap-1 text-xs text-slate-500"><CheckCircle2 size={12} />Zatwierdzone przez Ciebie wzorcowe zdarzenia system wykorzystuje jako przykłady przy kolejnych analizach.</p>
    </div>
  )
}
