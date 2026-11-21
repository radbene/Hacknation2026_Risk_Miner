import { Link, useNavigate } from '@tanstack/react-router'
import { CheckCheck, ExternalLink, X } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceList } from '@/components/evidence/EvidencePanel'
import { Intro } from '@/components/Explain'
import { ExpertOnly } from '@/components/Layout'
import { RiskCodes } from '@/components/LinkStatusBadge'
import { LinkReasons, LinkVerdict } from '@/components/LinkReasons'
import { PageHeader } from '@/components/PageHeader'
import { ReviewActions } from '@/components/ReviewActions'
import { StatusBadge } from '@/components/StatusBadge'
import { confidenceWords, Fact } from '@/components/Visual'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Label, Loading, QueryState, Select, Textarea, useToast } from '@/components/ui'
import { RISK_NAMES } from '@/lib/labels'
import { cn, fmtDate, fmtNum, fmtPln } from '@/lib/utils'
import { EVENT_PL } from '@/pages/ProjectCard'
import { queueRoute } from '@/router'

type Q = Schemas['QueueItem']
type ObjType = Q['object_type']
const TYPES: { t: ObjType; label: string; help: string }[] = [
  { t: 'project_procedure', label: 'Powiązania z BZP', help: 'czy projekt z listy dobrze dopasowano do ogłoszeń w BZP' },
  { t: 'event', label: 'Zdarzenia i przyczyny', help: 'opóźnienia, zmiany umów, kary – z przyczyną i kategorią ryzyka' },
  { t: 'data_issue', label: 'Braki w danych', help: 'czego brakuje i gdzie źródła się różnią' },
  { t: 'contract_change', label: 'Zmiany umów', help: 'zmiany odczytane z ogłoszeń o zmianie i o wykonaniu umowy' },
  { t: 'contract', label: 'Umowy', help: 'wartości i terminy umów odczytane z ogłoszeń' },
  { t: 'project', label: 'Dane projektów', help: 'dane z listy organizatora' },
  { t: 'fact', label: 'Kwoty z adnotacji', help: 'kwoty odczytane z adnotacji instytucji w pliku organizatora' },
  { t: 'clause', label: 'Klauzule umowne', help: 'projekty zapisów umownych proponowanych w analizach' },
  { t: 'analysis_item', label: 'Elementy analiz', help: 'flagi i wnioski w analizach użytkowników' },
  { t: 'document', label: 'Dokumenty', help: 'dokumenty dodane do bazy' },
  { t: 'lesson', label: 'Wnioski z kontroli', help: 'wnioski z raportów NIK' },
  { t: 'risk_category', label: 'Nowe kategorie ryzyka', help: 'kategorie zaproponowane przez model' },
]

export default function ReviewQueue() {
  return <ExpertOnly what="Do zatwierdzenia"><QueueInner /></ExpertOnly>
}

