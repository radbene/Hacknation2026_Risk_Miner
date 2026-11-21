import { Link, useNavigate } from '@tanstack/react-router'
import { ExternalLink, FileUp, Link2, RefreshCw, Sparkles } from 'lucide-react'
import { useRef, useState } from 'react'
import {
  useCandidates, useContracts, useDocuments, useEvents, useHistory, useIssues, useLinks, useNotices, useProcedures, useProject,
} from '@/api/cases'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { TimelineTab } from '@/components/case/TimelineTab'
import { GraphTab } from '@/components/case/GraphTab'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { NoticeView } from '@/components/evidence/NoticeView'
import { JobRunner } from '@/components/JobRunner'
import { Completeness, LinkStatusBadge, RiskCodes } from '@/components/LinkStatusBadge'
import { MethodConfidence } from '@/components/MethodConfidence'
import { PageHeader } from '@/components/PageHeader'
import { ReviewActions } from '@/components/ReviewActions'
import { StatusBadge } from '@/components/StatusBadge'
import {
  Badge, Button, Card, CardContent, CardHeader, DataTable, Dialog, Input, Label, QueryState, Tabs, Textarea, useToast,
  type ColumnDef,
} from '@/components/ui'
import { ACTION_LABEL, EVENT_TYPE_LABEL, OBJECT_TYPE_LABEL } from '@/lib/labels'
import { cn, fmtDate, fmtDateTime, fmtNum, fmtPln } from '@/lib/utils'
import { projectRoute } from '@/router'

const NOTICE_PL: Record<string, string> = {
  ContractNotice: 'Ogłoszenie o zamówieniu', TenderResultNotice: 'Ogłoszenie o wyniku', AgreementUpdateNotice: 'Zmiana umowy',
  ContractPerformingNotice: 'Wykonanie umowy',
}
const EVENT_PL: Record<string, string> = {
  ...EVENT_TYPE_LABEL, late: 'Opóźnienie', paid_above_value: 'Wypłata powyżej wartości umowy', change_deadline: 'Zmiana terminu',
  change_value: 'Zmiana wynagrodzenia', change_scope: 'Zmiana zakresu', repeated: 'Powtórzone postępowanie', improper: 'Nienależyte wykonanie / kary',
  cancelled: 'Unieważnienie', single_offer: 'Jedna oferta', over_budget: 'Oferty powyżej budżetu', not_performed: 'Niewykonanie',
  terminated: 'Rozwiązanie umowy', document_fragment: 'Fragment dokumentu',
}
const ISSUE_V: Record<string, 'success' | 'warning' | 'danger' | 'default' | 'info'> = {
  potwierdzone: 'success', 'częściowe': 'warning', brak: 'default', sprzeczne: 'danger',
  nie_ma_w_paczce: 'default', dokument_nie_wspomina: 'info', brak_potwierdzenia: 'warning', potwierdzono_niewykonanie: 'danger',
}
const ISSUE_L: Record<string, string> = {
  nie_ma_w_paczce: 'nie ma w paczce', dokument_nie_wspomina: 'dokument nie wspomina', brak_potwierdzenia: 'brak potwierdzenia',
  potwierdzono_niewykonanie: 'potwierdzono, że nie wykonano',
}

