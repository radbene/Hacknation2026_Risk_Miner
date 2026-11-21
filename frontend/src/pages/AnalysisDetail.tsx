import { Link, useNavigate } from '@tanstack/react-router'
import { Check, Download, EyeOff, RefreshCw, RotateCcw, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, rawFetch, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { FeaturesForm, type Features } from '@/components/analysis/FeaturesForm'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { RiskCodes } from '@/components/LinkStatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { Badge, Button, Card, CardContent, CardHeader, QueryState, Tabs, useToast } from '@/components/ui'
import { cn, fmtNum, fmtPct, fmtPln } from '@/lib/utils'
import { analysisRoute } from '@/router'

type A = Schemas['AnalysisOut']
type Item = Schemas['AnalysisItemOut']
type P = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

const SEV_V: Record<string, 'danger' | 'warning' | 'default'> = { wysoka: 'danger', 'średnia': 'warning', niska: 'default' }
const LEVEL_PL: Record<string, string> = { neighbours: 'sąsiedzi', subsector: 'podsektor', wodkan: 'wod-kan', works: 'wszystkie roboty' }
const AXIS_PL: Record<string, string> = { realizacja: 'ryzyko realizacji', 'postępowanie': 'postępowanie', przygotowanie: 'przygotowanie', dane: 'braki danych' }

export default function AnalysisDetail() {
  const { analysisId } = analysisRoute.useParams()
  const s = analysisRoute.useSearch()
  const navigate = useNavigate({ from: '/analizy/$analysisId' })
  const tab = s.tab ?? 'flagi'
  const q = useApi(['analysis', analysisId], async () => unwrap(await api.GET('/api/analyses/{analysis_id}', { params: { path: { analysis_id: analysisId } } })))
  const recompute = useApiMutation<void, A>({
    fn: async () => unwrap(await api.POST('/api/analyses/{analysis_id}/recompute', { params: { path: { analysis_id: analysisId } } })),
    invalidate: [['analysis', analysisId]],
  })
  return (
    <QueryState q={q}>{(a) => {
      const by = (k: string) => (a.items ?? []).filter((i) => i.kind === k)
      return (
        <div>
          <PageHeader back title={a.title}
            description={<>Analiza nowej inwestycji · wersja {a.version} · {a.created_by ?? '—'} · baza: {String((a.summary as P).n_cases ?? '—')} przypadków
              {(a.summary as P).cases_by_tier && <> ({Object.entries((a.summary as P).cases_by_tier).map(([k, v]) => `${k === 'deep' ? 'pogłębione' : 'automatyczne'} ${v}`).join(', ')})</>}</>}
            actions={<>
              <Button variant="outline" loading={recompute.isPending} onClick={() => recompute.mutate()}><RefreshCw size={14} />Przelicz</Button>
              {(['docx', 'json', 'csv'] as const).map((f) => <ExportButton key={f} id={a.id} format={f} title={a.title} />)}
            </>} />
          <Summary a={a} />
          <Tabs value={tab} onChange={(t) => navigate({ search: { tab: t }, replace: true })} className="mt-4" tabs={[
            { value: 'flagi', label: 'Czerwone flagi', count: by('flag').length },
            { value: 'dzialania', label: 'Działania i klauzule', count: by('action').length },
            { value: 'ocena', label: 'Budżet i harmonogram', count: by('assessment').length },
            { value: 'zakresy', label: 'Zakresy z bazy', count: by('range').length },
            { value: 'sasiedzi', label: 'Podobne inwestycje', count: by('neighbour').filter((n) => !n.excluded).length },
            { value: 'cechy', label: 'Cechy inwestycji' },
          ]}>
            {tab === 'flagi' && <Flags items={by('flag')} a={a} />}
            {tab === 'dzialania' && <Actions items={by('action')} a={a} />}
            {tab === 'ocena' && <Assessment items={by('assessment')} a={a} />}
            {tab === 'zakresy' && <Ranges items={by('range')} a={a} />}
            {tab === 'sasiedzi' && <Neighbours items={by('neighbour')} a={a} />}
            {tab === 'cechy' && <FeaturesTab a={a} />}
          </Tabs>
        </div>
      )
    }}</QueryState>
  )
}

function ExportButton({ id, format, title }: { id: string; format: 'docx' | 'json' | 'csv'; title: string }) {
  const [busy, setBusy] = useState(false)
  return (
    <Button variant="outline" size="sm" loading={busy} onClick={async () => {
      setBusy(true)
      try {
        const r = await rawFetch(`/api/analyses/${id}/export?format=${format}`)
        const blob = await r.blob()
        const url = URL.createObjectURL(blob)
        const el = document.createElement('a')
        el.href = url; el.download = `${title.replace(/[^\p{L}\d]+/gu, '_').slice(0, 40)}.${format}`; el.click()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      } finally { setBusy(false) }
    }}><Download size={12} />{format.toUpperCase()}</Button>
  )
}

/* ------------------------------------------------------------------ summary */

function Summary({ a }: { a: A }) {
  const s = a.summary as P
  const pl = s.p_late ?? {}
  const dd = s.delay_days ?? {}
  const pr = s.paid_ratio ?? {}
  const b = s.budget ?? {}
  const tile = (label: string, value: React.ReactNode, sub?: React.ReactNode, warn?: boolean) => (
    <div className={cn('rounded-lg border bg-white p-3', warn ? 'border-rose-200' : 'border-slate-200')}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={cn('mt-0.5 text-2xl font-semibold tabular-nums', warn && 'text-rose-700')}>{value}</div>
      {sub && <div className="mt-0.5 text-[11px] text-slate-500">{sub}</div>}
    </div>)
  return (
    <div>
      <div className="mb-1 flex items-center gap-2"><BlockLabel label="obliczenia" /><span className="text-xs text-slate-500">Każda liczba z liczebnością n i poziomem odniesienia – szczegóły w zakładkach.</span></div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {tile('Prawdopodobieństwo opóźnienia', fmtPct(pl.estimate), <>n={pl.n ?? '—'} · {LEVEL_PL[pl.fallback_level] ?? pl.fallback_level} · 95% CI {fmtPct(pl.ci_low)}–{fmtPct(pl.ci_high)}</>, (pl.estimate ?? 0) >= 0.4)}
        {tile('Opóźnienie (P50 / P80)', <>{fmtNum(dd.p50, 0)} / {fmtNum(dd.p80, 0)} <span className="text-sm font-normal">dni</span></>, <>n={dd.n ?? '—'} · {LEVEL_PL[dd.fallback_level] ?? dd.fallback_level}</>)}
        {tile('Wypłata / wartość umowy (P80)', fmtNum(pr.p80, 2), <>P50 {fmtNum(pr.p50, 2)} · n={pr.n ?? '—'}</>, (pr.p80 ?? 0) > 1.05)}
        {tile('Budżet na tle sąsiadów', b.percentile != null ? `P${Math.round(b.percentile * 100)}` : '—',
          b.message ?? (b.reserve_p80 ? <>rezerwa P80: {fmtPln(b.reserve_p80.amount)}</> : b.position), b.percentile != null && b.percentile < 0.25)}
        {tile('Czerwone flagi', s.n_flags ?? 0, <>wysokie: {s.flags_high ?? 0} · <RiskCodes codes={s.risk_codes} /></>, (s.flags_high ?? 0) > 0)}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ item decision */

function ItemDecision({ a, it, allowExclude }: { a: A; it: Item; allowExclude?: boolean }) {
  const { toast } = useToast()
  const m = useApiMutation<Schemas['AnalysisItemPatch'], Item>({
    fn: async (body) => unwrap(await api.PATCH('/api/analyses/{analysis_id}/items/{item_id}', { params: { path: { analysis_id: a.id, item_id: it.id } }, body })),
    invalidate: [['analysis', a.id]],
    onSuccess: (_r, v) => v.excluded !== undefined && v.excluded !== null && toast({ kind: 'success', title: v.excluded ? 'Wykluczono – przeliczono analizę' : 'Przywrócono – przeliczono analizę' }),
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się', description: String(e) }),
  })
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <StatusBadge status={it.status} />
      {it.status !== 'approved' && <Button size="sm" variant="success" loading={m.isPending} onClick={() => m.mutate({ status: 'approved' })}><Check size={12} />Akceptuj</Button>}
      {it.status !== 'rejected' && <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate({ status: 'rejected' })}><X size={12} />Odrzuć</Button>}
      {it.status !== 'proposed' && <Button size="sm" variant="ghost" onClick={() => m.mutate({ status: 'proposed' })}><RotateCcw size={12} />Cofnij</Button>}
      {allowExclude && <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate({ excluded: !it.excluded })}>
        <EyeOff size={12} />{it.excluded ? 'Przywróć do porównania' : 'Wyklucz i przelicz'}</Button>}
    </div>
  )
}

