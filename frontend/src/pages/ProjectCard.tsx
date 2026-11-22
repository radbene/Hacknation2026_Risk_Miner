import { Link, useNavigate } from '@tanstack/react-router'
import { ExternalLink, FileUp, Link2, RefreshCw } from 'lucide-react'
import { useRef, useState } from 'react'
import {
  useCandidates, useContracts, useDocuments, useEvents, useHistory, useLinks, useNotices, useProcedures, useProject,
} from '@/api/cases'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { BlockLabel } from '@/components/BlockLabel'
import { GraphTab } from '@/components/case/GraphTab'
import { TimelineTab } from '@/components/case/TimelineTab'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { NoticeView } from '@/components/evidence/NoticeView'
import { Intro } from '@/components/Explain'
import { JobRunner } from '@/components/JobRunner'
import { Completeness, LinkStatusBadge, RiskCodes } from '@/components/LinkStatusBadge'
import { LinkReasons, LinkVerdict } from '@/components/LinkReasons'
import { PageHeader } from '@/components/PageHeader'
import { ReviewActions } from '@/components/ReviewActions'
import { StatusBadge } from '@/components/StatusBadge'
import { confidenceWords, Fact } from '@/components/Visual'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Input, Label, QueryState, Tabs, Textarea, useToast } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { ACTION_LABEL, EVENT_TYPE_LABEL, OBJECT_TYPE_LABEL } from '@/lib/labels'
import { cn, fmtDate, fmtDateTime, fmtNum, fmtPln } from '@/lib/utils'
import { projectRoute } from '@/router'

const NOTICE_PL: Record<string, string> = {
  ContractNotice: 'Ogłoszenie o zamówieniu', TenderResultNotice: 'Ogłoszenie o wyniku postępowania', AgreementUpdateNotice: 'Ogłoszenie o zmianie umowy',
  ContractPerformingNotice: 'Ogłoszenie o wykonaniu umowy',
}
export const EVENT_PL: Record<string, string> = {
  ...EVENT_TYPE_LABEL, late: 'Opóźnienie', paid_above_value: 'Wypłata wyższa niż wartość umowy', change_deadline: 'Zmiana terminu',
  change_value: 'Zmiana wynagrodzenia', change_scope: 'Zmiana zakresu', repeated: 'Powtórzone postępowanie', improper: 'Nienależyte wykonanie / kary umowne',
  cancelled: 'Unieważnienie', single_offer: 'Jedna oferta', over_budget: 'Oferty powyżej budżetu', not_performed: 'Niewykonanie umowy',
  terminated: 'Rozwiązanie umowy', document_fragment: 'Fragment dokumentu',
}
const ISSUE: Record<string, { label: string; tone: 'default' | 'info' | 'warning' | 'danger' | 'success' }> = {
  nie_ma_w_paczce: { label: 'nie ma w zebranych materiałach', tone: 'default' },
  dokument_nie_wspomina: { label: 'dokument nie wspomina', tone: 'info' },
  brak_potwierdzenia: { label: 'brak potwierdzenia', tone: 'warning' },
  potwierdzono_niewykonanie: { label: 'potwierdzono, że nie wykonano', tone: 'danger' },
  sprzeczne: { label: 'źródła się różnią', tone: 'danger' },
  potwierdzone: { label: 'potwierdzone', tone: 'success' },
}

