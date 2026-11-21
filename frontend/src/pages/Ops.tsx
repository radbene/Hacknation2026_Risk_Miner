import { useNavigate } from '@tanstack/react-router'
import { Database, Download, PlayCircle } from 'lucide-react'
import { api, rawFetch, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { JobRunner } from '@/components/JobRunner'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, DataTable, QueryState, Tabs, type ColumnDef } from '@/components/ui'
import { cn, fmtDateTime, fmtNum, fmtPct } from '@/lib/utils'
import { opsRoute } from '@/router'

export default function Ops() {
  const s = opsRoute.useSearch()
  const navigate = useNavigate({ from: '/zrodla' })
  const tab = s.tab ?? 'zrodla'
  return (
    <div>
      <PageHeader title="Źródła i operacje" description="Konektory i ich stan, dziennik wszystkich zapytań do źródeł zewnętrznych, jakość dopasowania względem zbioru wzorcowego, modele językowe (gdzie przetwarzane są dane), licencje."
        actions={<>
          <JobRunner label="Zbierz warstwę automatyczną (próbka 2000)" icon={<Database size={14} />} variant="outline" invalidate={[['dashboard']]}
            start={async () => unwrap(await api.POST('/api/harvest', { body: { source: 'bzp_zip', limit: 2000, date_from: null, date_to: null } }))} />
          <Button variant="outline" onClick={async () => {
            const r = await rawFetch('/api/exports/bundle.zip'); const b = await r.blob(); const u = URL.createObjectURL(b)
            const a = document.createElement('a'); a.href = u; a.download = 'riskminer_eksport.zip'; a.click()
          }}><Download size={14} />Eksport (ZIP)</Button>
        </>} />
      <Tabs value={tab} onChange={(t) => navigate({ search: { tab: t }, replace: true })} tabs={[
        { value: 'zrodla', label: 'Konektory' }, { value: 'log', label: 'Dziennik zapytań' }, { value: 'jakosc', label: 'Jakość dopasowania' },
        { value: 'llm', label: 'Modele językowe' }, { value: 'alerty', label: 'Monitorowanie' }, { value: 'licencje', label: 'Licencje' },
      ]}>
        {tab === 'zrodla' && <Connectors />}
        {tab === 'log' && <OpLog />}
        {tab === 'jakosc' && <Quality />}
        {tab === 'llm' && <Llm />}
        {tab === 'alerty' && <Alerts />}
        {tab === 'licencje' && <Licences />}
      </Tabs>
    </div>
  )
}

function Connectors() {
  const q = useApi(['ops', 'connectors'], async () => unwrap(await api.GET('/api/ops/connectors')))
  return <QueryState q={q}>{(cs) => (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{cs.map((c) => (
      <Card key={c.code}>
        <CardHeader title={c.name} description={<span className="font-mono">{c.base_url ?? c.code}</span>}
          actions={<Badge variant={c.status === 'działa' ? (c.ok === false ? 'danger' : 'success') : 'default'}>{c.status}</Badge>} />
        <CardContent className="text-xs text-slate-600">
          <div>Licencja: {c.licence ?? '—'} · priorytet {c.tier}</div>
          <div>Ostatnio OK: {fmtDateTime(c.last_ok_at)}</div>
          {c.last_error && <div className="text-rose-700">Ostatni błąd: {c.last_error}</div>}
        </CardContent>
      </Card>))}</div>
  )}</QueryState>
}

function OpLog() {
  const q = useApi(['ops', 'log'], async () => unwrap(await api.GET('/api/ops/log', { params: { query: { limit: 300 } } })))
  return <QueryState q={q}>{(d) => (
    <>
      <p className="mb-2 text-xs text-slate-500">{d.total} operacji (pokazano ostatnie {d.items.length}). Każde zapytanie do BZP i każde wywołanie modelu jest zapisywane.</p>
      <DataTable dense data={d.items} getRowId={(r) => r.id} columns={[
        { accessorKey: 'at', header: 'Czas', cell: ({ getValue }) => <span className="whitespace-nowrap text-xs">{fmtDateTime(getValue() as string)}</span> },
        { accessorKey: 'connector', header: 'Źródło', cell: ({ getValue }) => <Badge>{String(getValue())}</Badge> },
        { accessorKey: 'operation', header: 'Operacja' },
        { accessorKey: 'params', header: 'Parametry', cell: ({ getValue }) => <code className="line-clamp-2 max-w-md text-[11px]">{JSON.stringify(getValue())}</code> },
        { accessorKey: 'status_code', header: 'HTTP', cell: ({ getValue }) => <span className={cn('tabular-nums', Number(getValue()) >= 400 && 'text-rose-700')}>{String(getValue() ?? '—')}</span> },
        { accessorKey: 'n_results', header: 'Wyników' },
        { accessorKey: 'duration_ms', header: 'ms' },
        { accessorKey: 'error', header: 'Błąd', cell: ({ getValue }) => <span className="text-xs text-rose-700">{String(getValue() ?? '')}</span> },
      ] as ColumnDef<Schemas['OpLogOut']>[]} />
    </>
  )}</QueryState>
}

