import { Link, useNavigate } from '@tanstack/react-router'
import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { BlockLabel } from '@/components/BlockLabel'
import { LoginDialog } from '@/components/Layout'
import { PixelMine } from '@/components/PixelMine'
import { Card, CardContent } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { cn } from '@/lib/utils'

function Step({ n, title, children, to, cta }: { n: number; title: string; children: React.ReactNode; to?: string; cta?: string }) {
  return (
    <Card className="h-full">
      <CardContent className="flex gap-3 py-4">
        <div className="grid h-9 w-9 shrink-0 place-items-center border-2 border-ink bg-brand font-pixel text-sm text-white">{n}</div>
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
  return (
    <div>
      <Hero />
      {isExpert ? <ExpertGuide /> : <UserGuide />}
    </div>
  )
}

/** Title, one-line pitch, a few facts and the role picker, next to the pixel-art mine. */
function Hero() {
  const { isExpert, login, logout } = useAuth()
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(false)
  const [busy, setBusy] = useState(false)
  const demo = useApi(['demo-users'], async () => unwrap(await api.GET('/api/auth/demo-users')))
  const hint = (demo.data ?? []).find((u) => u.username === 'ekspert')?.password_hint
  async function asExpert() {
    if (isExpert) return navigate({ to: '/kolejka' })
    if (!hint) return setDialog(true)
    setBusy(true)
    try { await login('ekspert', hint); navigate({ to: '/kolejka' }) } catch { setDialog(true) } finally { setBusy(false) }
  }
  function asUser() { if (isExpert) logout(); navigate({ to: '/nowa-inwestycja' }) }
  return (
    <section className="mb-10 grid items-center gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:gap-12">
      <div className="min-w-0">
        <h1 className="font-pixel text-[44px] leading-[0.95] text-brand sm:text-[64px] xl:text-[76px]">Risk<br />Miner</h1>
        <p className="mt-4 max-w-xl text-lg font-semibold text-ink sm:text-xl">Baza doświadczeń z inwestycji wodno-kanalizacyjnych: wydobywamy ryzyka z tego, co już się wydarzyło.</p>
        <ul className="mt-4 space-y-1 font-mono text-[13px] text-slate-700">
          <li>&gt; źródło: Biuletyn Zamówień Publicznych i dane MFiPR</li>
          <li>&gt; pilotaż: wodociągi i kanalizacja, projekty KPO</li>
          <li>&gt; model językowy: Bielik, na naszym serwerze</li>
        </ul>
        <div className="mt-6 max-w-xl border-2 border-ink bg-surface shadow-md">
          <div className="flex items-center gap-3 border-b-2 border-ink px-3 py-1.5">
            <span className="h-3 w-3 border-2 border-ink" aria-hidden />
            <span className="font-mono text-xs font-semibold">wybierz_role.exe</span>
            <span className="stripes h-3 flex-1" aria-hidden />
          </div>
          <div className="grid gap-3 p-4 sm:grid-cols-2">
            <RoleButton active={!isExpert} onClick={asUser} title="Analityk" desc="Oceń ryzyko planowanej inwestycji" />
            <RoleButton active={isExpert} onClick={asExpert} busy={busy} title="Ekspert" desc="Zatwierdzaj dane i prowadź wiedzę" />
          </div>
          {hint && !isExpert && <p className="border-t-2 border-dashed border-ink/30 px-4 py-2 font-mono text-[11px] text-slate-600">Demo: panel eksperta otwiera się bez hasła.</p>}
        </div>
      </div>
      <div className="mx-auto w-full max-w-md lg:max-w-none">
        <div className="border-2 border-ink bg-surface p-4 shadow-lg sm:p-6"><PixelMine /></div>
      </div>
      <LoginDialog open={dialog} onClose={() => setDialog(false)} />
    </section>
  )
}

function RoleButton({ title, desc, onClick, active, busy }: { title: string; desc: string; onClick: () => void; active?: boolean; busy?: boolean }) {
  return (
    <button type="button" onClick={onClick} disabled={busy} aria-pressed={active}
      className={cn('press flex cursor-pointer flex-col items-start gap-0.5 border-2 border-ink px-4 py-3 text-left shadow-sm hover:shadow-md disabled:opacity-60',
        active ? 'bg-brand text-white' : 'bg-white text-ink')}>
      <span className="flex w-full items-center justify-between font-mono text-sm font-bold uppercase tracking-wide">{title}<ArrowRight size={15} aria-hidden /></span>
      <span className={cn('text-xs', active ? 'text-white/85' : 'text-slate-600')}>{desc}</span>
    </button>
  )
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
    <div>
      <PageHeader title="Jak zacząć" description="RISK MINER pokazuje, co poszło nie tak w podobnych zakończonych inwestycjach wodno-kanalizacyjnych, i na tej podstawie ocenia ryzyko planowanej inwestycji. Dane pochodzą z Biuletynu Zamówień Publicznych." />
      <div className="grid gap-4 md:grid-cols-2">
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
    <div>
      <PageHeader title="Jak pracować w panelu eksperta" description="Powiązania, zdarzenia, przyczyny i braki danych zbudowane automatycznie są propozycjami. Do bazy jako wiarygodne trafiają po Twojej decyzji, a ponowne przeliczenie ich nie nadpisuje." />
      <div className="grid gap-4 md:grid-cols-2">
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