export default function ProjectCard() {
  const { projectId } = projectRoute.useParams()
  const s = projectRoute.useSearch()
  const navigate = useNavigate({ from: '/projekty/$projectId' })
  const tab = s.tab ?? 'przeglad'
  const setTab = (t: string) => navigate({ search: { ...s, tab: t, notice: undefined }, replace: true })
  const p = useProject(projectId)
  const events = useEvents(projectId)
  const issues = useIssues(projectId)
  const links = useLinks(projectId)

  return (
    <QueryState q={p}>{(d) => (
      <div>
        <PageHeader back title={<span><span className="mr-2 font-mono text-base text-brand">{d.code}</span>{d.title}</span>}
          description={<>{d.beneficiary_name} · {d.voivodeship ?? '—'} · {d.subsector_main ?? 'podsektor nieustalony'} · warstwa {d.tier === 'deep' ? 'pogłębiona' : 'automatyczna'}</>}
          actions={<>
            <JobRunner label="Wzbogać" icon={<RefreshCw size={14} />} variant="outline"
              invalidate={[['project', projectId], ['links', projectId], ['events', projectId]]}
              start={async () => unwrap(await api.POST('/api/enrich', { body: { project_ids: [projectId], sources: null, as_of: null } }))} />
            <Reanalyze projectId={projectId} />
          </>}>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <LinkStatusBadge status={d.link_status} /><StatusBadge status={d.status} />
            <span className="text-slate-500">Kompletność</span><Completeness value={d.completeness} />
            {d.n_pending_review > 0 && <Badge variant="warning">{d.n_pending_review} do przeglądu</Badge>}
          </div>
        </PageHeader>
        <Tabs value={tab} onChange={setTab} tabs={[
          { value: 'przeglad', label: 'Przegląd' },
          { value: 'os', label: 'Oś czasu' },
          { value: 'powiazania', label: 'Powiązania', count: links.data?.length },
          { value: 'umowy', label: 'Umowy i zmiany' },
          { value: 'zdarzenia', label: 'Zdarzenia i przyczyny', count: events.data?.length },
          { value: 'ogloszenia', label: 'Ogłoszenia' },
          { value: 'dokumenty', label: 'Dokumenty' },
          { value: 'braki', label: 'Braki i sprzeczności', count: issues.data?.length },
          { value: 'graf', label: 'Relacje' },
          { value: 'historia', label: 'Historia' },
        ]}>
          {tab === 'przeglad' && <Overview d={d} />}
          {tab === 'os' && <TimelineTab projectId={projectId} />}
          {tab === 'powiazania' && <LinksTab projectId={projectId} />}
          {tab === 'umowy' && <ContractsTab projectId={projectId} />}
          {tab === 'zdarzenia' && <EventsTab projectId={projectId} />}
          {tab === 'ogloszenia' && <NoticesTab projectId={projectId} selected={s.notice} section={s.section} quote={s.quote}
            onSelect={(id) => navigate({ search: { ...s, notice: id }, replace: true })} />}
          {tab === 'dokumenty' && <DocumentsTab projectId={projectId} />}
          {tab === 'braki' && <IssuesTab projectId={projectId} />}
          {tab === 'graf' && <GraphTab projectId={projectId} />}
          {tab === 'historia' && <HistoryTab projectId={projectId} />}
        </Tabs>
      </div>
    )}</QueryState>
  )
}

/* ------------------------------------------------------------------ overview */

const XLSX_FIELDS: [keyof Schemas['ProjectDetail'], string][] = [
  ['public_id_type', 'Typ identyfikatora'], ['public_id_value', 'Identyfikator publiczny'], ['record_scope', 'Zakres rekordu'],
  ['project_status', 'Status projektu'], ['funding', 'Finansowanie'], ['work_type', 'Rodzaj robót'], ['formula', 'Formuła'],
  ['city', 'Miejscowość'], ['teryt', 'TERYT'], ['voivodeship', 'Województwo'],
]