function Quality() {
  const q = useApi(['ops', 'quality'], async () => unwrap(await api.GET('/api/quality')))
  return <QueryState q={q}>{(m) => {
    const l = m.linking as Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
    return (
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-4">
          {[['Precyzja', fmtPct(l.precision)], ['Czułość (recall)', fmtPct(l.recall)], ['F1', fmtNum(l.f1, 3)],
            ['Projekty w pełni poprawne', `${l.projects_fully_correct ?? '—'} / ${l.n_projects ?? '—'}`]].map(([k, v]) => (
            <Card key={k} className="p-3"><div className="text-xs text-slate-500">{k}</div><div className="text-2xl font-semibold tabular-nums">{v}</div></Card>))}
        </div>
        <p className="text-xs text-slate-500">Zbiór wzorcowy: {m.gold_set} ({l.n_gold_links ?? '—'} powiązań ogłoszeń, ręcznie zweryfikowanych; wabiki i inne części jako przykłady negatywne). Obliczono {fmtDateTime(m.computed_at)}.</p>
        {!!l.organizer_errors?.length && (
          <Card><CardHeader title="Błędy w danych organizatora wykryte podczas dopasowania" />
            <CardContent><ul className="list-disc pl-5 text-sm">{l.organizer_errors.map((e: Record<string, string>, i: number) => <li key={i}><b>{e.rm_id}</b>: {e.note}</li>)}</ul></CardContent></Card>)}
        {!!l.missed?.length && <Card><CardHeader title="Pominięte" /><CardContent><pre className="text-xs">{JSON.stringify(l.missed, null, 1)}</pre></CardContent></Card>}
      </div>
    )
  }}</QueryState>
}

function Llm() {
  const r = useApi(['settings', 'llm'], async () => unwrap(await api.GET('/api/settings/llm')))
  const u = useApi(['ops', 'llm-usage'], async () => unwrap(await api.GET('/api/ops/llm-usage')))
  return (
    <div className="space-y-4">
      <QueryState q={r}>{(d) => (
        <Card>
          <CardHeader title={`Routing modeli (tryb: ${d.mode})`} description={d.data_processing_note ?? 'Każde zadanie ma łańcuch profili; ostatni „rules” to zawsze działający tryb bez modelu.'} />
          <CardContent className="space-y-3">
            <table className="w-full text-xs"><thead className="text-left text-slate-500"><tr><th>Zadanie</th><th>Łańcuch profili</th><th>Gdzie przetwarzane</th></tr></thead>
              <tbody>{Object.entries(d.tasks).map(([t, chain]) => (
                <tr key={t} className="border-t border-slate-100"><td className="py-1 font-mono">{t}</td><td>{chain.join(' → ')}</td>
                  <td>{d.data_location_labels?.[d.task_locations?.[t] ?? ''] ?? d.task_locations?.[t] ?? '—'}</td></tr>))}</tbody></table>
            <div className="grid gap-2 md:grid-cols-3">{d.profiles.map((p) => (
              <div key={p.name} className="rounded border border-slate-200 p-2 text-xs">
                <div className="flex items-center justify-between"><b>{p.name}</b><Badge variant={p.available ? 'success' : 'default'}>{p.available ? 'dostępny' : 'niedostępny'}</Badge></div>
                <div>{p.provider} · {p.model}</div><div className="text-slate-500">{d.data_location_labels?.[p.data_location] ?? p.data_location}</div>
                {p.unavailable_reason && <div className="text-amber-700">{p.unavailable_reason}</div>}
              </div>))}</div>
          </CardContent>
        </Card>
      )}</QueryState>
      <QueryState q={u}>{(rows) => (
        <DataTable dense data={rows} empty="Brak wywołań modeli." columns={[
          { accessorKey: 'task', header: 'Zadanie' }, { accessorKey: 'provider', header: 'Dostawca' }, { accessorKey: 'model', header: 'Model' },
          { accessorKey: 'data_location', header: 'Lokalizacja danych' }, { accessorKey: 'calls', header: 'Wywołania' }, { accessorKey: 'cached', header: 'Z pamięci' },
          { accessorKey: 'errors', header: 'Błędy' }, { accessorKey: 'tokens_in', header: 'Tokeny we' }, { accessorKey: 'tokens_out', header: 'Tokeny wy' },
          { accessorKey: 'cost_usd', header: 'Koszt USD', cell: ({ getValue }) => fmtNum(getValue() as number, 4) },
        ] as ColumnDef<Schemas['LLMUsageRow']>[]} />
      )}</QueryState>
    </div>
  )
}

function Alerts() {
  const q = useApi(['ops', 'alerts'], async () => unwrap(await api.GET('/api/alerts')))
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={async () => { unwrap(await api.POST('/api/monitor/run', { body: { as_of: null } })); setTimeout(() => q.refetch(), 3000) }}>
          <PlayCircle size={14} />Sprawdź obserwowane postępowania</Button>
        <span className="text-xs text-slate-500">Nowe ogłoszenia, przekroczone terminy, „Zakończone” bez ogłoszenia o wykonaniu.</span>
      </div>
      <QueryState q={q} empty={(x) => x.length === 0}>{(as) => (
        <ul className="space-y-2">{as.map((a) => (
          <li key={a.id} className={cn('rounded border p-2 text-sm', a.read ? 'border-slate-200 bg-white' : 'border-amber-200 bg-amber-50')}>
            <Badge variant={a.severity === 'high' ? 'danger' : 'warning'}>{a.kind}</Badge> {a.message} <span className="text-xs text-slate-500">{fmtDateTime(a.created_at)}</span>
          </li>))}</ul>
      )}</QueryState>
    </div>
  )
}

function Licences() {
  const q = useApi(['ops', 'licences'], async () => unwrap(await api.GET('/api/ops/licences')))
  return <QueryState q={q}>{(ls) => (
    <DataTable dense data={ls} columns={[
      { accessorKey: 'name', header: 'Nazwa' }, { accessorKey: 'kind', header: 'Rodzaj' }, { accessorKey: 'licence', header: 'Licencja' },
      { accessorKey: 'notes', header: 'Uwagi', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '')}</span> },
    ] as ColumnDef<Schemas['LicenceOut']>[]} />
  )}</QueryState>
}
