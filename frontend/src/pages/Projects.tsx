import { Link, useNavigate } from '@tanstack/react-router'
import { CalendarClock, FileUp, MapPin, RefreshCw, Search } from 'lucide-react'
import { useRef, useState } from 'react'
import { useProjects } from '@/api/cases'
import { api, unwrap, type Schemas } from '@/api/client'
import { Intro } from '@/components/Explain'
import { JobRunner } from '@/components/JobRunner'
import { Completeness, LinkStatusBadge } from '@/components/LinkStatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, Dialog, Input, QueryState, Select, useToast } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { SUBSECTORS } from '@/lib/labels'
import { projectsRoute } from '@/router'

type P = Schemas['ProjectListItem']
const PAGE = 60

export default function Projects() {
  const s = projectsRoute.useSearch()
  const navigate = useNavigate({ from: '/projekty' })
  const { isExpert } = useAuth()
  const set = (patch: Partial<typeof s>) => navigate({ search: { ...s, ...patch }, replace: true })
  const tier = s.tier ?? 'deep'
  const q = useProjects({ q: s.q, tier, subsector: s.subsector, link_status: s.link_status, pending: s.pending })
  const [text, setText] = useState(s.q ?? '')
  const [shown, setShown] = useState(PAGE)

  return (
    <div>
      <PageHeader title="Baza przypadków"
        description="Zakończone i trwające inwestycje wodno-kanalizacyjne, z których system uczy się, co się w nich wydarzyło."
        actions={isExpert ? <>
          <ImportXlsx />
          <JobRunner label="Pobierz aktualne dane z BZP" icon={<RefreshCw size={14} />} invalidate={[['projects']]}
            start={async () => unwrap(await api.POST('/api/enrich', { body: { project_ids: null, sources: null, as_of: null } }))} />
        </> : undefined} />
      <Intro can={[
        'wyszukać inwestycję po nazwie, gminie lub numerze ogłoszenia',
        'otworzyć kartę inwestycji: przebieg zamówień, zmiany umów, opóźnienia i ich przyczyny – z odnośnikami do oryginalnych ogłoszeń',
        ...(isExpert ? ['zaimportować listę projektów (plik Excel) i pobrać z BZP nowe ogłoszenia dla wszystkich projektów – system dopasuje je do projektów i wyliczy zdarzenia; nic nie zostanie nadpisane bez Twojej decyzji'] : []),
      ]}>
        Baza ma dwie części: <b>22 projekty z listy przekazanej przez organizatora</b> – opisane szczegółowo i sprawdzane przez eksperta – oraz <b>ok. 34 tys. postępowań pobranych automatycznie</b> z Biuletynu Zamówień Publicznych (lata 2021–2026), które służą do porównań przy analizie nowych inwestycji.
      </Intro>
      <form className="mb-4 flex flex-wrap items-end gap-2" role="search" onSubmit={(e) => { e.preventDefault(); setShown(PAGE); set({ q: text || undefined }) }}>
        <label className="relative">
          <span className="sr-only">Szukaj</span>
          <Search size={14} className="absolute left-2.5 top-2.5 text-slate-400" aria-hidden />
          <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="Nazwa, gmina, NIP, numer ogłoszenia…" className="w-72 pl-8" />
        </label>
        <Select aria-label="Która część bazy" value={tier} onChange={(e) => { setShown(PAGE); set({ tier: e.target.value }) }}
          options={[{ value: 'deep', label: 'Projekty z listy organizatora (22)' }, { value: 'auto', label: 'Postępowania pobrane z BZP' }]} className="w-64" />
        <Select aria-label="Podsektor" value={s.subsector ?? ''} onChange={(e) => set({ subsector: e.target.value || undefined })} placeholder="Każdy podsektor"
          options={SUBSECTORS.map((x) => ({ value: x, label: x }))} className="w-56" />
        {isExpert && tier === 'deep' && (
          <label className="flex h-9 items-center gap-1.5 text-sm"><input type="checkbox" checked={!!s.pending} onChange={(e) => set({ pending: e.target.checked || undefined })} className="accent-brand" />
            Tylko z pozycjami do zatwierdzenia</label>)}
        <Button type="submit" variant="outline">Szukaj</Button>
      </form>
      <QueryState q={q}>{(d) => (
        <>
          <p className="mb-2 text-xs text-slate-500">Znaleziono: {d.total.toLocaleString('pl-PL')}{d.items.length < d.total ? ` (pokazano ${Math.min(shown, d.items.length)})` : ''}</p>
          <div className="grid gap-3 lg:grid-cols-2">{d.items.slice(0, shown).map((p) => <ProjectTile key={p.id} p={p} expert={isExpert} />)}</div>
          {!d.items.length && <p className="py-8 text-center text-sm text-slate-500">Nic nie znaleziono – zmień wyszukiwanie lub filtry.</p>}
          {d.items.length > shown && <div className="mt-4 text-center"><Button variant="outline" onClick={() => setShown((x) => x + PAGE)}>Pokaż więcej</Button></div>}
        </>
      )}</QueryState>
    </div>
  )
}