function Overview({ d }: { d: Schemas['ProjectDetail'] }) {
  const ev = ((d.import_row as Record<string, unknown> | null)?.evidence ?? {}) as Record<string, string>
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader title="Opis przedsięwzięcia" description="Z pliku organizatora (xlsx) – każda wartość z adresem komórki." actions={<BlockLabel label="dane_zrodlowe" />} />
        <CardContent className="space-y-3 text-sm">
          <p className="whitespace-pre-line text-slate-700">{d.description ?? '—'}</p>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
            {XLSX_FIELDS.map(([k, label]) => (
              <div key={k} className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1">
                <dt className="text-xs text-slate-500">{label}</dt>
                <dd className="flex items-center gap-1 text-right text-sm">{String(d[k] ?? '—')}{ev[k as string] && <EvidenceChip ids={[ev[k as string]]} label="xlsx" />}</dd>
              </div>
            ))}
            <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1"><dt className="text-xs text-slate-500">Wartość projektu</dt>
              <dd className="text-sm">{fmtPln(d.project_value)}</dd></div>
            <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1"><dt className="text-xs text-slate-500">Dofinansowanie</dt>
              <dd className="text-sm">{fmtPln(d.grant_value)}</dd></div>
          </dl>
          {d.annotation && <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs"><b>Adnotacja instytucji:</b> {d.annotation}</div>}
        </CardContent>
      </Card>
      <div className="space-y-4">
        <Card>
          <CardHeader title="Beneficjent" />
          <CardContent className="text-sm">
            <div className="font-medium">{d.beneficiary?.name ?? d.beneficiary_name}</div>
            <div className="text-xs text-slate-500">NIP {d.beneficiary?.nip ?? d.beneficiary_nip ?? '—'} · REGON {d.beneficiary?.regon ?? '—'}</div>
            <div className="text-xs text-slate-500">{d.beneficiary?.city} {d.beneficiary?.province}</div>
            {!!d.beneficiary?.verified_by?.length && <div className="mt-1 text-xs">Zweryfikowano: {d.beneficiary.verified_by.join(', ')}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader title="Decyzja eksperta" description="Zatwierdź dane projektu lub popraw pole – każda zmiana trafia do historii." />
          <CardContent>
            <ReviewActions objectType="project" objectId={d.id} status={d.status} exemplary={d.exemplary} proposal={d.proposal}
              values={d as unknown as Record<string, unknown>}
              editFields={[{ key: 'title', label: 'Tytuł' }, { key: 'description', label: 'Opis', type: 'longtext' },
                { key: 'subsector_main', label: 'Podsektor' }, { key: 'work_type', label: 'Rodzaj robót' }, { key: 'formula', label: 'Formuła' },
                { key: 'public_id_value', label: 'Identyfikator publiczny' }, { key: 'project_status', label: 'Status projektu' }]}
              invalidate={[['project', d.id]]} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ links */

function LinksTab({ projectId }: { projectId: string }) {
  const links = useLinks(projectId)
  const cands = useCandidates(projectId)
  const [relink, setRelink] = useState(false)
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title="Powiązane postępowania BZP" description="Metoda, pewność i składowe dopasowania – każda ze źródłem. Propozycje systemu czekają na decyzję eksperta."
          actions={<Button size="sm" variant="outline" onClick={() => setRelink(true)}><Link2 size={14} />Wskaż inne postępowanie</Button>} />
        <CardContent>
          <QueryState q={links} empty={(l) => l.length === 0}>{(ls) => (
            <div className="space-y-3">
              {ls.map((l) => (
                <div key={l.id} className={cn('rounded-md border p-3', l.status === 'rejected' ? 'border-rose-200 bg-rose-50/40 opacity-70' : 'border-slate-200')}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{l.procedure_title}</div>
                      <div className="text-xs text-slate-500">{l.bzp_number} · <span className="font-mono">{l.ocid}</span>{l.part_no ? ` · część ${l.part_no}` : ''}
                        {l.is_override && <Badge variant="violet" className="ml-1">decyzja eksperta</Badge>}</div>
                    </div>
                    <div className="flex items-center gap-2"><MethodConfidence method={l.method} confidence={l.confidence} /><StatusBadge status={l.status} /></div>
                  </div>
                  <ComponentsTable comps={l.components} />
                  {!!l.alternatives?.length && (
                    <details className="mt-2 text-xs"><summary className="cursor-pointer text-slate-600">Alternatywy odrzucone przez system ({l.alternatives.length})</summary>
                      <ul className="mt-1 space-y-1">{l.alternatives.map((a, i) => (
                        <li key={i} className="rounded bg-slate-50 p-1.5"><b>{fmtNum(a.score)}</b> · {a.bzp_number ?? a.ocid} – {a.title}
                          {a.why_not && <div className="text-amber-700">Dlaczego nie: {a.why_not}</div>}</li>))}</ul></details>)}
                  <div className="mt-2"><ReviewActions objectType="project_procedure" objectId={l.id} status={l.status} proposal={l.proposal}
                    onRelink={() => setRelink(true)} invalidate={[['links', projectId], ['project', projectId]]} /></div>
                </div>
              ))}
            </div>
          )}</QueryState>
        </CardContent>
      </Card>
      <Card>
        <CardHeader title="Kandydaci (wszystkie postępowania beneficjenta)" description="Świeże przeliczenie dopasowania – nic nie jest zapisywane." actions={<BlockLabel label="obliczenia" />} />
        <CardContent>
          <QueryState q={cands} empty={(c) => c.length === 0}>{(cs) => (
            <DataTable dense data={cs} getRowId={(r) => String(r.procedure_id)} columns={[
              { accessorKey: 'score', header: 'Wynik', cell: ({ getValue }) => <span className="tabular-nums font-semibold">{fmtNum(getValue() as number, 3)}</span> },
              { accessorKey: 'bzp_number', header: 'Ogłoszenie', cell: ({ row }) => <span className="font-mono text-xs">{row.original.bzp_number ?? row.original.ocid}</span> },
              { accessorKey: 'title', header: 'Tytuł', cell: ({ getValue }) => <span className="line-clamp-2 max-w-xl text-xs">{String(getValue() ?? '')}</span> },
              { id: 'comps', header: 'Składowe', cell: ({ row }) => <span className="text-[11px] text-slate-600">{(row.original.components ?? []).map((c) => `${c.name} ${fmtNum(c.score)}`).join(' · ')}</span> },
            ] as ColumnDef<Schemas['LinkCandidate']>[]} />
          )}</QueryState>
        </CardContent>
      </Card>
      <RelinkDialog open={relink} onClose={() => setRelink(false)} projectId={projectId} candidates={cands.data ?? []} />
    </div>
  )
}

function ComponentsTable({ comps }: { comps?: Schemas['LinkComponent'][] }) {
  if (!comps?.length) return null
  return (
    <table className="mt-2 w-full text-xs">
      <thead className="text-left text-slate-500"><tr><th className="py-0.5 font-medium">Składowa</th><th className="font-medium">Wynik</th><th className="font-medium">Waga</th><th className="font-medium">Wyjaśnienie</th><th /></tr></thead>
      <tbody>{comps.map((c, i) => (
        <tr key={i} className="border-t border-slate-100">
          <td className="py-0.5 font-mono">{c.name}</td>
          <td className={cn('tabular-nums', c.score >= 0.8 ? 'text-emerald-700' : c.score < 0.5 ? 'text-rose-700' : 'text-amber-700')}>{fmtNum(c.score)}</td>
          <td className="tabular-nums text-slate-500">{c.weight == null ? '—' : fmtNum(c.weight)}</td>
          <td className="text-slate-700">{c.detail}</td>
          <td>{c.evidence_id && <EvidenceChip ids={[c.evidence_id]} />}</td>
        </tr>))}</tbody>
    </table>
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
    onSuccess: () => { toast({ kind: 'success', title: 'Powiązanie zmienione', description: 'Zapisano jako decyzję eksperta (przetrwa ponowne przeliczenie).' }); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zmienić powiązania', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title="Wskaż właściwe postępowanie" description="Wybierz kandydata albo podaj numer ogłoszenia BZP (zostanie pobrane z BZP)."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button>
        <Button loading={m.isPending} disabled={!sel && !notice.trim() || !comment.trim()}
          onClick={() => m.mutate({ procedure_id: sel || null, notice_number: notice.trim() || null, part_no: part ? Number(part) : null, comment, ocid: null })}>Zapisz powiązanie</Button></>}>
      <div className="space-y-3 text-sm">
        <div className="max-h-64 space-y-1 overflow-auto">
          {candidates.map((c) => (
            <label key={String(c.procedure_id)} className={cn('flex cursor-pointer items-start gap-2 rounded border p-2', sel === c.procedure_id ? 'border-brand bg-brand-soft' : 'border-slate-200')}>
              <input type="radio" name="cand" className="mt-1 accent-brand" checked={sel === c.procedure_id} onChange={() => { setSel(String(c.procedure_id)); setNotice('') }} />
              <span><b className="tabular-nums">{fmtNum(c.score, 3)}</b> · <span className="font-mono text-xs">{c.bzp_number}</span><br /><span className="text-xs">{c.title}</span></span>
            </label>))}
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-2"><Label htmlFor="rl-n">…albo numer ogłoszenia BZP</Label>
            <Input id="rl-n" value={notice} onChange={(e) => { setNotice(e.target.value); setSel('') }} placeholder="2023/BZP 00110672/01" /></div>
          <div><Label htmlFor="rl-p">Część</Label><Input id="rl-p" type="number" min={1} value={part} onChange={(e) => setPart(e.target.value)} /></div>
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
      <QueryState q={procs} empty={(x) => x.length === 0}>{(ps) => (
        <div className="grid gap-3 md:grid-cols-2">{ps.map((p) => (
          <Card key={p.id}>
            <CardHeader title={p.title} description={<><span className="font-mono">{p.bzp_number}</span> · {p.mode ?? 'tryb ?'} · CPV {p.cpv_main ?? '—'}</>}
              actions={<EvidenceChip ids={p.evidence_ids} />} />
            <CardContent className="grid grid-cols-2 gap-2 text-xs">
              <Kv k="Wartość szacunkowa (netto)" v={fmtPln(p.est_value_net)} />
              <Kv k="Kwota na sfinansowanie (brutto)" v={fmtPln(p.budget_gross)} />
              <Kv k="Liczba ofert" v={p.offers_count ?? '—'} />
              <Kv k="Okres realizacji" v={p.planned_period_text ?? (p.planned_days ? `${p.planned_days} dni` : '—')} />
              <Kv k="Części" v={p.parts ?? 1} />
              <Kv k="Środki UE" v={p.eu_funded == null ? '—' : p.eu_funded ? `tak${p.eu_project_ref ? ` (${p.eu_project_ref})` : ''}` : 'nie'} />
              {p.cancelled && <div className="col-span-2"><Badge variant="danger">Unieważnione: {p.cancel_basis}</Badge></div>}
            </CardContent>
          </Card>))}</div>
      )}</QueryState>
      <QueryState q={contracts} empty={(x) => x.length === 0}>{(cs) => (
        <div className="space-y-3">{cs.map((c) => {
          const delay = c.actual_end && c.planned_end ? Math.round((+new Date(c.actual_end) - +new Date(c.planned_end)) / 86400000) : null
          return (
            <Card key={c.id}>
              <CardHeader title={`Umowa${c.part_no ? ` – część ${c.part_no}` : ''}`}
                description={c.contractor ? `Wykonawca: ${c.contractor.natural_person_flag ? 'osoba fizyczna (dane ukryte)' : c.contractor.name}${c.contractor.nip && !c.contractor.natural_person_flag ? ` · NIP ${c.contractor.nip}` : ''}` : undefined}
                actions={<><EvidenceChip ids={c.evidence_ids} /><StatusBadge status={c.status} /></>} />
              <CardContent>
                <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                  <Kv k="Zawarta" v={fmtDate(c.signed_at)} />
                  <Kv k="Wartość (brutto)" v={fmtPln(c.value_gross)} />
                  <Kv k="Planowany koniec" v={fmtDate(c.planned_end)} />
                  <Kv k="Faktyczny koniec" v={fmtDate(c.actual_end)} />
                  <Kv k="Wypłacono (brutto)" v={fmtPln(c.paid_gross)} warn={!!(c.paid_gross && c.value_gross && c.paid_gross > c.value_gross)} />
                  <Kv k="Opóźnienie" v={delay == null ? '—' : `${delay} dni`} warn={(delay ?? 0) > 0} />
                  <Kv k="W terminie" v={c.on_time == null ? '—' : c.on_time ? 'tak' : 'nie'} warn={c.on_time === false} />
                  <Kv k="Należycie" v={c.proper == null ? '—' : c.proper ? 'tak' : 'nie'} warn={c.proper === false} />
                </div>
                {!!c.changes?.length && (
                  <div className="mt-3">
                    <h3 className="mb-1 text-xs font-semibold text-slate-700">Zmiany umowy ({c.changes.length})</h3>
                    <ul className="space-y-2">{c.changes.map((ch) => (
                      <li key={ch.id} className="rounded border border-slate-200 p-2 text-xs">
                        <div className="flex flex-wrap items-center gap-2"><b>Zmiana nr {ch.change_no}</b>
                          {ch.change_date && <span>{fmtDate(ch.change_date)}</span>}
                          {ch.legal_basis_code && <Badge variant="info">{ch.legal_basis_code}</Badge>}
                          {ch.new_end && <Badge>nowy termin {fmtDate(ch.new_end)}</Badge>}
                          {ch.value_delta != null && <Badge>{ch.value_delta > 0 ? '+' : ''}{fmtPln(ch.value_delta)}</Badge>}
                          <EvidenceChip ids={ch.evidence_ids} />
                        </div>
                        {ch.legal_basis && <div className="mt-1 text-slate-500">{ch.legal_basis}</div>}
                        {ch.reason && <div className="mt-1 text-slate-700">„{ch.reason}”</div>}
                      </li>))}</ul>
                  </div>)}
              </CardContent>
            </Card>)
        })}</div>
      )}</QueryState>
    </div>
  )
}

function Kv({ k, v, warn }: { k: string; v: React.ReactNode; warn?: boolean }) {
  return <div><div className="text-slate-500">{k}</div><div className={cn('font-medium', warn && 'text-rose-700')}>{v}</div></div>
}

/* ------------------------------------------------------------------ events */

function EventsTab({ projectId }: { projectId: string }) {
  const ev = useEvents(projectId)
  return (
    <QueryState q={ev} empty={(x) => x.length === 0}>{(items) => (
      <div className="space-y-3">{items.map((e) => (
        <Card key={e.id} className={cn(e.status === 'rejected' && 'opacity-60')}>
          <CardHeader title={<span className="flex flex-wrap items-center gap-2">{e.title ?? EVENT_PL[e.event_type] ?? e.event_type}<RiskCodes codes={e.risk_codes} />{e.exemplary && <Badge variant="violet">wzorcowe</Badge>}</span>}
            description={<>{EVENT_PL[e.event_type] ?? e.event_type} · {fmtDate(e.event_date)}</>}
            actions={<><BlockLabel label={e.model_label ? 'wniosek_modelu' : 'dane_zrodlowe'} /><MethodConfidence method={e.method} confidence={e.confidence} compact /><StatusBadge status={e.status} /></>} />
          <CardContent className="space-y-2 text-sm">
            {e.quote && <blockquote className="border-l-2 border-teal-400 bg-teal-50/40 py-1 pl-2 text-xs text-slate-700">„{e.quote}” <EvidenceChip ids={e.evidence_ids} /></blockquote>}
            {!e.quote && <EvidenceChip ids={e.evidence_ids} />}
            <dl className="grid gap-x-4 gap-y-1 text-xs sm:grid-cols-2">
              {e.cause && <div><dt className="text-slate-500">Przyczyna</dt><dd>{e.cause}</dd></div>}
              {e.effect && <div><dt className="text-slate-500">Skutek</dt><dd>{e.effect}
                {e.effect_days != null && ` · ${fmtNum(e.effect_days, 0)} dni`}{e.effect_pln != null && ` · ${fmtPln(e.effect_pln)}`}{e.effect_pct != null && ` · ${fmtNum(e.effect_pct, 1)}%`}</dd></div>}
              {e.signal && <div><dt className="text-slate-500">Sygnał</dt><dd>{e.signal}</dd></div>}
              {e.mitigation && <div><dt className="text-slate-500">Działanie zaradcze</dt><dd>{e.mitigation}{e.mitigation_effect && <Badge className="ml-1" variant={e.mitigation_effect === 'skuteczne' ? 'success' : 'warning'}>{e.mitigation_effect}</Badge>}</dd></div>}
            </dl>
            {e.model_label && <div className="text-[11px] text-violet-700">Wniosek modelu: {e.model_label}</div>}
            <ReviewActions objectType="event" objectId={e.id} status={e.status} exemplary={e.exemplary} proposal={e.proposal}
              values={e as unknown as Record<string, unknown>}
              editFields={[{ key: 'risk_codes', label: 'Kategorie ryzyka', type: 'rcodes' }, { key: 'cause', label: 'Przyczyna', type: 'longtext' },
                { key: 'effect', label: 'Skutek', type: 'longtext' }, { key: 'mitigation', label: 'Działanie zaradcze', type: 'longtext' }]}
              invalidate={[['events', projectId]]} />
          </CardContent>
        </Card>))}</div>
    )}</QueryState>
  )
}

/* ------------------------------------------------------------------ notices */

function NoticesTab({ projectId, selected, section, quote, onSelect }: { projectId: string; selected?: string; section?: string; quote?: string; onSelect: (id: string) => void }) {
  const n = useNotices(projectId)
  return (
    <QueryState q={n} empty={(x) => x.length === 0}>{(ns) => {
      const cur = selected ?? ns[0]?.id
      return (
        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <ul className="space-y-1">{ns.map((x) => (
            <li key={x.id}><button onClick={() => onSelect(x.id)}
              className={cn('w-full rounded border p-2 text-left text-xs cursor-pointer', cur === x.id ? 'border-brand bg-brand-soft' : 'border-slate-200 hover:bg-slate-50')}>
              <div className="font-semibold">{NOTICE_PL[x.notice_type] ?? x.notice_type}</div>
              <div className="font-mono">{x.notice_number}</div>
              <div className="text-slate-500">{fmtDate(x.published_at)}</div>
            </button></li>))}</ul>
          <div>
            {cur && (() => {
              const x = ns.find((y) => y.id === cur)
              return (<>
                {x?.url && <a href={x.url} target="_blank" rel="noreferrer" className="mb-2 inline-flex items-center gap-1 text-xs text-brand hover:underline"><ExternalLink size={12} />Ogłoszenie w e-Zamówieniach (link stały)</a>}
                <NoticeView noticeId={cur} section={section} quote={quote} />
              </>)
            })()}
          </div>
        </div>
      )
    }}</QueryState>
  )
}

/* ------------------------------------------------------------------ documents */

function DocumentsTab({ projectId }: { projectId: string }) {
  const docs = useDocuments(projectId)
  const ref = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [url, setUrl] = useState('')
  const { toast } = useToast()
  const qc = docs.refetch
  async function upload(f: File) {
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', f)
      fd.append('project_id', projectId)
      const headers: Record<string, string> = {}
      const u = localStorage.getItem('rm_user'); if (u) headers['X-User'] = u
      const r = await fetch('/api/documents', { method: 'POST', body: fd, headers })
      if (!r.ok) throw new Error(await r.text())
      toast({ kind: 'success', title: 'Dokument dodany', description: 'Tekst wyodrębniony, fragmenty ryzyka zaproponowane.' })
      qc()
    } catch (e) { toast({ kind: 'error', title: 'Nie udało się dodać dokumentu', description: String(e) }) } finally {
      setBusy(false); if (ref.current) ref.current.value = ''
    }
  }
  async function fromUrl() {
    setBusy(true)
    try {
      unwrap(await api.POST('/api/documents/from-url', { body: { url, project_id: projectId, analysis_id: null, doc_type: null } }))
      setUrl(''); qc()
    } catch (e) { toast({ kind: 'error', title: 'Nie udało się pobrać', description: String(e) }) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-2">
        <input ref={ref} type="file" className="hidden" accept=".pdf,.docx,.xlsx,.xls,.csv,.html,.htm,.txt" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} aria-label="Plik dokumentu" />
        <Button variant="outline" loading={busy} onClick={() => ref.current?.click()}><FileUp size={14} />Dodaj dokument (PDF, DOCX, XLSX)</Button>
        <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="…albo adres URL dokumentu" className="w-80" />
        <Button variant="outline" disabled={!url.startsWith('http')} loading={busy} onClick={fromUrl}>Pobierz</Button>
      </div>
      <QueryState q={docs} empty={(x) => x.length === 0}>{(ds) => (
        <DataTable data={ds} getRowId={(r) => r.id} columns={[
          { accessorKey: 'title', header: 'Dokument', cell: ({ row }) => (
            <Link to="/dokumenty/$documentId" params={{ documentId: row.original.id }} search={{}} className="font-medium text-brand hover:underline">{row.original.title ?? row.original.file_name}</Link>) },
          { accessorKey: 'doc_type', header: 'Typ', cell: ({ getValue }) => <Badge>{String(getValue() ?? '—')}</Badge> },
          { accessorKey: 'phase', header: 'Faza', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '—')}</span> },
          { accessorKey: 'pages', header: 'Strony' },
          { accessorKey: 'version', header: 'Wersja' },
          { accessorKey: 'text_status', header: 'Tekst', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '—')}</span> },
          { accessorKey: 'created_at', header: 'Dodano', cell: ({ getValue }) => <span className="text-xs">{fmtDateTime(getValue() as string)}</span> },
        ] as ColumnDef<Schemas['DocumentOut']>[]} />
      )}</QueryState>
    </div>
  )
}

