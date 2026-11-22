import { Link, useNavigate } from '@tanstack/react-router'
import { Database, Download, PlayCircle, RefreshCw } from 'lucide-react'
import { api, rawFetch, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { Intro } from '@/components/Explain'
import { JobRunner } from '@/components/JobRunner'
import { ExpertOnly } from '@/components/Layout'
import { PageHeader } from '@/components/PageHeader'
import { Fact } from '@/components/Visual'
import { Badge, Button, Card, CardContent, CardHeader, QueryState, Tabs, useToast } from '@/components/ui'
import { cn, fmtDateTime } from '@/lib/utils'
import { opsRoute } from '@/router'

const NOTICE_PL: Record<string, string> = {
  ContractNotice: 'ogłoszeń o zamówieniu', TenderResultNotice: 'ogłoszeń o wyniku', AgreementUpdateNotice: 'ogłoszeń o zmianie umowy', ContractPerformingNotice: 'ogłoszeń o wykonaniu umowy',
}
const SOURCE_HELP: Record<string, string> = {
  bzp: 'Ogłoszenia o zamówieniach, wynikach, zmianach i wykonaniu umów. Główne źródło danych o przebiegu inwestycji.',
  bzp_zip: 'Kopia ogłoszeń wodno-kanalizacyjnych z BZP z lat 2021–2026 od organizatora. Źródło inwestycji do porównań i zapas, gdy BZP nie odpowiada.',
  organizer_xlsx: 'Lista 22 projektów przekazana przez organizatora (plik Excel).',
  vat_whitelist: 'Weryfikacja NIP-ów zamawiających i wykonawców.',
  ted: 'Zamówienia powyżej progów unijnych.',
  nik: 'Wnioski z kontroli inwestycji.',
  kio: 'Spory w przetargach.',
  upload: 'Dokumenty dodane ręcznie przez eksperta (umowy, aneksy, protokoły, SWZ).',
}

export default function Ops() {
  return <ExpertOnly what="Źródła danych"><OpsInner /></ExpertOnly>
}

function OpsInner() {
  const s = opsRoute.useSearch()
  const navigate = useNavigate({ from: '/zrodla' })
  const tab = s.tab === 'llm' ? 'zrodla' : s.tab ?? 'zrodla'
  return (
    <div>
      <PageHeader title="Źródła danych"
        actions={<Button variant="outline" onClick={async () => {
          const r = await rawFetch('/api/exports/bundle.zip'); const u = URL.createObjectURL(await r.blob())
          const a = document.createElement('a'); a.href = u; a.download = 'riskminer_eksport.zip'; a.click()
        }}><Download size={14} />Pobierz eksport bazy (ZIP)</Button>} />
      <Intro can={['pobrać nowe ogłoszenia z BZP dla projektów z listy albo uzupełnić bazę porównawczą', 'sprawdzić w dzienniku każde zapytanie do źródeł i jego wynik', 'uruchomić sprawdzenie trwających inwestycji']}>
        Skąd system bierze dane i jak je aktualizuje. Ponowne pobranie niczego nie dubluje i nie nadpisuje decyzji eksperta. Modele językowe ustawisz w sekcji <Link to="/modele" className="text-brand hover:underline">Modele językowe</Link>.
      </Intro>
      <Tabs value={tab} onChange={(t) => navigate({ search: { tab: t }, replace: true })} tabs={[
        { value: 'zrodla', label: 'Źródła' }, { value: 'log', label: 'Dziennik zapytań' }, { value: 'jakosc', label: 'Trafność dopasowania' },
        { value: 'alerty', label: 'Trwające inwestycje' }, { value: 'licencje', label: 'Licencje' },
      ]}>
        {tab === 'zrodla' && <Connectors />}
        {tab === 'log' && <OpLog />}
        {tab === 'jakosc' && <Quality />}
        {tab === 'alerty' && <Alerts />}
        {tab === 'licencje' && <Licences />}
      </Tabs>
    </div>
  )
}

function Connectors() {
  const q = useApi(['ops', 'connectors'], async () => unwrap(await api.GET('/api/ops/connectors')))
  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <Card><CardContent className="space-y-2 py-4 text-sm">
          <h3 className="font-semibold">Aktualizacja 22 projektów z listy</h3>
          <p className="text-slate-600">Pobiera z BZP ogłoszenia zamawiających z listy od 2021 r., dopasowuje je do projektów i aktualizuje zdarzenia. Trwa ok. 2 minut.</p>
          <JobRunner label="Pobierz aktualne dane z BZP" icon={<RefreshCw size={14} />} invalidate={[['projects']]}
            start={async () => unwrap(await api.POST('/api/enrich', { body: { project_ids: null, sources: null, as_of: null } }))} />
        </CardContent></Card>
        <Card><CardContent className="space-y-2 py-4 text-sm">
          <h3 className="font-semibold">Baza porównawcza</h3>
          <p className="text-slate-600">Wczytuje 2000 kolejnych ogłoszeń z kopii BZP. Pełna baza jest już wczytana.</p>
          <JobRunner label="Uzupełnij bazę porównawczą" icon={<Database size={14} />} variant="outline"
            start={async () => unwrap(await api.POST('/api/harvest', { body: { source: 'bzp_zip', limit: 2000, date_from: null, date_to: null } }))} />
        </CardContent></Card>
      </div>
      <QueryState q={q}>{(cs) => (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{cs.map((c) => {
          const works = c.status === 'działa'
          return (
            <Card key={c.code}>
              <CardHeader title={c.name} actions={works ? (c.ok === false ? <Badge variant="danger">błąd</Badge> : <Badge variant="success">działa</Badge>) : <Badge>zaprojektowane</Badge>} />
              <CardContent className="space-y-1 text-sm">
                <p className="text-slate-600">{SOURCE_HELP[c.code] ?? ''}</p>
                {c.last_ok_at && <p className="text-xs text-slate-500">Ostatnie udane pobranie: {fmtDateTime(c.last_ok_at)}</p>}
                {c.last_error && <p className="text-xs text-rose-700">Ostatni problem: {c.last_error}</p>}
                {c.licence && <p className="text-xs text-slate-500">Warunki użycia: {c.licence}</p>}
              </CardContent>
            </Card>)
        })}</div>
      )}</QueryState>
    </div>
  )
}