export default function ProjectCard() {
  const { projectId } = projectRoute.useParams()
  const s = projectRoute.useSearch()
  const navigate = useNavigate({ from: '/projekty/$projectId' })
  const { isExpert } = useAuth()
  const tab = s.tab ?? 'przeglad'
  const setTab = (t: string) => navigate({ search: { ...s, tab: t, notice: undefined }, replace: true })
  const p = useProject(projectId)
  const events = useEvents(projectId)
  const links = useLinks(projectId)

  return (
    <QueryState q={p}>{(d) => {
      const deep = d.tier === 'deep'
      return (
        <div>
          <PageHeader back title={d.title}
            description={<>{d.beneficiary_name}{d.voivodeship ? `, ${d.voivodeship}` : ''}</>}
            actions={isExpert && deep ? <>
              <JobRunner label="Pobierz aktualne dane z BZP" icon={<RefreshCw size={14} />} variant="outline"
                invalidate={[['project', projectId], ['links', projectId], ['events', projectId]]}
                start={async () => unwrap(await api.POST('/api/enrich', { body: { project_ids: [projectId], sources: null, as_of: null } }))} />
              <Reanalyze projectId={projectId} />
            </> : undefined}>
            {deep && <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
              <span className="flex items-center gap-1">Dopasowanie do ogłoszeń BZP: <LinkStatusBadge status={d.link_status} /></span>
              <span className="flex items-center gap-1">Kompletność danych: <Completeness value={d.completeness} /></span>
              {isExpert && d.n_pending_review > 0 && <Badge variant="warning">{d.n_pending_review} do zatwierdzenia</Badge>}
            </div>}
          </PageHeader>
          <Tabs value={tab} onChange={setTab} tabs={[
            { value: 'przeglad', label: 'Opis' },
            { value: 'os', label: 'Przebieg w czasie' },
            { value: 'powiazania', label: 'Ogłoszenia BZP tej inwestycji', count: links.data?.filter((l) => l.status !== 'rejected').length },
            { value: 'umowy', label: 'Umowy i zmiany' },
            { value: 'zdarzenia', label: 'Zdarzenia i przyczyny', count: events.data?.length },
            { value: 'ogloszenia', label: 'Treść ogłoszeń' },
            { value: 'dokumenty', label: 'Dokumenty' },
            { value: 'braki', label: 'Braki w danych' },
            { value: 'graf', label: 'Mapa powiązań' },
            { value: 'historia', label: 'Historia zmian' },
          ]}>
            {tab === 'przeglad' && <Overview d={d} expert={isExpert} />}
            {tab === 'os' && <><Intro>
              Kolejne kroki inwestycji: ogłoszenie, wybór wykonawcy, umowa, zmiany umowy oraz planowany i faktyczny termin. Różnica terminów to opóźnienie.</Intro>
              <TimelineTab projectId={projectId} /></>}
            {tab === 'powiazania' && <LinksTab projectId={projectId} expert={isExpert} />}
            {tab === 'umowy' && <ContractsTab projectId={projectId} />}
            {tab === 'zdarzenia' && <EventsTab projectId={projectId} expert={isExpert} />}
            {tab === 'ogloszenia' && <NoticesTab projectId={projectId} selected={s.notice} section={s.section} quote={s.quote}
              onSelect={(id) => navigate({ search: { ...s, notice: id }, replace: true })} />}
            {tab === 'dokumenty' && <DocumentsTab projectId={projectId} expert={isExpert} />}
            {tab === 'braki' && <IssuesTab projectId={projectId} />}
            {tab === 'graf' && <><Intro>
              Beneficjent, postępowania, ogłoszenia, umowy, zmiany i zdarzenia oraz ich związki. Linia przerywana to powiązanie, którego ekspert jeszcze nie zatwierdził.</Intro>
              <GraphTab projectId={projectId} /></>}
            {tab === 'historia' && <HistoryTab projectId={projectId} />}
          </Tabs>
        </div>
      )
    }}</QueryState>
  )
}

/* ------------------------------------------------------------------ overview */

const XLSX_FIELDS: [keyof Schemas['ProjectDetail'], string][] = [
  ['public_id_type', 'Rodzaj identyfikatora'], ['public_id_value', 'Identyfikator (numer ogłoszenia lub projektu KPO)'],
  ['record_scope', 'Czego dotyczy rekord'], ['project_status', 'Stan realizacji'], ['funding', 'Finansowanie'],
  ['work_type', 'Rodzaj robót'], ['formula', 'Formuła realizacji'], ['city', 'Miejscowość'], ['voivodeship', 'Województwo'],
]