/* ------------------------------------------------------------------ issues */

function IssuesTab({ projectId }: { projectId: string }) {
  const c = useApi(['project', projectId, 'completeness'], async () =>
    unwrap(await api.GET('/api/projects/{project_id}/completeness', { params: { path: { project_id: projectId } } })))
  return (
    <QueryState q={c}>{(d) => (
      <div className="space-y-3">
        <div className="flex items-center gap-3 text-sm"><span>Kompletność danych projektu:</span><Completeness value={d.score} /><BlockLabel label="obliczenia" /></div>
        <p className="text-xs text-slate-500">Stany wg eksperta nie są równoważne: <b>nie ma w paczce</b> (nie znaczy, że dokument nie istnieje) · <b>dokument nie wspomina</b> · <b>brak potwierdzenia</b> · <b>potwierdzono, że nie wykonano</b>; <b>sprzeczne</b> – źródła podają różne wartości.</p>
        <DataTable data={d.items} getRowId={(r) => r.id} columns={[
          { accessorKey: 'state', header: 'Stan', cell: ({ getValue }) => <Badge variant={ISSUE_V[String(getValue())] ?? 'default'}>{ISSUE_L[String(getValue())] ?? String(getValue() ?? '—')}</Badge> },
          { accessorKey: 'field', header: 'Pole', cell: ({ getValue }) => <span className="font-mono text-xs">{String(getValue() ?? '')}</span> },
          { accessorKey: 'message', header: 'Opis', cell: ({ row }) => <div className="max-w-xl text-xs">{row.original.message}</div> },
          { accessorKey: 'what_to_add', header: 'Co uzupełnić', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '')}</span> },
          { accessorKey: 'impact', header: 'Wpływ na analizę', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '')}</span> },
          { id: 'ev', header: 'Źródło', cell: ({ row }) => row.original.evidence_ids?.length ? <EvidenceChip ids={row.original.evidence_ids} /> : null },
        ] as ColumnDef<Schemas['DataIssueOut']>[]} />
      </div>
    )}</QueryState>
  )
}

