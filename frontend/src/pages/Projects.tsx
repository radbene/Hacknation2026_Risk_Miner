import { Link, useNavigate } from '@tanstack/react-router'
import { FileUp, RefreshCw, Search } from 'lucide-react'
import { useRef, useState } from 'react'
import { useProjects } from '@/api/cases'
import { api, isFallback, unwrap, type Schemas } from '@/api/client'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { JobRunner } from '@/components/JobRunner'
import { Completeness, LinkStatusBadge } from '@/components/LinkStatusBadge'
import { MethodConfidence } from '@/components/MethodConfidence'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { Badge, Button, DataTable, Dialog, Input, QueryState, Select, useToast, type ColumnDef } from '@/components/ui'
import { LINK_STATUS_LABEL, SUBSECTORS } from '@/lib/labels'
import { projectsRoute } from '@/router'

type P = Schemas['ProjectListItem']

const columns: ColumnDef<P>[] = [
  { accessorKey: 'code', header: 'Kod', cell: ({ row }) => (
    <Link to="/projekty/$projectId" params={{ projectId: row.original.id }} className="font-mono text-xs font-semibold text-brand hover:underline" onClick={(e) => e.stopPropagation()}>
      {row.original.code}</Link>) },
  { accessorKey: 'title', header: 'Przedsięwzięcie', cell: ({ row }) => (
    <div className="min-w-64 max-w-md"><div className="line-clamp-2 font-medium">{row.original.title}</div>
      <div className="text-xs text-slate-500">{row.original.beneficiary_name} · {row.original.voivodeship}
        {row.original.record_scope && row.original.record_scope !== 'całe postępowanie' && <Badge variant="info" className="ml-1">{row.original.record_scope}</Badge>}</div></div>) },
  { accessorKey: 'subsector_main', header: 'Podsektor', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '—')}</span> },
  { accessorKey: 'public_id_value', header: 'Identyfikator', cell: ({ row }) => (
    <div className="text-xs"><div className="text-slate-500">{row.original.public_id_type}</div><div className="flex items-center gap-1 font-mono">{row.original.public_id_value}
      <EvidenceChip ids={row.original.evidence_ids} label="xlsx" /></div></div>) },
  { accessorKey: 'link_status', header: 'Powiązanie', cell: ({ row }) => (
    <div className="flex flex-col gap-1"><LinkStatusBadge status={row.original.link_status} /><MethodConfidence method={row.original.method} confidence={row.original.confidence} compact /></div>) },
  { accessorKey: 'n_events', header: 'Zdarz.', cell: ({ getValue }) => <span className="tabular-nums">{String(getValue())}</span> },
  { accessorKey: 'n_issues', header: 'Braki', cell: ({ getValue }) => <span className="tabular-nums">{String(getValue())}</span> },
  { accessorKey: 'n_pending_review', header: 'Do przeglądu', cell: ({ getValue }) => {
    const n = Number(getValue()); return n > 0 ? <Badge variant="warning">{n}</Badge> : <span className="text-xs text-slate-400">0</span> } },
  { accessorKey: 'completeness', header: 'Kompletność', cell: ({ getValue }) => <Completeness value={getValue() as number | null} /> },
  { accessorKey: 'status', header: 'Status', cell: ({ getValue }) => <StatusBadge status={getValue() as string} /> },
]