function Overview({ d, expert }: { d: Schemas['ProjectDetail']; expert: boolean }) {
  const ev = ((d.import_row as Record<string, unknown> | null)?.evidence ?? {}) as Record<string, string>
  return (
    <div>
      <Intro can={expert ? ['zatwierdzić dane projektu albo poprawić błędną wartość'] : undefined}>
        Dane inwestycji{d.tier === 'deep' ? ' z listy organizatora (plik Excel)' : ' odczytane z ogłoszeń BZP'}. Przy każdej wartości jest jej źródło.
      </Intro>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Opis przedsięwzięcia" actions={<BlockLabel label="dane_zrodlowe" />} />
          <CardContent className="space-y-4 text-sm">
            <p className="whitespace-pre-line text-slate-700">{d.description ?? 'Brak opisu.'}</p>
            <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
              {XLSX_FIELDS.map(([k, label]) => d[k] ? (
                <div key={k} className="flex items-start justify-between gap-2"><Fact label={label} value={String(d[k])} />
                  {ev[k as string] && <EvidenceChip ids={[ev[k as string]]} />}</div>) : null)}
              <Fact label="Wartość projektu" value={fmtPln(d.project_value)} />
              <Fact label="Kwota dofinansowania" value={fmtPln(d.grant_value)} />
            </div>
            {d.annotation && <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs"><b>Adnotacja instytucji:</b> {d.annotation}</div>}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader title="Beneficjent" />
            <CardContent className="space-y-1 text-sm">
              <div className="font-medium">{d.beneficiary?.name ?? d.beneficiary_name}</div>
              <div className="text-xs text-slate-500">NIP {d.beneficiary?.nip ?? d.beneficiary_nip ?? '—'}</div>
              <div className="text-xs text-slate-500">{[d.beneficiary?.city, d.beneficiary?.province].filter(Boolean).join(', ')}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader title="Stan weryfikacji" />
            <CardContent className="space-y-2 text-sm">
              <StatusBadge status={d.status} />
              {expert ? <ReviewActions objectType="project" objectId={d.id} status={d.status} exemplary={d.exemplary} proposal={d.proposal}
                values={d as unknown as Record<string, unknown>}
                editFields={[{ key: 'title', label: 'Nazwa' }, { key: 'description', label: 'Opis', type: 'longtext' },
                  { key: 'subsector_main', label: 'Podsektor' }, { key: 'work_type', label: 'Rodzaj robót' }, { key: 'formula', label: 'Formuła' },
                  { key: 'public_id_value', label: 'Identyfikator' }, { key: 'project_status', label: 'Stan realizacji' }]}
                invalidate={[['project', d.id]]} />
                : null}
            </CardContent>
          </Card>
        </div>
      </div>
      {d.tier === 'deep' && <PublicSources projectId={d.id} />}
    </div>
  )
}

type PublicFact = { source: string; label: string; value: string | null; subject: string | null; subject_type: string; evidence_ids: string[]; fact_type: string }
const SOURCE_PL: Record<string, string> = { kposk: 'KPOŚK (dane.gov.pl)', ted: 'TED', vat_whitelist: 'Biała lista VAT', krs: 'KRS' }

/** Facts about the project, its beneficiary and contractors from public sources beyond BZP. */
function PublicSources({ projectId }: { projectId: string }) {
  const q = useApi(['public-sources', projectId], async () => {
    const r = await fetch(`/api/projects/${projectId}/public-sources`)
    if (!r.ok) throw new Error(await r.text())
    return (await r.json()) as PublicFact[]
  })
  const items = q.data ?? []
  if (!items.length) return null
  const notices = items.filter((x) => x.fact_type === 'ted_notice')
  const rest = items.filter((x) => x.fact_type !== 'ted_notice')
  return (
    <Card className="mt-4">
      <CardHeader title="Inne źródła publiczne" description="KPOŚK, TED, Biała lista VAT i KRS – każda wartość z odnośnikiem do źródła." actions={<BlockLabel label="dane_zrodlowe" />} />
      <CardContent className="space-y-2 text-sm">
        <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {rest.map((x, i) => (
            <div key={i} className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1">
              <div><div className="text-xs text-slate-500">{x.label}{x.subject ? ` · ${x.subject}` : ''} · <span className="font-mono">{SOURCE_PL[x.source] ?? x.source}</span></div>
                <div className="text-slate-800">{x.value ?? '—'}</div></div>
              <EvidenceChip ids={x.evidence_ids} />
            </div>))}
        </div>
        {notices.length > 0 && <details className="text-xs text-slate-600"><summary className="cursor-pointer">Ogłoszenia robót tego zamawiającego w TED ({notices.length})</summary>
          <ul className="mt-1 space-y-1">{notices.map((x, i) => <li key={i} className="flex items-start justify-between gap-2"><span>{x.value}</span><EvidenceChip ids={x.evidence_ids} /></li>)}</ul></details>}
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ links */

function LinksTab({ projectId, expert }: { projectId: string; expert: boolean }) {
  const links = useLinks(projectId)
  const cands = useCandidates(projectId)
  const [relink, setRelink] = useState(false)
  return (
    <div className="space-y-4">
      <Intro can={expert ? ['zatwierdzić lub odrzucić powiązanie albo wskazać inne postępowanie; decyzja przetrwa ponowne pobranie danych'] : undefined}>
        Postępowanie w BZP, którego dotyczy inwestycja, z listą warunków, które sprawdził system, oraz postępowaniami tego zamawiającego, które odrzucił.
      </Intro>
      <QueryState q={links} empty={(l) => l.length === 0}>{(ls) => (
        <div className="space-y-3">
          {ls.map((l) => (
            <Card key={l.id} className={cn(l.status === 'rejected' && 'opacity-60')}>
              <CardHeader title={l.procedure_title} description={<>Ogłoszenie {l.bzp_number}{l.part_no ? `, część ${l.part_no}` : ''}</>}
                actions={<StatusBadge status={l.status} />} />
              <CardContent className="space-y-3">
                <LinkVerdict method={l.method} confidence={l.confidence} />
                <LinkReasons comps={l.components} />
                {!!l.alternatives?.length && (
                  <details className="text-sm"><summary className="cursor-pointer text-slate-600">Inne postępowania tego zamawiającego, które system rozważył ({l.alternatives.length})</summary>
                    <ul className="mt-2 space-y-1.5">{l.alternatives.map((a, i) => (
                      <li key={i} className="rounded bg-slate-50 p-2 text-xs"><b>{a.title}</b> <span className="text-slate-500">(ogłoszenie {a.bzp_number}; dopasowanie {confidenceWords(a.score)})</span>
                        {a.why_not && <div className="text-amber-800">Dlaczego nie: {a.why_not}</div>}</li>))}</ul></details>)}
                {expert && <ReviewActions objectType="project_procedure" objectId={l.id} status={l.status} proposal={l.proposal}
                  onRelink={() => setRelink(true)} invalidate={[['links', projectId], ['project', projectId]]} />}
              </CardContent>
            </Card>
          ))}
        </div>
      )}</QueryState>
      {expert && <>
        <div className="flex justify-end"><Button variant="outline" onClick={() => setRelink(true)}><Link2 size={14} />Wskaż inne postępowanie</Button></div>
        <RelinkDialog open={relink} onClose={() => setRelink(false)} projectId={projectId} candidates={cands.data ?? []} />
      </>}
    </div>
  )
}

function RelinkDialog({ open, onClose, projectId, candidates }: { open: boolean; onClose: () => void; projectId: string; candidates: Schemas['LinkCandidate'][] }) {
  const { toast } = useToast()
  const [sel, setSel] = useState<string>('')
  const [notice, setNotice] = useState('')
  const [part, setPart] = useState('')
  const [comment, setComment] = useState('')
  const m = useApiMutation<Schemas['ProjectRelinkIn'], Schemas['LinkOut']>({
    fn: async (body) => unwrap(await api.POST('/api/projects/{project_id}/relink', { params: { path: { project_id: projectId } }, body })),
    invalidate: [['links', projectId], ['project', projectId], ['projects'], ['review'], ['history']],
    onSuccess: () => { toast({ kind: 'success', title: 'Powiązanie zmienione' }); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zmienić powiązania', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title="Wskaż właściwe postępowanie" description="Wybierz postępowanie tego zamawiającego albo wpisz numer ogłoszenia BZP."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button>
        <Button loading={m.isPending} disabled={(!sel && !notice.trim()) || !comment.trim()}
          onClick={() => m.mutate({ procedure_id: sel || null, notice_number: notice.trim() || null, part_no: part ? Number(part) : null, comment, ocid: null })}>Zapisz powiązanie</Button></>}>
      <div className="space-y-3 text-sm">
        <div className="max-h-64 space-y-1 overflow-auto">
          {candidates.map((c) => (
            <label key={String(c.procedure_id)} className={cn('flex cursor-pointer items-start gap-2 rounded border p-2', sel === c.procedure_id ? 'border-brand bg-brand-soft' : 'border-slate-200')}>
              <input type="radio" name="cand" className="mt-1 accent-brand" checked={sel === c.procedure_id} onChange={() => { setSel(String(c.procedure_id)); setNotice('') }} />
              <span><span className="text-xs">{c.title}</span><br /><span className="text-[11px] text-slate-500">dopasowanie {confidenceWords(c.score)}</span></span>
            </label>))}
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-2"><Label htmlFor="rl-n">…albo numer ogłoszenia BZP</Label>
            <Input id="rl-n" value={notice} onChange={(e) => { setNotice(e.target.value); setSel('') }} placeholder="np. 2023/BZP 00110672/01" /></div>
          <div><Label htmlFor="rl-p">Część zamówienia</Label><Input id="rl-p" type="number" min={1} value={part} onChange={(e) => setPart(e.target.value)} /></div>
        </div>
        <div><Label htmlFor="rl-c">Uzasadnienie (wymagane)</Label><Textarea id="rl-c" value={comment} onChange={(e) => setComment(e.target.value)} rows={2} /></div>
      </div>
    </Dialog>
  )
}

/* ------------------------------------------------------------------ contracts */

function ContractsTab({ projectId }: { projectId: string }) {
  const procs = useProcedures(projectId)
  const contracts = useContracts(projectId)
  return (
    <div className="space-y-4">
      <Intro>
        Przetarg, umowy z wykonawcami i każda zmiana umowy z podstawą prawną i powodem. Wartość szacunkowa jest netto, pozostałe kwoty brutto.
      </Intro>
      <QueryState q={procs} empty={(x) => x.length === 0}>{(ps) => (
        <div className="grid gap-3 md:grid-cols-2">{ps.map((p) => (
          <Card key={p.id}>
            <CardHeader title={p.title} description={<>Ogłoszenie {p.bzp_number}</>} actions={<EvidenceChip ids={p.evidence_ids} />} />
            <CardContent className="grid grid-cols-2 gap-3 text-sm">
              <Fact label="Wartość szacunkowa (netto)" value={fmtPln(p.est_value_net)} />
              <Fact label="Kwota przeznaczona przez zamawiającego (brutto)" value={fmtPln(p.budget_gross)} />
              <Fact label="Liczba ofert" value={p.offers_count ?? '—'} />
              <Fact label="Planowany czas realizacji" value={p.planned_period_text ?? (p.planned_days ? `${p.planned_days} dni` : '—')} />
              <Fact label="Tryb" value={p.mode ? p.mode.replace(/^Zamówienie udzielane jest w trybie /i, '').replace(/ na podstawie:.*/, '') : '—'} />
              <Fact label="Środki UE" value={p.eu_funded == null ? '—' : p.eu_funded ? 'tak' : 'nie'} />
              {p.cancelled && <div className="col-span-2"><Badge variant="danger">Postępowanie unieważnione</Badge></div>}
            </CardContent>
          </Card>))}</div>
      )}</QueryState>
      <QueryState q={contracts} empty={(x) => x.length === 0}>{(cs) => (
        <div className="space-y-3">{cs.map((c) => {
          const delay = c.actual_end && c.planned_end ? Math.round((+new Date(c.actual_end) - +new Date(c.planned_end)) / 86400000) : null
          return (
            <Card key={c.id}>
              <CardHeader title={`Umowa${c.part_no ? `, część ${c.part_no}` : ''}`}
                description={c.contractor ? `Wykonawca: ${c.contractor.natural_person_flag ? 'osoba fizyczna (dane ukryte)' : c.contractor.name}` : undefined}
                actions={<EvidenceChip ids={c.evidence_ids} />} />
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                  <Fact label="Podpisana" value={fmtDate(c.signed_at)} />
                  <Fact label="Wartość umowy" value={fmtPln(c.value_gross)} />
                  <Fact label="Planowany koniec" value={fmtDate(c.planned_end)} />
                  <Fact label="Faktyczny koniec" value={fmtDate(c.actual_end)} />
                  <Fact label="Wypłacono" value={fmtPln(c.paid_gross)} warn={!!(c.paid_gross && c.value_gross && c.paid_gross > c.value_gross)} />
                  <Fact label="Opóźnienie" value={delay == null ? '—' : delay > 0 ? `${delay} dni` : 'w terminie'} warn={(delay ?? 0) > 0} />
                  <Fact label="Wykonana w terminie?" value={c.on_time == null ? '—' : c.on_time ? 'tak' : 'nie'} warn={c.on_time === false} />
                  <Fact label="Wykonana należycie?" value={c.proper == null ? '—' : c.proper ? 'tak' : 'nie'} warn={c.proper === false} />
                </div>
                {!!c.changes?.length && (
                  <div>
                    <h3 className="mb-1 text-sm font-semibold">Zmiany umowy ({c.changes.length})</h3>
                    <ol className="space-y-2">{c.changes.map((ch) => (
                      <li key={ch.id} className="rounded-md border border-slate-200 p-2 text-sm">
                        <div className="flex flex-wrap items-center gap-2"><b>Zmiana nr {ch.change_no}</b>
                          {ch.change_date && <span className="text-xs text-slate-500">{fmtDate(ch.change_date)}</span>}
                          {ch.new_end && <Badge>nowy termin: {fmtDate(ch.new_end)}</Badge>}
                          {ch.value_delta != null && <Badge>{ch.value_delta > 0 ? '+' : ''}{fmtPln(ch.value_delta)}</Badge>}
                          <EvidenceChip ids={ch.evidence_ids} className="ml-auto" />
                        </div>
                        {ch.legal_basis && <div className="mt-1 text-xs text-slate-500">Podstawa: {ch.legal_basis}</div>}
                        {ch.reason && <div className="mt-1 text-slate-700">Powód: „{ch.reason}”</div>}
                      </li>))}</ol>
                  </div>)}
              </CardContent>
            </Card>)
        })}</div>
      )}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ events */

function EventsTab({ projectId, expert }: { projectId: string; expert: boolean }) {
  const ev = useEvents(projectId)
  return (
    <div>
      <Intro can={expert ? ['zatwierdzić zdarzenie, poprawić przyczynę lub kategorię ryzyka, oznaczyć je jako wzorcowe'] : undefined}>
        Opóźnienia, zmiany umów, wypłaty ponad wartość umowy i kary: przyczyna z cytatem, skutek w dniach i złotych oraz kategoria ryzyka R01–R15. „Wniosek modelu” oznacza, że przyczynę sklasyfikował model językowy na podstawie cytatu sprawdzonego w źródle.
      </Intro>
      <QueryState q={ev} empty={(x) => x.length === 0}>{(items) => (
        <div className="space-y-3">{items.map((e) => (
          <Card key={e.id} className={cn(e.status === 'rejected' && 'opacity-60')}>
            <CardHeader title={<span className="flex flex-wrap items-center gap-2">{e.title ?? EVENT_PL[e.event_type] ?? e.event_type}<RiskCodes codes={e.risk_codes} />{e.exemplary && <Badge variant="violet">wzorcowe</Badge>}</span>}
              description={e.event_date ? fmtDate(e.event_date) : undefined}
              actions={<><BlockLabel label={e.model_label ? 'wniosek_modelu' : 'dane_zrodlowe'} /><StatusBadge status={e.status} /></>} />
            <CardContent className="space-y-2 text-sm">
              {e.quote && <blockquote className="border-l-2 border-teal-400 bg-teal-50/40 py-1 pl-2 text-slate-700">„{e.quote}”</blockquote>}
              <div className="flex"><EvidenceChip ids={e.evidence_ids} label="Pokaż w źródle" /></div>
              <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
                {e.cause && <Fact label="Przyczyna" value={<span className="font-normal">{e.cause}</span>} />}
                {(e.effect || e.effect_days != null || e.effect_pln != null) && <Fact label="Skutek" value={<span className="font-normal">{e.effect}
                  {e.effect_days != null && `, ${fmtNum(e.effect_days, 0)} dni`}{e.effect_pln != null && `, ${fmtPln(e.effect_pln)}`}</span>} />}
                {e.mitigation && <Fact label="Działanie zaradcze" value={<span className="font-normal">{e.mitigation}{e.mitigation_effect && <Badge className="ml-1" variant={e.mitigation_effect === 'skuteczne' ? 'success' : 'warning'}>{e.mitigation_effect}</Badge>}</span>} />}
              </div>
              {e.model_label && <div className="text-[11px] text-amber-800">Przyczynę sklasyfikował {e.model_label.replace(/\s*\(.*\)$/, '')}, pewność {confidenceWords(e.confidence)}.</div>}
              {expert && <ReviewActions objectType="event" objectId={e.id} status={e.status} exemplary={e.exemplary} proposal={e.proposal}
                values={e as unknown as Record<string, unknown>}
                editFields={[{ key: 'risk_codes', label: 'Kategorie ryzyka', type: 'rcodes' }, { key: 'cause', label: 'Przyczyna', type: 'longtext' },
                  { key: 'effect', label: 'Skutek', type: 'longtext' }, { key: 'mitigation', label: 'Działanie zaradcze', type: 'longtext' }]}
                invalidate={[['events', projectId]]} />}
            </CardContent>
          </Card>))}</div>
      )}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ notices */

function NoticesTab({ projectId, selected, section, quote, onSelect }: { projectId: string; selected?: string; section?: string; quote?: string; onSelect: (id: string) => void }) {
  const n = useNotices(projectId)
  return (
    <div>
      <Intro>
        Pełna treść ogłoszeń tej inwestycji w numeracji punktów z oryginału.
      </Intro>
      <QueryState q={n} empty={(x) => x.length === 0}>{(ns) => {
        const cur = selected ?? ns[0]?.id
        return (
          <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
            <ul className="space-y-1">{ns.map((x) => (
              <li key={x.id}><button onClick={() => onSelect(x.id)}
                className={cn('w-full cursor-pointer rounded border p-2 text-left text-xs', cur === x.id ? 'border-brand bg-brand-soft' : 'border-slate-200 bg-white hover:bg-slate-50')}>
                <div className="font-semibold">{NOTICE_PL[x.notice_type] ?? x.notice_type}</div>
                <div>{fmtDate(x.published_at)}</div>
              </button></li>))}</ul>
            <div>
              {cur && (() => {
                const x = ns.find((y) => y.id === cur)
                return (<>
                  {x?.url && <a href={x.url} target="_blank" rel="noreferrer" className="mb-2 inline-flex items-center gap-1 text-xs text-brand hover:underline"><ExternalLink size={12} />Oryginał w e-Zamówieniach</a>}
                  <NoticeView noticeId={cur} section={section} quote={quote} />
                </>)
              })()}
            </div>
          </div>
        )
      }}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ documents */

function DocumentsTab({ projectId, expert }: { projectId: string; expert: boolean }) {
  const docs = useDocuments(projectId)
  const ref = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [url, setUrl] = useState('')
  const { toast } = useToast()
  async function upload(f: File) {
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', f); fd.append('project_id', projectId)
      const token = localStorage.getItem('rm_token')
      const r = await fetch('/api/documents', { method: 'POST', body: fd, headers: token ? { Authorization: `Bearer ${token}` } : {} })
      if (!r.ok) throw new Error((await r.json().catch(() => ({})))?.detail ?? r.statusText)
      toast({ kind: 'success', title: 'Dokument dodany', description: 'Tekst odczytany; fragmenty wskazujące ryzyko czekają na Twoją decyzję.' })
      docs.refetch()
    } catch (e) { toast({ kind: 'error', title: 'Nie udało się dodać dokumentu', description: String(e) }) } finally {
      setBusy(false); if (ref.current) ref.current.value = ''
    }
  }
  async function fromUrl() {
    setBusy(true)
    try { unwrap(await api.POST('/api/documents/from-url', { body: { url, project_id: projectId, analysis_id: null, doc_type: null } })); setUrl(''); docs.refetch() }
    catch (e) { toast({ kind: 'error', title: 'Nie udało się pobrać', description: String(e) }) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-3">
      <Intro can={expert ? ['dodać dokument (PDF, Word, Excel) albo adres URL; system odczyta tekst ze stronami i wskaże fragmenty świadczące o ryzyku', 'przeliczyć zdarzenia, żeby zobaczyć, co zmienił nowy dokument'] : undefined}>
        Dokumenty spoza BZP: umowa, aneksy, protokoły, SWZ, program funkcjonalno-użytkowy, raporty kontroli.
      </Intro>
      {expert && <div className="flex flex-wrap items-end gap-2">
        <input ref={ref} type="file" className="hidden" accept=".pdf,.docx,.xlsx,.xls,.csv,.html,.htm,.txt" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} aria-label="Plik dokumentu" />
        <Button variant="outline" loading={busy} onClick={() => ref.current?.click()}><FileUp size={14} />Dodaj dokument</Button>
        <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="…albo adres dokumentu w internecie" className="w-80" />
        <Button variant="outline" disabled={!url.startsWith('http')} loading={busy} onClick={fromUrl}>Pobierz</Button>
      </div>}
      <QueryState q={docs} empty={(x) => x.length === 0}>{(ds) => (
        <ul className="grid gap-2 md:grid-cols-2">{ds.map((d) => (
          <li key={d.id}><Link to="/dokumenty/$documentId" params={{ documentId: d.id }} search={{}}
            className="flex items-start gap-2 border-2 border-ink bg-surface p-3 hover:border-brand">
            <span className="min-w-0"><span className="block truncate font-medium">{d.title ?? d.file_name}</span>
              <span className="text-xs text-slate-500">{[d.doc_type, d.pages ? `${d.pages} str.` : null].filter(Boolean).join(', ')}</span></span>
          </Link></li>))}</ul>
      )}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ issues */

function IssuesTab({ projectId }: { projectId: string }) {
  const c = useApi(['project', projectId, 'completeness'], async () =>
    unwrap(await api.GET('/api/projects/{project_id}/completeness', { params: { path: { project_id: projectId } } })))
  return (
    <div>
      <Intro>
        Czego brakuje i jak to ogranicza analizę. Te cztery stany nie są równoważne: <b>nie ma w zebranych materiałach</b> (dokument może istnieć), <b>dokument nie wspomina</b>, <b>brak potwierdzenia</b> i <b>potwierdzono, że nie wykonano</b>. Osobno pokazujemy sprzeczności między źródłami.
      </Intro>
      <QueryState q={c}>{(d) => (
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm"><span>Kompletność danych tej inwestycji:</span><Completeness value={d.score} /></div>
          <ul className="space-y-2">{d.items.map((i) => {
            const st = ISSUE[String(i.state)] ?? { label: String(i.state ?? '—'), tone: 'default' as const }
            return (
              <li key={i.id} className="border-2 border-ink bg-surface p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2"><Badge variant={st.tone}>{st.label}</Badge><span className="font-medium">{i.message}</span>
                  {!!i.evidence_ids?.length && <EvidenceChip ids={i.evidence_ids} className="ml-auto" />}</div>
                {i.what_to_add && <div className="mt-1 text-xs"><span className="text-slate-500">Co uzupełnić: </span>{i.what_to_add}</div>}
                {i.impact && <div className="text-xs"><span className="text-slate-500">Jak to wpływa na analizę: </span>{i.impact}</div>}
              </li>)
          })}</ul>
        </div>
      )}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ history */

function HistoryTab({ projectId }: { projectId: string }) {
  const h = useHistory(projectId)
  return (
    <div>
      <Intro>Decyzje eksperta dotyczące tej inwestycji: kto, kiedy, z jakim uzasadnieniem i co zmienił.</Intro>
      <QueryState q={h} empty={(x) => x.length === 0}>{(items) => (
        <ol className="space-y-2">{items.map((r) => (
          <li key={r.id} className="border-2 border-ink bg-surface p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2"><b>{fmtDateTime(r.at)}</b><span>{r.reviewer}</span>
              <Badge>{ACTION_LABEL[r.action] ?? r.action}</Badge><span className="text-slate-500">{OBJECT_TYPE_LABEL[r.object_type] ?? r.object_type}</span></div>
            {r.comment && <div className="mt-1 text-slate-700">Uzasadnienie: „{r.comment}”</div>}
            <ChangeList before={r.before} after={r.after} />
          </li>))}</ol>
      )}</QueryState>
    </div>
  )
}

const SKIP = new Set(['id', 'created_at', 'updated_at', 'reviewed_at', 'evidence_ids', 'proposal', 'components', 'alternatives', 'import_row', 'features'])
function ChangeList({ before, after }: { before?: Record<string, unknown> | null; after?: Record<string, unknown> | null }) {
  if (!after) return null
  const keys = Object.keys(after).filter((k) => !SKIP.has(k) && JSON.stringify(after[k]) !== JSON.stringify(before?.[k]))
  if (!keys.length) return null
  const v = (x: unknown) => (x == null || x === '' ? '—' : Array.isArray(x) ? x.join(', ') : typeof x === 'object' ? '…' : String(x))
  return <ul className="mt-1 space-y-0.5 text-xs text-slate-600">{keys.map((k) => <li key={k}><span className="text-slate-500">{k}:</span> {v(before?.[k])} → <b>{v(after[k])}</b></li>)}</ul>
}

/* ------------------------------------------------------------------ re-analysis */

function Reanalyze({ projectId }: { projectId: string }) {
  const [diff, setDiff] = useState<Schemas['ReanalysisDiff'] | null>(null)
  const { toast } = useToast()
  const m = useApiMutation<void, Schemas['ReanalysisDiff']>({
    fn: async () => unwrap(await api.POST('/api/projects/{project_id}/reanalyze', { params: { path: { project_id: projectId } } })),
    invalidate: [['events', projectId], ['project', projectId]],
    onSuccess: (d) => setDiff(d),
    onError: (e) => toast({ kind: 'error', title: 'Przeliczenie nie powiodło się', description: String(e) }),
  })
  const sec = (t: string, xs: { title?: string | null; event_type: string }[], v: 'success' | 'info' | 'danger') => (
    <div><h3 className="mb-1 text-sm font-semibold">{t} <Badge variant={v}>{xs.length}</Badge></h3>
      <ul className="list-disc pl-5 text-sm">{xs.map((x, i) => <li key={i}>{x.title ?? x.event_type}</li>)}</ul></div>)
  return (
    <>
      <Button variant="outline" loading={m.isPending} onClick={() => m.mutate()}>Przelicz zdarzenia</Button>
      <Dialog open={!!diff} onClose={() => setDiff(null)} title="Co zmieniło się po przeliczeniu" description="Twoje wcześniejsze decyzje nie zostały nadpisane. Różnice czekają na Twoją ocenę."
        footer={<Button onClick={() => setDiff(null)}>OK</Button>}>
        {diff && <div className="space-y-3">
          {sec('Nowe zdarzenia', diff.new ?? [], 'success')}
          {sec('Zmienione (czekają na decyzję)', (diff.changed ?? []).map((c) => (c.event ?? {}) as { title?: string; event_type: string }), 'info')}
          {sec('Bez zmian', diff.confirmed ?? [], 'info')}
          {sec('Już nie występują w danych', diff.closed ?? [], 'danger')}
        </div>}
      </Dialog>
    </>
  )
}