function QueueInner() {
  const s = queueRoute.useSearch()
  const navigate = useNavigate({ from: '/kolejka' })
  const type = (s.type ?? 'event') as ObjType
  const status = s.status ?? 'proposed'
  const counts = useApi(['review', 'counts'], async () => unwrap(await api.GET('/api/review/counts')))
  const q = useApi(['review', 'queue', type, status, s.project ?? ''], async () => unwrap(await api.GET('/api/review/queue', {
    params: { query: { object_type: type, status, project_id: s.project ?? null, limit: 200 } },
  })))
  const [bulk, setBulk] = useState(false)
  const sel = q.data?.items.find((i) => i.object_id === s.item)
  const setSel = (id?: string) => navigate({ search: { ...s, item: id }, replace: true })
  const meta = TYPES.find((x) => x.t === type)

  return (
    <div>
      <PageHeader title="Do zatwierdzenia" actions={<Button variant="success" onClick={() => setBulk(true)}><CheckCheck size={14} />Zatwierdź pewne pozycje hurtowo</Button>} />
      <Intro can={['wybrać rodzaj pozycji z listy po lewej', 'kliknąć pozycję – po prawej zobaczysz podsumowanie, źródło z zaznaczonym fragmentem i przyciski decyzji',
        'zatwierdzić, poprawić lub odrzucić; uzasadnienie trafia do historii', 'zatwierdzić hurtowo pozycje, których system jest pewny (np. powiązania po numerze ogłoszenia)']}>
        Wszystko, co system zbudował automatycznie, jest propozycją. Tutaj decydujesz, co trafia do bazy jako wiarygodne. Najpierw pokazujemy pozycje, których system jest najmniej pewny. Twoje decyzje nie są nadpisywane przy ponownym przeliczeniu – system zapisze wtedy tylko propozycję zmiany do oceny.
      </Intro>
      <div className="grid gap-4 xl:grid-cols-[16rem_minmax(0,1fr)_minmax(0,1.3fr)] lg:grid-cols-[16rem_minmax(0,1fr)]">
        <nav aria-label="Rodzaje pozycji" className="space-y-1">
          <Select aria-label="Pokaż" value={status} onChange={(e) => navigate({ search: { ...s, status: e.target.value, item: undefined }, replace: true })} className="mb-2 w-full"
            options={[{ value: 'proposed', label: 'Czekające na decyzję' }, { value: 'approved', label: 'Zatwierdzone' }, { value: 'edited', label: 'Poprawione' },
              { value: 'rejected', label: 'Odrzucone' }, { value: 'all', label: 'Wszystkie' }]} />
          {TYPES.map((x) => {
            const n = counts.data?.[x.t] ?? 0
            if (!n && x.t !== type && status === 'proposed') return null
            return (
              <button key={x.t} onClick={() => navigate({ search: { ...s, type: x.t, item: undefined }, replace: true })}
                className={cn('flex w-full cursor-pointer items-center justify-between rounded px-3 py-2 text-left text-sm', x.t === type ? 'bg-brand-soft font-semibold text-brand' : 'hover:bg-slate-100')}>
                {x.label}{status === 'proposed' && <Badge variant={n ? 'warning' : 'default'}>{n}</Badge>}
              </button>)
          })}
        </nav>
        <div className="min-w-0">
          {meta && <p className="mb-2 text-xs text-slate-500">{meta.label}: {meta.help}.</p>}
          <QueryState q={q} empty={(d) => d.items.length === 0}>{(d) => (
            <ul className="space-y-2">{d.items.map((it) => (
              <li key={it.object_id}>
                <button onClick={() => setSel(it.object_id)} className={cn('w-full cursor-pointer rounded-lg border bg-white p-3 text-left',
                  it.object_id === s.item ? 'border-brand ring-1 ring-brand' : 'border-slate-200 hover:border-slate-300')}>
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-medium">{it.title.replace(/^[^:]+: /, '')}</span>
                    {it.project_code && <span className="shrink-0 font-mono text-[11px] text-slate-400">{it.project_code}</span>}
                  </div>
                  {it.summary && <p className="mt-1 line-clamp-2 text-xs text-slate-600">{it.summary}</p>}
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                    <span>pewność: {confidenceWords(it.confidence)}</span>
                    {it.has_proposal && <Badge variant="info">nowa propozycja po przeliczeniu</Badge>}
                  </div>
                </button>
              </li>))}</ul>
          )}</QueryState>
        </div>
        <div className="min-w-0 lg:col-span-2 xl:col-span-1">
          {sel ? <div className="xl:sticky xl:top-0"><Detail it={sel} onClose={() => setSel(undefined)} /></div>
            : <div className="hidden rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 xl:block">Kliknij pozycję z listy, aby zobaczyć szczegóły i podjąć decyzję.</div>}
        </div>
      </div>
      <BulkDialog open={bulk} onClose={() => setBulk(false)} type={type} />
    </div>
  )
}