/* ------------------------------------------------------------------ flags */

function Flags({ items, a }: { items: Item[]; a: A }) {
  if (!items.length) return <p className="text-sm text-slate-500">Brak flag.</p>
  return (
    <div className="space-y-3">{items.map((it) => {
      const p = it.payload as P
      return (
        <Card key={it.id} className={cn(it.status === 'rejected' && 'opacity-60')}>
          <CardHeader title={<span className="flex flex-wrap items-center gap-2"><Badge variant={SEV_V[p.severity] ?? 'default'}>{p.severity}</Badge>{it.title}</span>}
            description={<>{AXIS_PL[p.axis] ?? p.axis}{p.n != null && <> · n={p.n}{p.k != null && `, k=${p.k}`}</>}</>}
            actions={<><RiskCodes codes={it.risk_codes} /><BlockLabel label={it.label} /></>} />
          <CardContent className="space-y-2 text-sm">
            <p>{p.why}</p>
            {p.quote && <blockquote className="border-l-2 border-teal-400 bg-teal-50/40 py-1 pl-2 text-xs">„{p.quote}” <span className="text-slate-500">(opis inwestycji)</span></blockquote>}
            {!!p.examples?.length && (
              <details className="text-xs"><summary className="cursor-pointer text-slate-600">Przykłady z podobnych inwestycji ({p.examples.length})</summary>
                <ul className="mt-1 space-y-1">{p.examples.map((e: P) => (
                  <li key={e.event_id} className="rounded bg-slate-50 p-1.5">
                    <Link to="/projekty/$projectId" params={{ projectId: e.project_id }} search={{ tab: 'zdarzenia' }} className="font-medium text-brand hover:underline">{e.title}</Link>
                    {e.quote && <div className="text-slate-600">„{e.quote}”</div>} <EvidenceChip ids={e.evidence_ids} />
                  </li>))}</ul></details>)}
            {!!p.items?.length && (
              <ul className="list-disc pl-5 text-xs">{p.items.map((x: P) => <li key={x.no}>{x.no}. {x.item} <span className="text-slate-500">({x.guide_sections})</span> <RiskCodes codes={x.risk_codes} /></li>)}</ul>)}
            {p.formula && <p className="text-[11px] text-slate-500">Wzór: {p.formula}</p>}
            <ItemDecision a={a} it={it} />
          </CardContent>
        </Card>)
    })}</div>
  )
}