function describe(o: Schemas['OpLogOut']): string {
  const p = (o.params ?? {}) as Record<string, unknown>
  if (o.connector === 'bzp' && o.operation === 'search') {
    const t = NOTICE_PL[String(p.NoticeType)] ?? 'ogłoszeń'
    const who = p.OrganizationName ? ` zamawiającego „${p.OrganizationName}”` : p.NoticeNumber ? ` o numerze ${p.NoticeNumber}` : ''
    const from = String(p.PublicationDateFrom ?? '').slice(0, 10), to = String(p.PublicationDateTo ?? '').slice(0, 10)
    return `Wyszukanie w BZP ${t}${who}${from ? `, ${from} – ${to}` : ''}`
  }
  if (o.connector === 'bzp_zip') return 'Wczytanie kopii BZP przekazanej przez organizatora'
  if (o.connector === 'llm' || o.connector.startsWith('llm')) return `Wywołanie modelu językowego (${o.operation})`
  return `${o.connector}: ${o.operation}`
}

function OpLog() {
  const q = useApi(['ops', 'log'], async () => unwrap(await api.GET('/api/ops/log', { params: { query: { limit: 200 } } })))
  return <QueryState q={q}>{(d) => (
    <div>
      <p className="mb-2 text-sm text-slate-600">Ostatnie {d.items.length} z {d.total.toLocaleString('pl-PL')} zapisanych operacji.</p>
      <ol className="space-y-1">{d.items.map((o) => {
        const bad = (o.status_code ?? 200) >= 400 || !!o.error
        return (
          <li key={o.id} className={cn('flex flex-wrap items-baseline gap-x-3 rounded border bg-white px-3 py-1.5 text-sm', bad ? 'border-rose-200' : 'border-slate-200')}>
            <span className="w-32 shrink-0 text-xs text-slate-500">{fmtDateTime(o.at)}</span>
            <span className="min-w-0 flex-1">{describe(o)}</span>
            <span className={cn('text-xs', bad ? 'text-rose-700' : 'text-slate-500')}>
              {bad ? `nie udało się${o.error ? `: ${o.error}` : ''}` : `${o.n_results ?? 0} wyników`}</span>
          </li>)
      })}</ol>
    </div>
  )}</QueryState>
}