function Detail({ it, onClose }: { it: Q; onClose: () => void }) {
  return (
    <Card className="border-brand/40">
      <CardHeader title={it.title.replace(/^[^:]+: /, '')}
        description={it.project_code ? <Link to="/projekty/$projectId" params={{ projectId: it.project_id! }} search={{}} className="inline-flex items-center gap-1 text-brand hover:underline">Karta projektu {it.project_code}<ExternalLink size={11} /></Link> : undefined}
        actions={<><StatusBadge status={it.status} /><button onClick={onClose} aria-label="Zamknij szczegóły" className="cursor-pointer rounded p-1 text-slate-500 hover:bg-slate-100"><X size={16} /></button></>} />
      <CardContent className="space-y-4">
        {it.object_type === 'event' ? <EventDetail id={it.object_id} />
          : it.object_type === 'project_procedure' ? <LinkDetail it={it} />
          : it.object_type === 'data_issue' ? <IssueDetail it={it} />
          : <GenericDetail it={it} />}
        <div className="border-t border-slate-100 pt-3">
          <div className="mb-2 text-xs font-semibold text-slate-600">Twoja decyzja</div>
          <ReviewActions objectType={it.object_type} objectId={it.object_id} status={it.status} invalidate={[['review'], ['events'], ['links']]}
            editFields={it.object_type === 'event' ? [{ key: 'risk_codes', label: 'Kategorie ryzyka', type: 'rcodes' }, { key: 'cause', label: 'Przyczyna', type: 'longtext' },
              { key: 'effect', label: 'Skutek', type: 'longtext' }, { key: 'mitigation', label: 'Działanie zaradcze', type: 'longtext' }] : undefined} />
        </div>
      </CardContent>
    </Card>
  )
}

function Sources({ ids }: { ids?: string[] | null }) {
  if (!ids?.length) return <p className="text-xs text-rose-700">Brak źródła – tej pozycji nie da się sprawdzić w dokumencie.</p>
  return <div><div className="mb-1 text-xs font-semibold text-slate-600">Źródło</div><EvidenceList ids={ids} /></div>
}

function EventDetail({ id }: { id: string }) {
  const q = useApi(['event', id], async () => unwrap(await api.GET('/api/events/{event_id}', { params: { path: { event_id: id } } })))
  if (q.isLoading) return <Loading />
  const e = q.data
  if (!e) return null
  return (
    <>
      <div className="flex flex-wrap items-center gap-2 text-sm"><Badge>{EVENT_PL[e.event_type] ?? e.event_type}</Badge><BlockLabel label={e.model_label ? 'wniosek_modelu' : 'dane_zrodlowe'} />
        {e.event_date && <span className="text-xs text-slate-500">{fmtDate(e.event_date)}</span>}</div>
      <div className="space-y-1 text-sm">
        <div className="text-xs text-slate-500">Kategoria ryzyka</div>
        {(e.risk_codes ?? []).length ? (e.risk_codes ?? []).map((c) => <div key={c} className="flex items-center gap-2"><RiskCodes codes={[c]} />{RISK_NAMES[c] ?? ''}</div>) : <span>—</span>}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 text-sm">
        <Fact label="Przyczyna" value={<span className="font-normal">{e.cause ?? '—'}</span>} />
        <Fact label="Skutek" value={<span className="font-normal">{e.effect ?? '—'}{e.effect_days != null && ` · ${fmtNum(e.effect_days, 0)} dni`}{e.effect_pln != null && ` · ${fmtPln(e.effect_pln)}`}</span>} />
        {e.mitigation && <Fact label="Działanie zaradcze" value={<span className="font-normal">{e.mitigation}</span>} />}
        <Fact label="Pewność systemu" value={confidenceWords(e.confidence)} hint={e.model_label ? `sklasyfikował: ${e.model_label}` : 'wyliczone regułami z danych BZP'} />
      </div>
      <Sources ids={e.evidence_ids} />
    </>
  )
}