/* ------------------------------------------------------------------ actions */

function Actions({ items, a }: { items: Item[]; a: A }) {
  if (!items.length) return <p className="text-sm text-slate-500">Brak działań.</p>
  return (
    <div className="space-y-3">{items.map((it) => {
      const p = it.payload as P
      return (
        <Card key={it.id}>
          <CardHeader title={it.title} description={p.flags?.length ? <>flagi: {p.flags.join(', ')}</> : undefined}
            actions={<BlockLabel label={it.label} />} />
          <CardContent className="space-y-2 text-sm">
            {p.summary && <><p>{p.summary}</p><ol className="list-decimal pl-5 text-sm">{(p.top_actions ?? []).map((x: string, i: number) => <li key={i}>{x}</li>)}</ol>
              <p className="text-[11px] text-violet-700">Wniosek modelu ({p.model_label}) – wymaga weryfikacji eksperta.</p></>}
            {(p.clauses ?? []).map((c: P) => (
              <div key={c.id} className="rounded-md border border-slate-200 p-2">
                <div className="flex flex-wrap items-center gap-2 text-sm font-medium">{c.title}<Badge variant="info">{c.legal_basis}</Badge>
                  {c.status !== 'approved' && <Badge variant="warning" title="Klauzula z katalogu zespołu – zatwierdź w „Wiedza ekspercka”">projekt</Badge>}</div>
                <p className="mt-1 text-xs text-slate-700">{c.text}</p>
                {c.trigger && <p className="mt-0.5 text-[11px] text-slate-500">Kiedy: {c.trigger}</p>}
              </div>))}
            {(p.lessons ?? []).map((l: P) => (
              <div key={l.id} className="rounded-md bg-slate-50 p-2 text-xs"><b>Lekcja ({l.source_kind}):</b> {l.title} – {l.recommendation} <EvidenceChip ids={l.evidence_ids} /></div>))}
            {(p.examples ?? []).map((e: P) => (
              <div key={e.id} className="rounded-md bg-emerald-50 p-2 text-xs"><b>Wzorcowe zdarzenie:</b> {e.title} – {e.mitigation} {e.mitigation_effect && `(${e.mitigation_effect})`}</div>))}
            <ItemDecision a={a} it={it} />
          </CardContent>
        </Card>)
    })}</div>
  )
}