function Quality() {
  const q = useApi(['ops', 'quality'], async () => unwrap(await api.GET('/api/quality')))
  return <QueryState q={q}>{(m) => {
    const l = m.linking as Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
    return (
      <div className="space-y-4">
        <p className="text-sm text-slate-600">Porównanie z ręcznie sprawdzonym przypisaniem {l.n_gold_links ?? '—'} ogłoszeń BZP do 22 projektów z listy.</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <Card className="p-4"><Fact label="Poprawne spośród wskazanych" value={<span className="text-2xl">{Math.round((l.precision ?? 0) * 100)}%</span>} hint={`${l.tp ?? 0} poprawnych, ${l.fp ?? 0} błędnych`} /></Card>
          <Card className="p-4"><Fact label="Znalezione spośród właściwych" value={<span className="text-2xl">{Math.round((l.recall ?? 0) * 100)}%</span>} hint={`${l.fn ?? 0} pominiętych`} /></Card>
          <Card className="p-4"><Fact label="Projekty dopasowane w całości poprawnie" value={<span className="text-2xl">{l.projects_fully_correct ?? '—'} z {l.n_projects ?? '—'}</span>} hint={`błędnie wskazane podobne postępowania: ${l.decoys_linked?.length ?? 0}`} /></Card>
        </div>
        {!!l.organizer_errors?.length && (
          <Card><CardHeader title="Błędy w danych organizatora wykryte przy dopasowaniu" />
            <CardContent><ul className="list-disc space-y-1 pl-5 text-sm">{l.organizer_errors.map((e: Record<string, string>, i: number) => (
              <li key={i}><b>{e.rm_id}</b>: numeru {e.notice_number} z listy nie ma w BZP. Występuje tylko jako odwołanie w innych ogłoszeniach tego postępowania i przez nie system dopasował projekt.</li>))}</ul></CardContent></Card>)}
        <p className="text-xs text-slate-500">Obliczono {fmtDateTime(m.computed_at)}.</p>
      </div>
    )
  }}</QueryState>
}

function Alerts() {
  const q = useApi(['ops', 'alerts'], async () => unwrap(await api.GET('/api/alerts')))
  const { toast } = useToast()
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">Ostrzeżenia o trwających inwestycjach: nowe ogłoszenie, termin minął bez ogłoszenia o wykonaniu, sprzeczne dane.</p>
      <Button variant="outline" onClick={async () => { try { unwrap(await api.POST('/api/monitor/run', { body: { as_of: null } })); toast({ kind: 'success', title: 'Sprawdzanie uruchomione' }); setTimeout(() => q.refetch(), 4000) } catch (e) { toast({ kind: 'error', title: 'Nie udało się', description: String(e) }) } }}>
        <PlayCircle size={14} />Sprawdź trwające inwestycje teraz</Button>
      <QueryState q={q} empty={(x) => x.length === 0}>{(as) => (
        <ul className="space-y-2">{as.map((a) => (
          <li key={a.id} className={cn('rounded border p-2 text-sm', a.read ? 'border-slate-200 bg-white' : 'border-amber-200 bg-amber-50')}>
            {a.message} <span className="text-xs text-slate-500">{fmtDateTime(a.created_at)}</span>
            {a.project_id && <Link to="/projekty/$projectId" params={{ projectId: a.project_id }} search={{}} className="ml-2 text-xs text-brand hover:underline">karta projektu</Link>}
          </li>))}</ul>
      )}</QueryState>
    </div>
  )
}

function Licences() {
  const q = useApi(['ops', 'licences'], async () => unwrap(await api.GET('/api/ops/licences')))
  const KIND: Record<string, string> = { data: 'Dane', library: 'Biblioteki programistyczne', model: 'Modele językowe' }
  return <QueryState q={q}>{(ls) => (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Żadna biblioteka nie ma licencji GPL ani AGPL.</p>
      {Object.entries(KIND).map(([k, title]) => {
        const xs = ls.filter((l) => l.kind === k)
        if (!xs.length) return null
        return (
          <section key={k}><h3 className="mb-1 text-sm font-semibold">{title} ({xs.length})</h3>
            <ul className="grid gap-1 text-sm md:grid-cols-2">{xs.slice(0, k === 'library' ? 40 : 100).map((l) => (
              <li key={l.name} className="rounded border border-slate-200 bg-white px-3 py-1.5"><b>{l.name}</b>: {l.licence}</li>))}</ul>
            {k === 'library' && xs.length > 40 && <p className="mt-1 text-xs text-slate-500">Pełna lista ({xs.length}) jest w pliku LICENSES-THIRD-PARTY.md.</p>}
          </section>)
      })}
    </div>
  )}</QueryState>
}