function ProjectTile({ p, expert }: { p: P; expert: boolean }) {
  return (
    <Link to="/projekty/$projectId" params={{ projectId: p.id }} search={{}} className="group">
      <Card className="h-full p-4 transition-colors group-hover:border-brand">
        <div className="flex items-start justify-between gap-2">
          <h2 className="line-clamp-2 font-medium text-slate-900">{p.title}</h2>
          {p.tier === 'deep' && <span className="shrink-0 font-mono text-xs text-slate-400">{p.code}</span>}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1"><MapPin size={12} />{p.beneficiary_name ?? '—'}{p.voivodeship ? `, ${p.voivodeship}` : ''}</span>
          {p.subsector_main && <span>{p.subsector_main}</span>}
          {p.project_status && <span className="inline-flex items-center gap-1"><CalendarClock size={12} />{p.project_status}</span>}
          {p.record_scope && p.record_scope !== 'całe postępowanie' && <Badge variant="info">{p.record_scope}</Badge>}
        </div>
        {p.tier === 'deep' && (
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
            <span className="flex items-center gap-1">Dopasowanie do BZP: <LinkStatusBadge status={p.link_status} /></span>
            <span>{p.n_events} {p.n_events === 1 ? 'zdarzenie' : 'zdarzeń'}</span>
            <span className="flex items-center gap-1">Kompletność danych: <Completeness value={p.completeness} /></span>
            {expert && p.n_pending_review > 0 && <Badge variant="warning">{p.n_pending_review} do zatwierdzenia</Badge>}
          </div>)}
      </Card>
    </Link>
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
      const token = localStorage.getItem('rm_token')
      const r = await fetch('/api/imports/xlsx?profile=organizer', { method: 'POST', body: fd, headers: token ? { Authorization: `Bearer ${token}` } : {} })
      if (!r.ok) throw new Error((await r.json().catch(() => ({})))?.detail ?? r.statusText)
      setReport(await r.json())
    } catch (e) { toast({ kind: 'error', title: 'Import nie powiódł się', description: String(e) }) } finally {
      setBusy(false); if (ref.current) ref.current.value = ''
    }
  }
  return (
    <>
      <input ref={ref} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} aria-label="Plik z listą projektów" />
      <Button variant="outline" onClick={() => ref.current?.click()} loading={busy} title="Wczytaj listę projektów z pliku Excel (format organizatora)"><FileUp size={14} />Importuj listę projektów (Excel)</Button>
      <Dialog open={!!report} onClose={() => setReport(null)} title="Wynik importu listy projektów" description={report ? `Plik „${report.file}”` : ''}
        footer={<Button onClick={() => setReport(null)}>OK</Button>}>
        {report && (
          <div className="space-y-3 text-sm">
            <p>Przeczytano <b>{report.rows}</b> wierszy: <b>{report.created}</b> nowych projektów, <b>{report.updated}</b> zmienionych, <b>{report.unchanged}</b> bez zmian.
              Ponowny import tego samego pliku niczego nie dubluje.</p>
            {(report.issues?.length ?? 0) > 0 && <>
              <h3 className="font-semibold">Wartości do sprawdzenia ({report.issues!.length})</h3>
              <ul className="list-disc space-y-1 pl-5 text-xs">{report.issues!.map((i, k) => (
                <li key={k}>Wiersz {String(i.row)}{i.code ? ` (${String(i.code)})` : ''}: {String(i.message)}</li>))}</ul></>}
          </div>
        )}
      </Dialog>
    </>
  )
}