/* ------------------------------------------------------------------ assessment & ranges */

function Assessment({ items, a }: { items: Item[]; a: A }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">{items.map((it) => {
      const p = it.payload as P
      return (
        <Card key={it.id}>
          <CardHeader title={it.title} description={<>n={p.n ?? 0}{p.fallback_level && ` · ${LEVEL_PL[p.fallback_level] ?? p.fallback_level}`}{p.basis && ` · ${p.basis}`}</>} actions={<BlockLabel label={it.label} />} />
          <CardContent className="space-y-1 text-sm">
            {p.percentile != null && <div>Pozycja: <b>P{Math.round(p.percentile * 100)}</b> {p.position && <Badge>{p.position}</Badge>} {p.value != null && <span className="text-xs text-slate-500">(wartość {fmtNum(p.value)})</span>}</div>}
            {p.quantiles && <div className="text-xs text-slate-600">Sąsiedzi: {Object.entries(p.quantiles).map(([k, v]) => `${k} ${fmtNum(v as number)}`).join(' · ')}</div>}
            {p.reserve_p80 && <div className="text-xs">Rezerwa na poziomie P80 wypłaty: <b>{fmtPln(p.reserve_p80.amount)}</b> (×{fmtNum(p.reserve_p80.ratio)})</div>}
            {(p.p50 != null || p.p80 != null) && <div className="text-xs">P50 {fmtNum(p.p50)} · P80 {fmtNum(p.p80)} · P95 {fmtNum(p.p95)}</div>}
            {p.estimate != null && <div className="text-xs">Udział {fmtPct(p.estimate)} (k={p.k}, 95% CI {fmtPct(p.ci_low)}–{fmtPct(p.ci_high)})</div>}
            {p.message && <p className="rounded bg-amber-50 p-1.5 text-xs text-amber-900">{p.message}</p>}
            {p.status === 'not_compared' && <Badge variant="warning">nie porównano</Badge>}
            {p.formula && <p className="text-[11px] text-slate-500">Wzór: {p.formula}</p>}
            <ItemDecision a={a} it={it} />
          </CardContent>
        </Card>)
    })}</div>
  )
}

function Ranges({ items, a }: { items: Item[]; a: A }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs text-slate-500"><tr>
          <th className="px-3 py-2">Miara</th><th>n</th><th>Poziom</th><th>Okres</th><th>Estymata / P50</th><th>P80</th><th>P95</th><th>95% CI</th><th className="px-2">Decyzja</th></tr></thead>
        <tbody>{items.map((it) => {
          const p = it.payload as P
          const isProp = p.estimate !== undefined && p.p50 === undefined
          return (
            <tr key={it.id} className="border-t border-slate-100 align-top">
              <td className="px-3 py-2"><div className="font-medium">{it.title}</div><div className="max-w-md text-[11px] text-slate-500">{p.formula}</div></td>
              <td className="tabular-nums">{p.n}</td>
              <td className="text-xs">{LEVEL_PL[p.fallback_level] ?? p.fallback_level}</td>
              <td className="text-xs">{p.period ?? '—'}</td>
              <td className="tabular-nums">{isProp ? fmtPct(p.estimate) : fmtNum(p.p50)}</td>
              <td className="tabular-nums">{isProp ? '—' : fmtNum(p.p80)}</td>
              <td className="tabular-nums">{isProp ? '—' : fmtNum(p.p95)}</td>
              <td className="text-xs tabular-nums">{isProp ? `${fmtPct(p.ci_low)}–${fmtPct(p.ci_high)}` : '—'}</td>
              <td className="px-2"><ItemDecision a={a} it={it} /></td>
            </tr>)
        })}</tbody>
      </table>
    </div>
  )
}

/* ------------------------------------------------------------------ neighbours */