export default function Projects() {
  const s = projectsRoute.useSearch()
  const navigate = useNavigate({ from: '/projekty' })
  const set = (patch: Partial<typeof s>) => navigate({ search: { ...s, ...patch }, replace: true })
  const q = useProjects({ q: s.q, tier: s.tier ?? 'deep', subsector: s.subsector, link_status: s.link_status, pending: s.pending })
  const [text, setText] = useState(s.q ?? '')

  return (
    <div>
      <PageHeader title="Baza przypadków" description="Projekty z pliku organizatora i automatycznie zebrane postępowania wod-kan. Każda wartość ma źródło; wszystko, co zaproponował system, czeka na decyzję eksperta."
        actions={<>
          <ImportXlsx />
          <JobRunner label="Wzbogać wszystkie" icon={<RefreshCw size={14} />} invalidate={[['projects'], ['dashboard']]}
            start={async () => unwrap(await api.POST('/api/enrich', { body: { project_ids: null, sources: null, as_of: null } }))} />
        </>} />
      <form className="mb-3 flex flex-wrap items-end gap-2" role="search" onSubmit={(e) => { e.preventDefault(); set({ q: text || undefined }) }}>
        <label className="relative">
          <span className="sr-only">Szukaj</span>
          <Search size={14} className="absolute left-2.5 top-2.5 text-slate-400" aria-hidden />
          <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="Kod, tytuł, beneficjent, NIP, numer…" className="w-72 pl-8" />
        </label>
        <Select aria-label="Warstwa" value={s.tier ?? 'deep'} onChange={(e) => set({ tier: e.target.value })}
          options={[{ value: 'deep', label: 'Warstwa pogłębiona (22)' }, { value: 'auto', label: 'Warstwa automatyczna' }]} className="w-56" />
        <Select aria-label="Podsektor" value={s.subsector ?? ''} onChange={(e) => set({ subsector: e.target.value || undefined })} placeholder="Wszystkie podsektory"
          options={SUBSECTORS.map((x) => ({ value: x, label: x }))} className="w-56" />
        <Select aria-label="Status powiązania" value={s.link_status ?? ''} onChange={(e) => set({ link_status: e.target.value || undefined })} placeholder="Każde powiązanie"
          options={Object.entries(LINK_STATUS_LABEL).map(([value, label]) => ({ value, label }))} className="w-44" />
        <label className="flex h-9 items-center gap-1.5 text-sm"><input type="checkbox" checked={!!s.pending} onChange={(e) => set({ pending: e.target.checked || undefined })} className="accent-brand" />
          Tylko do przeglądu</label>
        <Button type="submit" variant="outline">Szukaj</Button>
      </form>
      <QueryState q={q}>{(d) => (
        <>
          <p className="mb-2 text-xs text-slate-500">{d.total} rekordów</p>
          <DataTable data={d.items} columns={columns} getRowId={(r) => r.id}
            onRowClick={(r) => navigate({ to: '/projekty/$projectId', params: { projectId: r.id } })}
            rowClassName={(r) => (r.link_status === 'uncertain' ? 'bg-amber-50/50' : undefined)}
            empty="Brak projektów dla wybranych filtrów." />
        </>
      )}</QueryState>
    </div>
  )
}

function ImportXlsx() {
  const ref = useRef<HTMLInputElement>(null)
  const [report, setReport] = useState<Schemas['ImportReport'] | null>(null)
  const [busy, setBusy] = useState(false)
  const { toast } = useToast()
  async function onFile(f: File) {
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', f)
      const r = await fetch('/api/imports/xlsx?profile=organizer', { method: 'POST', body: fd, headers: { 'X-User': localStorage.getItem('rm_user') ?? '' } })
      if (r.status === 501 || r.status >= 502) throw new TypeError('mock')
      if (!r.ok) throw new Error(await r.text())
      setReport(await r.json())
    } catch (e) {
      if (isFallback(e)) setReport({ file: f.name, sha256: '(tryb demonstracyjny)', rows: 22, created: 0, updated: 0, unchanged: 22,
        issues: [{ row: 23, column: 'Identyfikator publiczny', value: '2023/BZP 00110672/01', message: 'Numer ogłoszenia nie istnieje w BZP – powiązanie przez łańcuch ogłoszeń' },
          { row: 9, column: 'Zakres rekordu', value: 'część 1', message: 'Rekord dotyczy części – łączenie po „Umowa dla części nr N”' }] })
      else toast({ kind: 'error', title: 'Import nie powiódł się', description: String(e) })
    } finally { setBusy(false); if (ref.current) ref.current.value = '' }
  }
  return (
    <>
      <input ref={ref} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} aria-label="Plik xlsx" />
      <Button variant="outline" onClick={() => ref.current?.click()} loading={busy}><FileUp size={14} />Importuj xlsx</Button>
      <Dialog open={!!report} onClose={() => setReport(null)} title="Raport importu" description={report ? `${report.file} · SHA-256 ${report.sha256}` : ''}
        footer={<Button onClick={() => setReport(null)}>OK</Button>}>
        {report && (
          <div className="text-sm">
            <div className="grid grid-cols-4 gap-2">{(['rows', 'created', 'updated', 'unchanged'] as const).map((k) => (
              <div key={k} className="rounded border border-slate-200 p-2"><div className="text-xs text-slate-500">{({ rows: 'Wiersze', created: 'Nowe', updated: 'Zmienione', unchanged: 'Bez zmian' })[k]}</div>
                <div className="text-lg font-semibold">{report[k]}</div></div>))}</div>
            <h3 className="mt-3 mb-1 font-semibold">Problemy jakości danych ({report.issues?.length ?? 0})</h3>
            <ul className="list-disc pl-5 text-xs">{(report.issues ?? []).map((i, k) => <li key={k}>wiersz {String(i.row)}, „{String(i.column)}”: {String(i.message)}</li>)}</ul>
          </div>
        )}
      </Dialog>
    </>
  )
}