function LinkDetail({ it }: { it: Q }) {
  const q = useApi(['links', it.project_id ?? ''], async () => unwrap(await api.GET('/api/links', { params: { query: { project_id: it.project_id ?? null } } })).items,
    undefined, { enabled: !!it.project_id })
  const l = q.data?.find((x) => x.id === it.object_id)
  if (q.isLoading) return <Loading />
  if (!l) return <GenericDetail it={it} />
  return (
    <>
      <div className="text-sm"><div className="font-medium">{l.procedure_title}</div><div className="text-xs text-slate-500">ogłoszenie {l.bzp_number}{l.part_no ? `, część ${l.part_no}` : ''}</div></div>
      <LinkVerdict method={l.method} confidence={l.confidence} />
      <div><div className="mb-1 text-xs font-semibold text-slate-600">Dlaczego to powiązanie</div><LinkReasons comps={l.components} /></div>
      {!!l.alternatives?.length && <p className="text-xs text-slate-500">System rozważył też {l.alternatives.length} inne postępowania tego zamawiającego – szczegóły na karcie projektu (zakładka „Ogłoszenia BZP tej inwestycji”), gdzie możesz też wskazać inne postępowanie.</p>}
    </>
  )
}

function IssueDetail({ it }: { it: Q }) {
  const q = useApi(['project', it.project_id ?? '', 'issues'], async () => unwrap(await api.GET('/api/projects/{project_id}/issues', { params: { path: { project_id: it.project_id! } } })),
    undefined, { enabled: !!it.project_id })
  const i = q.data?.find((x) => x.id === it.object_id)
  if (q.isLoading) return <Loading />
  if (!i) return <GenericDetail it={it} />
  return (
    <>
      <p className="text-sm">{i.message}</p>
      <div className="grid gap-3 sm:grid-cols-2 text-sm">
        {i.what_to_add && <Fact label="Co uzupełnić" value={<span className="font-normal">{i.what_to_add}</span>} />}
        {i.impact && <Fact label="Jak to wpływa na analizę" value={<span className="font-normal">{i.impact}</span>} />}
      </div>
      {!!i.evidence_ids?.length && <Sources ids={i.evidence_ids} />}
    </>
  )
}

function GenericDetail({ it }: { it: Q }) {
  return (
    <>
      {it.summary && <p className="text-sm text-slate-700">{it.summary}</p>}
      <Fact label="Pewność systemu" value={confidenceWords(it.confidence)} />
      <Sources ids={it.evidence_ids} />
    </>
  )
}

function BulkDialog({ open, onClose, type }: { open: boolean; onClose: () => void; type: ObjType }) {
  const { toast } = useToast()
  const [minConf, setMinConf] = useState('1')
  const [comment, setComment] = useState('Zatwierdzenie hurtowe pozycji pewnych')
  const meta = TYPES.find((x) => x.t === type)
  const m = useApiMutation<Schemas['BulkConfirmIn'], Schemas['BulkResult']>({
    fn: async (body) => unwrap(await api.POST('/api/review/bulk-confirm', { body })),
    invalidate: [['review'], ['projects'], ['links'], ['events'], ['history']],
    onSuccess: (r) => { toast({ kind: 'success', title: `Zatwierdzono ${r.confirmed} pozycji`, description: `${r.skipped} pozostało do ręcznej decyzji (mniej pewne albo już rozstrzygnięte).` }); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title={`Zatwierdź hurtowo: ${meta?.label ?? type}`}
      description="Zatwierdza tylko te propozycje, których system jest pewny co najmniej w wybranym stopniu. Pozostałe zostają do ręcznej decyzji. Każde zatwierdzenie trafia do historii."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button>
        <Button variant="success" loading={m.isPending} onClick={() => m.mutate({ object_type: type, min_confidence: Number(minConf), comment, ids: null, project_id: null, method: null })}>Zatwierdź</Button></>}>
      <div className="space-y-3 text-sm">
        <div><Label htmlFor="b-c">Zatwierdź pozycje, których system jest pewny</Label>
          <Select id="b-c" value={minConf} onChange={(e) => setMinConf(e.target.value)}
            options={[{ value: '1', label: 'całkowicie (np. dopasowanie po numerze ogłoszenia lub projektu KPO)' }, { value: '0.95', label: 'bardzo wysoko' }, { value: '0.8', label: 'wysoko' }]} /></div>
        <div><Label htmlFor="b-k">Uzasadnienie</Label><Textarea id="b-k" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} /></div>
      </div>
    </Dialog>
  )
}