/* ------------------------------------------------------------------ history */

function HistoryTab({ projectId }: { projectId: string }) {
  const h = useHistory(projectId)
  return (
    <QueryState q={h} empty={(x) => x.length === 0}>{(items) => (
      <ol className="space-y-2">{items.map((r) => (
        <li key={r.id} className="rounded border border-slate-200 bg-white p-2 text-xs">
          <div className="flex flex-wrap items-center gap-2"><b>{fmtDateTime(r.at)}</b><span>{r.reviewer}</span>
            <Badge>{ACTION_LABEL[r.action] ?? r.action}</Badge><span className="text-slate-500">{OBJECT_TYPE_LABEL[r.object_type] ?? r.object_type}</span></div>
          {r.comment && <div className="mt-1 text-slate-700">„{r.comment}”</div>}
          {r.after && <details className="mt-1"><summary className="cursor-pointer text-slate-500">Zmiana</summary>
            <pre className="mt-1 max-h-48 overflow-auto rounded bg-slate-50 p-2 text-[11px]">{JSON.stringify({ przed: r.before, po: r.after }, null, 1)}</pre></details>}
        </li>))}</ol>
    )}</QueryState>
  )
}

/* ------------------------------------------------------------------ re-analysis */

function Reanalyze({ projectId }: { projectId: string }) {
  const [diff, setDiff] = useState<Schemas['ReanalysisDiff'] | null>(null)
  const { toast } = useToast()
  const m = useApiMutation<void, Schemas['ReanalysisDiff']>({
    fn: async () => unwrap(await api.POST('/api/projects/{project_id}/reanalyze', { params: { path: { project_id: projectId } } })),
    invalidate: [['events', projectId], ['project', projectId]],
    onSuccess: (d) => setDiff(d),
    onError: (e) => toast({ kind: 'error', title: 'Ponowna analiza nie powiodła się', description: String(e) }),
  })
  const sec = (t: string, xs: { title?: string | null; event_type: string }[], v: 'success' | 'info' | 'danger') => (
    <div><h3 className="mb-1 text-xs font-semibold">{t} <Badge variant={v}>{xs.length}</Badge></h3>
      <ul className="list-disc pl-5 text-xs">{xs.map((x, i) => <li key={i}>{x.title ?? x.event_type}</li>)}</ul></div>)
  return (
    <>
      <Button variant="outline" loading={m.isPending} onClick={() => m.mutate()}><Sparkles size={14} />Analizuj ponownie</Button>
      <Dialog open={!!diff} onClose={() => setDiff(null)} title="Wynik ponownej analizy" description="Co się zmieniło po przeliczeniu reguł na aktualnych danych. Decyzje eksperta nie zostały nadpisane."
        footer={<Button onClick={() => setDiff(null)}>OK</Button>}>
        {diff && <div className="space-y-3">
          {sec('Nowe', diff.new ?? [], 'success')}
          {sec('Zmienione (propozycja do przeglądu)', (diff.changed ?? []).map((c) => (c.event ?? {}) as { title?: string; event_type: string }), 'info')}
          {sec('Potwierdzone', diff.confirmed ?? [], 'info')}
          {sec('Zamknięte (nie występują w nowych danych)', diff.closed ?? [], 'danger')}
        </div>}
      </Dialog>
    </>
  )
}