function Neighbours({ items, a }: { items: Item[]; a: A }) {
  const sorted = [...items].sort((x, y) => Number(x.excluded) - Number(y.excluded) || (y.payload as P).score - (x.payload as P).score)
  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Podobieństwo = suma ważona składowych (wagi z tabeli wiedzy „similarity_weights”). Wykluczenie sąsiada przelicza zakresy, ocenę i flagi.</p>
      {sorted.map((it) => {
        const p = it.payload as P
        const o = p.outcome ?? {}
        return (
          <Card key={it.id} className={cn(it.excluded && 'opacity-50')}>
            <CardHeader title={<span className="flex flex-wrap items-center gap-2"><span className="tabular-nums text-brand">{fmtNum(p.score, 3)}</span>
              <Link to="/projekty/$projectId" params={{ projectId: p.project_id }} search={{}} className="hover:underline">{p.title}</Link>
              <Badge>{p.tier === 'deep' ? 'pogłębiony' : 'automatyczny'}</Badge>{it.excluded && <Badge variant="danger">wykluczony</Badge>}</span>}
              description={<>{p.project_code} · {p.subsector_main ?? '—'}</>} actions={<EvidenceChip ids={o.evidence_ids} label="Wynik" />} />
            <CardContent className="space-y-2">
              <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-5">
                <div><div className="text-slate-500">Wartość umowy</div><b>{fmtPln(o.value_gross)}</b></div>
                <div><div className="text-slate-500">Opóźnienie</div><b className={cn((o.delay_days ?? 0) > 0 && 'text-rose-700')}>{o.delay_days == null ? '—' : `${o.delay_days} dni`}</b></div>
                <div><div className="text-slate-500">Wypłata / umowa</div><b>{fmtNum(o.paid_ratio)}</b></div>
                <div><div className="text-slate-500">Zmiany umowy</div><b>{o.n_changes ?? '—'}</b></div>
                <div><div className="text-slate-500">Unieważnione</div><b>{o.cancelled ? 'tak' : 'nie'}</b></div>
              </div>
              <table className="w-full text-xs">
                <thead className="text-left text-slate-500"><tr><th className="font-medium">Składowa</th><th className="font-medium">Podobieństwo</th><th className="font-medium">Waga</th><th className="font-medium">Wkład</th><th className="font-medium">Szczegóły</th></tr></thead>
                <tbody>{(p.breakdown ?? []).map((b: P) => (
                  <tr key={b.component} className="border-t border-slate-100">
                    <td>{b.label}</td>
                    <td className="tabular-nums">{b.similarity == null ? <span className="text-slate-400">brak danych</span> : fmtNum(b.similarity)}</td>
                    <td className="tabular-nums">{fmtNum(b.weight)}</td>
                    <td><span className="inline-block h-1.5 rounded bg-brand" style={{ width: `${Math.max(2, b.contribution * 200)}px` }} /> <span className="tabular-nums">{fmtNum(b.contribution, 3)}</span></td>
                    <td className="text-slate-600">{b.detail}</td>
                  </tr>))}</tbody>
              </table>
              {!!p.shared_terms?.length && <div className="text-[11px] text-slate-500">Wspólne słowa: {p.shared_terms.join(', ')}</div>}
              {!!p.differences?.length && <div className="text-[11px] text-amber-800">Różnice: {p.differences.join('; ')}</div>}
              <ItemDecision a={a} it={it} allowExclude />
            </CardContent>
          </Card>)
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ features */

function FeaturesTab({ a }: { a: A }) {
  const [f, setF] = useState<Features>(a.features as Features)
  useEffect(() => setF(a.features as Features), [a.features])
  const { toast } = useToast()
  const m = useApiMutation<Features, A>({
    fn: async (body) => unwrap(await api.PUT('/api/analyses/{analysis_id}/features', { params: { path: { analysis_id: a.id } }, body })),
    invalidate: [['analysis', a.id]],
    onSuccess: () => toast({ kind: 'success', title: 'Cechy zapisane – analiza przeliczona' }),
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się', description: String(e) }),
  })
  const qs = ((a.params as P).questions ?? []) as string[]
  return (
    <Card>
      <CardHeader title="Cechy inwestycji" description="Zmiana cech przelicza sąsiadów, zakresy, ocenę i flagi. Zmiana trafia do historii."
        actions={<Button loading={m.isPending} onClick={() => m.mutate(f)}>Zapisz i przelicz</Button>} />
      <CardContent className="space-y-3">
        {qs.length > 0 && <ul className="list-disc rounded bg-amber-50 p-2 pl-6 text-xs text-amber-900">{qs.map((q, i) => <li key={i}>{q}</li>)}</ul>}
        <FeaturesForm value={f} onChange={setF} />
        {a.input_text && <details className="text-xs"><summary className="cursor-pointer text-slate-600">Opis źródłowy</summary><p className="mt-1 whitespace-pre-line text-slate-700">{a.input_text}</p></details>}
      </CardContent>
    </Card>
  )
}
