import { Link, useNavigate } from '@tanstack/react-router'
import { Check, Download, EyeOff, RefreshCw, RotateCcw, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, rawFetch, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { FeaturesForm, type Features } from '@/components/analysis/FeaturesForm'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { HowCalculated, Intro, Term } from '@/components/Explain'
import { RiskCodes } from '@/components/LinkStatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { Fact, Proportion, ScoreBar, Spread } from '@/components/Visual'
import { Badge, Button, Card, CardContent, CardHeader, QueryState, Tabs, useToast } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { RISK_NAMES } from '@/lib/labels'
import { cn, fmtNum, fmtPln } from '@/lib/utils'
import { analysisRoute } from '@/router'

type A = Schemas['AnalysisOut']
type Item = Schemas['AnalysisItemOut']
type P = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

const SEV: Record<string, { v: 'danger' | 'warning' | 'default'; t: string }> = { wysoka: { v: 'danger', t: 'ważne' }, 'średnia': { v: 'warning', t: 'do sprawdzenia' }, niska: { v: 'default', t: 'informacyjne' } }
const LEVEL_PL: Record<string, string> = { neighbours: 'najbardziej podobnych inwestycjach', subsector: 'wszystkich inwestycjach z tego podsektora', wodkan: 'wszystkich inwestycjach wod-kan', works: 'wszystkich robotach w bazie' }
const AXIS_PL: Record<string, string> = { realizacja: 'ryzyko w trakcie realizacji', 'postępowanie': 'ryzyko w przetargu', przygotowanie: 'stan przygotowania', dane: 'brakujące informacje' }
const pct = (x?: number | null) => (x == null ? '—' : `${Math.round(x * 100)}%`)

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
      const sm = a.summary as P
      return (
        <div>
          <PageHeader back title={a.title}
            description={<>Porównanie z {Number(sm.n_cases ?? 0).toLocaleString('pl-PL')} zakończonymi inwestycjami z bazy · wersja analizy {a.version}</>}
            actions={<>
              <Button variant="outline" loading={recompute.isPending} onClick={() => recompute.mutate()} title="Liczy analizę od nowa na aktualnej bazie i wiedzy eksperckiej"><RefreshCw size={14} />Przelicz</Button>
              <ExportButton id={a.id} format="docx" title={a.title} label="Pobierz kartę (Word)" />
              <ExportButton id={a.id} format="json" title={a.title} label="Dane (JSON)" />
              <ExportButton id={a.id} format="csv" title={a.title} label="Dane (CSV)" />
            </>} />
          <Summary a={a} />
          <Tabs value={tab} onChange={(t) => navigate({ search: { tab: t }, replace: true })} className="mt-4" tabs={[
            { value: 'flagi', label: 'Na co uważać', count: by('flag').length },
            { value: 'dzialania', label: 'Zalecane działania i zapisy', count: by('action').length },
            { value: 'ocena', label: 'Budżet i harmonogram' },
            { value: 'zakresy', label: 'Co działo się w podobnych' },
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

function ExportButton({ id, format, title, label }: { id: string; format: 'docx' | 'json' | 'csv'; title: string; label: string }) {
  const [busy, setBusy] = useState(false)
  return (
    <Button variant={format === 'docx' ? 'default' : 'outline'} size="sm" loading={busy} onClick={async () => {
      setBusy(true)
      try {
        const r = await rawFetch(`/api/analyses/${id}/export?format=${format}`)
        const url = URL.createObjectURL(await r.blob())
        const el = document.createElement('a')
        el.href = url; el.download = `${title.replace(/[^\p{L}\d]+/gu, '_').slice(0, 40)}.${format}`; el.click()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      } finally { setBusy(false) }
    }}><Download size={12} />{label}</Button>
  )
}

/* ------------------------------------------------------------------ summary */

function Summary({ a }: { a: A }) {
  const s = a.summary as P
  const pl = s.p_late ?? {}, dd = s.delay_days ?? {}, pr = s.paid_ratio ?? {}, b = s.budget ?? {}
  return (
    <Card>
      <CardHeader title="W skrócie" actions={<BlockLabel label="obliczenia" />}
        description={`Na podstawie ${s.n_neighbours ?? 0} najbardziej podobnych zakończonych inwestycji (zakładka „Podobne inwestycje”).`} />
      <CardContent className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <div className="space-y-1">
          <div className="text-xs font-semibold text-slate-600">Czy zdąży na czas?</div>
          <Proportion k={pl.k} n={pl.n} estimate={pl.estimate} low={pl.ci_low} high={pl.ci_high}
            what="podobnych umów wykonano po terminie" />
        </div>
        <div className="space-y-1">
          <div className="text-xs font-semibold text-slate-600">O ile dni bywały opóźnione?</div>
          <Spread p50={dd.p50} p80={dd.p80} p95={dd.p95} unit=" dni" />
          <div className="text-[11px] text-slate-500"><Term t="P50">typowo</Term> / <Term t="P80">z zapasem</Term>, n = {dd.n ?? '—'}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs font-semibold text-slate-600">Czy wypłata przekracza umowę?</div>
          <p className="text-sm">Typowo wypłacono <b>{pr.p50 != null ? `${Math.round(pr.p50 * 100)}%` : '—'}</b> wartości umowy; w 2 na 10 przypadków ponad <b>{pr.p80 != null ? `${Math.round(pr.p80 * 100)}%` : '—'}</b>.</p>
        </div>
        <div className="space-y-1">
          <div className="text-xs font-semibold text-slate-600">Czy budżet jest realny?</div>
          {b.percentile != null
            ? <p className="text-sm">Budżet jest wyższy niż w <b>{Math.round(b.percentile * 100)}</b> na 100 podobnych umów{b.reserve_p80 ? <>; z zapasem warto zarezerwować <b>{fmtPln(b.reserve_p80.amount)}</b> <Term t="rezerwa P80" /></> : null}.</p>
            : <p className="text-sm text-amber-800">{b.message ?? 'Nie porównano – uzupełnij wartość i informację netto/brutto w zakładce „Cechy inwestycji”.'}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ item decision */

function ItemDecision({ a, it, allowExclude }: { a: A; it: Item; allowExclude?: boolean }) {
  const { isExpert } = useAuth()
  const { toast } = useToast()
  const m = useApiMutation<Schemas['AnalysisItemPatch'], Item>({
    fn: async (body) => unwrap(await api.PATCH('/api/analyses/{analysis_id}/items/{item_id}', { params: { path: { analysis_id: a.id, item_id: it.id } }, body })),
    invalidate: [['analysis', a.id]],
    onSuccess: (_r, v) => v.excluded != null && toast({ kind: 'success', title: v.excluded ? 'Wykluczono – analiza przeliczona bez tej inwestycji' : 'Przywrócono – analiza przeliczona' }),
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się', description: String(e) }),
  })
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {isExpert && <>
        <StatusBadge status={it.status} />
        {it.status !== 'approved' && <Button size="sm" variant="success" loading={m.isPending} onClick={() => m.mutate({ status: 'approved' })}><Check size={12} />Zatwierdź</Button>}
        {it.status !== 'rejected' && <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate({ status: 'rejected' })}><X size={12} />Odrzuć</Button>}
        {it.status !== 'proposed' && <Button size="sm" variant="ghost" onClick={() => m.mutate({ status: 'proposed' })}><RotateCcw size={12} />Cofnij decyzję</Button>}
      </>}
      {allowExclude && <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate({ excluded: !it.excluded })}
        title={it.excluded ? 'Uwzględnij tę inwestycję w porównaniu' : 'Pomiń tę inwestycję (np. niepodobna) – wyniki zostaną przeliczone'}>
        <EyeOff size={12} />{it.excluded ? 'Uwzględnij ponownie' : 'Pomiń w porównaniu'}</Button>}
    </div>
  )
}

/* ------------------------------------------------------------------ flags */

function Flags({ items, a }: { items: Item[]; a: A }) {
  return (
    <div>
      <Intro can={['przeczytać, dlaczego flaga się pojawiła (każda ma uzasadnienie, a zdania z Twojego opisu są przytoczone)', 'zobaczyć przykłady z podobnych inwestycji – kliknij, by otworzyć ich kartę']}>
        Sprawy, które w podobnych inwestycjach prowadziły do opóźnień, zmian umów lub wzrostu kosztów – albo które wynikają z Twojego opisu (np. brak zgód właścicieli, brak decyzji). Kolejność: najpierw <b>ważne</b>, potem <b>do sprawdzenia</b> i <b>informacyjne</b>. Kod w fioletowej etykiecie to <Term t="kategoria ryzyka" /> z katalogu ekspertów.
      </Intro>
      {!items.length && <p className="text-sm text-slate-500">Brak flag.</p>}
      <div className="space-y-3">{items.map((it) => {
        const p = it.payload as P
        const sev = SEV[p.severity] ?? SEV.niska
        return (
          <Card key={it.id} className={cn(it.status === 'rejected' && 'opacity-60')}>
            <CardHeader title={<span className="flex flex-wrap items-center gap-2"><Badge variant={sev.v}>{sev.t}</Badge>{it.title}</span>}
              description={AXIS_PL[p.axis] ?? p.axis} actions={<><RiskCodes codes={it.risk_codes} /><BlockLabel label={it.label} /></>} />
            <CardContent className="space-y-2 text-sm">
              <p>{p.why}</p>
              {(it.risk_codes ?? []).map((c) => RISK_NAMES[c] ? <p key={c} className="text-xs text-slate-500">{c}: {RISK_NAMES[c]}</p> : null)}
              {p.quote && <blockquote className="border-l-2 border-teal-400 bg-teal-50/40 py-1 pl-2 text-sm">„{p.quote}” <span className="text-xs text-slate-500">– z Twojego opisu</span></blockquote>}
              {!!p.examples?.length && (
                <details className="text-sm"><summary className="cursor-pointer text-slate-600">Jak to wyglądało w podobnych inwestycjach ({p.examples.length})</summary>
                  <ul className="mt-2 space-y-1.5">{p.examples.map((e: P) => (
                    <li key={e.event_id} className="rounded bg-slate-50 p-2 text-xs">
                      <Link to="/projekty/$projectId" params={{ projectId: e.project_id }} search={{ tab: 'zdarzenia' }} className="font-medium text-brand hover:underline">{e.title}</Link>
                      {e.quote && <div className="mt-0.5 text-slate-600">„{e.quote}”</div>}
                      {!!e.evidence_ids?.length && <EvidenceChip ids={e.evidence_ids} label="Pokaż w źródle" className="mt-1" />}
                    </li>))}</ul></details>)}
              {!!p.items?.length && (
                <ul className="list-disc pl-5 text-sm">{p.items.map((x: P) => <li key={x.no}>{x.item} <span className="text-xs text-slate-500">(poradnik, rozdz. {x.guide_sections})</span></li>)}</ul>)}
              {p.formula && <HowCalculated>{p.formula}</HowCalculated>}
              <ItemDecision a={a} it={it} />
            </CardContent>
          </Card>)
      })}</div>
    </div>
  )
}

/* ------------------------------------------------------------------ actions */

function Actions({ items, a }: { items: Item[]; a: A }) {
  const llm = items.find((i) => i.label === 'wniosek_modelu')
  const rest = items.filter((i) => i !== llm)
  return (
    <div className="space-y-3">
      <Intro can={['skopiować proponowany zapis do projektu umowy lub SWZ (po weryfikacji prawnej)', 'przeczytać lekcje z kontroli i wzorcowe przypadki zatwierdzone przez eksperta']}>
        Dla każdej kategorii ryzyka wskazanej we flagach: zapis umowny lub działanie zapobiegawcze z podstawą prawną (katalog prowadzi ekspert), wnioski z kontroli NIK i wzorcowe przypadki z bazy. Na górze – krótkie podsumowanie przygotowane przez model językowy na podstawie wyliczonych liczb.
      </Intro>
      {llm && (() => {
        const p = llm.payload as P
        return (
          <Card className="border-amber-200">
            <CardHeader title="Podsumowanie" actions={<BlockLabel label="wniosek_modelu" />} description={`Przygotował: ${p.model_label ?? 'model językowy'} – na podstawie liczb z tej analizy; wymaga oceny eksperta.`} />
            <CardContent className="space-y-2 text-sm"><p>{p.summary}</p>
              <ol className="list-decimal space-y-0.5 pl-5">{(p.top_actions ?? []).map((x: string, i: number) => <li key={i}>{x}</li>)}</ol>
              <ItemDecision a={a} it={llm} /></CardContent>
          </Card>)
      })()}
      {rest.map((it) => {
        const p = it.payload as P
        return (
          <Card key={it.id}>
            <CardHeader title={`${p.risk_code}: ${p.risk_name ?? ''}`} actions={<BlockLabel label={it.label} />} />
            <CardContent className="space-y-2 text-sm">
              {(p.clauses ?? []).map((c: P) => (
                <div key={c.id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex flex-wrap items-center gap-2 font-medium">{c.title}
                    {c.status !== 'approved' && <Badge variant="warning" title="Zapis z katalogu zespołu – czeka na zatwierdzenie eksperta w „Wiedzy eksperckiej”">projekt zapisu</Badge>}</div>
                  <p className="mt-1">{c.text}</p>
                  <p className="mt-1 text-xs text-slate-500">Podstawa: {c.legal_basis}{c.trigger ? ` · kiedy stosować: ${c.trigger}` : ''}</p>
                </div>))}
              {(p.lessons ?? []).map((l: P) => (
                <div key={l.id} className="rounded-md bg-slate-50 p-2 text-xs"><b>Wniosek z kontroli:</b> {l.title} – {l.recommendation} <EvidenceChip ids={l.evidence_ids} /></div>))}
              {(p.examples ?? []).map((e: P) => (
                <div key={e.id} className="rounded-md bg-emerald-50 p-2 text-xs"><b>Wzorcowy przypadek:</b> {e.title} – {e.mitigation} {e.mitigation_effect && `(${e.mitigation_effect})`}</div>))}
              <ItemDecision a={a} it={it} />
            </CardContent>
          </Card>)
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ assessment */

function Assessment({ items }: { items: Item[]; a: A }) {
  return (
    <div>
      <Intro can={['sprawdzić, czy budżet i czas realizacji nie są zbyt optymistyczne', 'zobaczyć koszt na kilometr sieci lub na mieszkańca w porównaniu z podobnymi']}>
        Porównujemy budżet, harmonogram i koszt jednostkowy tej inwestycji z faktycznymi umowami podobnych inwestycji. Kwoty porównujemy tylko tego samego rodzaju (netto z netto, brutto z brutto). <Term t="percentyl">Percentyl</Term> P20 oznacza, że wartość jest niższa niż w 8 na 10 podobnych przypadków.
      </Intro>
      <div className="grid gap-3 md:grid-cols-2">{items.map((it) => {
        const p = it.payload as P
        return (
          <Card key={it.id}>
            <CardHeader title={it.title} actions={<BlockLabel label={it.label} />} />
            <CardContent className="space-y-2 text-sm">
              {p.percentile != null && <ScoreBar value={p.percentile} label={<>Pozycja na tle podobnych: P{Math.round(p.percentile * 100)}</>} detail={p.position} />}
              {p.value != null && <Fact label="Wartość tej inwestycji" value={fmtNum(p.value)} hint={p.basis} />}
              {p.quantiles && <><div className="text-xs text-slate-500">Podobne umowy:</div><Spread p50={p.quantiles.p50} p80={p.quantiles.p80} p95={p.quantiles.p90} third="9 na 10 nie więcej" /></>}
              {p.reserve_p80 && <p>Z zapasem (jak w 8 na 10 podobnych) warto przewidzieć <b>{fmtPln(p.reserve_p80.amount)}</b>.</p>}
              {p.estimate != null && <Proportion k={p.k} n={p.n} estimate={p.estimate} low={p.ci_low} high={p.ci_high} what="podobnych postępowań" tone="amber" />}
              {(p.p50 != null && p.estimate == null) && <Spread p50={p.p50} p80={p.p80} p95={p.p95} digits={2} />}
              {p.message && <p className="rounded bg-amber-50 p-2 text-xs text-amber-900">{p.message}</p>}
              <p className="text-xs text-slate-500">Na podstawie <Term t="n">{p.n ?? 0} przypadków</Term>{p.fallback_level ? ` (${LEVEL_PL[p.fallback_level] ?? p.fallback_level})` : ''}.</p>
              {p.formula && <HowCalculated>{p.formula}</HowCalculated>}
            </CardContent>
          </Card>)
      })}</div>
    </div>
  )
}

const RANGE_Q: Record<string, { q: string; what: string; tone?: 'rose' | 'amber' | 'brand'; unit?: string; digits?: number }> = {
  p_late: { q: 'Jak często podobne umowy kończyły się po terminie?', what: 'podobnych umów wykonano po terminie' },
  delay_days: { q: 'Ile dni opóźnienia (wszystkie umowy, w terminie = 0)?', what: '', unit: ' dni' },
  delay_days_if_late: { q: 'Jak duże było opóźnienie, gdy już wystąpiło?', what: '', unit: ' dni' },
  paid_ratio: { q: 'Ile wypłacono w stosunku do wartości umowy?', what: '', digits: 2 },
  p_change: { q: 'Jak często zmieniano umowę?', what: 'podobnych umów zmieniono', tone: 'amber' },
  share_cancelled: { q: 'Jak często unieważniano postępowanie?', what: 'podobnych postępowań unieważniono', tone: 'amber' },
  share_cancelled_255_3: { q: 'Jak często unieważniano, bo oferty przekraczały budżet?', what: 'podobnych postępowań unieważniono z powodu ceny', tone: 'amber' },
  offer_vs_budget: { q: 'Cena wybranej oferty a budżet zamawiającego', what: '', digits: 2 },
  offer_vs_estimate: { q: 'Cena wybranej oferty a wartość szacunkowa', what: '', digits: 2 },
}

function Ranges({ items, a }: { items: Item[]; a: A }) {
  return (
    <div>
      <Intro can={['rozwinąć „Jak to policzono?” przy każdej liczbie', 'sprawdzić, na ilu przypadkach policzono wynik']}>
        Co działo się w podobnych, zakończonych inwestycjach: jak często i o ile się opóźniały, czy wypłata przekraczała wartość umowy, jak często zmieniano umowy i unieważniano przetargi. Gdy podobnych inwestycji z danymi jest mało, liczymy na szerszej grupie (cały podsektor albo wszystkie inwestycje wod-kan) i stosujemy <Term t="wygładzenie" />. Przy odsetkach podajemy <Term t="przedział 95%">przedział</Term>, w którym prawdopodobnie leży prawdziwa wartość.
      </Intro>
      <div className="grid gap-3 md:grid-cols-2">{items.map((it) => {
        const p = it.payload as P
        const m = RANGE_Q[p.metric] ?? { q: it.title ?? p.metric, what: '' }
        const isProp = p.estimate !== undefined && p.p50 === undefined
        return (
          <Card key={it.id} className={cn(it.status === 'rejected' && 'opacity-60')}>
            <CardHeader title={m.q} actions={<BlockLabel label={it.label} />} />
            <CardContent className="space-y-2">
              {isProp ? <Proportion k={p.k} n={p.n} estimate={p.estimate} low={p.ci_low} high={p.ci_high} what={m.what} tone={m.tone} />
                : <Spread p50={p.p50} p80={p.p80} p95={p.p95} unit={m.unit} digits={m.digits ?? 0} />}
              <p className="text-xs text-slate-500">Policzono na <Term t="n">{p.n} przypadkach</Term> – {LEVEL_PL[p.fallback_level] ?? p.fallback_level}{p.period ? `, lata ${p.period}` : ''}.</p>
              {p.formula && <HowCalculated>{p.formula}</HowCalculated>}
              <ItemDecision a={a} it={it} />
            </CardContent>
          </Card>)
      })}</div>
    </div>
  )
}

/* ------------------------------------------------------------------ neighbours */

function Neighbours({ items, a }: { items: Item[]; a: A }) {
  const sorted = [...items].sort((x, y) => Number(x.excluded) - Number(y.excluded) || (y.payload as P).score - (x.payload as P).score)
  return (
    <div className="space-y-3">
      <Intro can={['zobaczyć, w czym każda inwestycja jest podobna, a w czym różna', 'pominąć inwestycję, która Twoim zdaniem nie pasuje – wszystkie wyniki zostaną przeliczone bez niej', 'otworzyć kartę inwestycji i sprawdzić, co się w niej wydarzyło']}>
        Zakończone inwestycje najbardziej zbliżone do opisanej. <Term t="podobieństwo">Podobieństwo</Term> składa się z kilku cech – pasek pokazuje, na ile dana cecha się zgadza, a <Term t="waga">waga</Term> – jak bardzo się liczy. Na tych inwestycjach opierają się zakresy i flagi.
      </Intro>
      {sorted.map((it) => {
        const p = it.payload as P
        const o = p.outcome ?? {}
        return (
          <Card key={it.id} className={cn(it.excluded && 'opacity-50')}>
            <CardHeader title={<Link to="/projekty/$projectId" params={{ projectId: p.project_id }} search={{}} className="hover:underline">{p.title}</Link>}
              description={<>{p.subsector_main ?? 'podsektor nieustalony'} · podobieństwo <b>{pct(p.score)}</b>{it.excluded ? ' · pominięta w porównaniu' : ''}</>}
              actions={<EvidenceChip ids={o.evidence_ids} label="Źródło wyniku" />} />
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                <Fact label="Wartość umowy" value={fmtPln(o.value_gross)} />
                <Fact label="Opóźnienie" value={o.delay_days == null ? '—' : o.delay_days > 0 ? `${o.delay_days} dni` : 'w terminie'} warn={(o.delay_days ?? 0) > 0} />
                <Fact label="Wypłata / umowa" value={o.paid_ratio == null ? '—' : `${Math.round(o.paid_ratio * 100)}%`} warn={(o.paid_ratio ?? 0) > 1.05} />
                <Fact label="Zmiany umowy" value={o.n_changes ?? '—'} />
              </div>
              <div className="grid gap-2 sm:grid-cols-2">{(p.breakdown ?? []).map((b: P) => (
                <ScoreBar key={b.component} value={b.similarity} label={<>{b.label} <span className="font-normal text-slate-400">(waga {Math.round(b.weight * 100)}%)</span></>} detail={b.detail} />))}</div>
              {!!p.shared_terms?.length && <p className="text-xs text-slate-500">Wspólne słowa w opisach: {p.shared_terms.join(', ')}</p>}
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
    <div>
      <Intro can={['poprawić lub uzupełnić cechę – po zapisaniu analiza zostanie przeliczona', 'sprawdzić, z którego zdania opisu odczytano każdą cechę']}>
        Cechy, na podstawie których szukamy podobnych inwestycji i oceniamy budżet. Przy każdej widać, skąd pochodzi: z reguły, z modelu językowego albo od Ciebie.
      </Intro>
      <Card>
        <CardHeader title="Cechy inwestycji" actions={<Button loading={m.isPending} onClick={() => m.mutate(f)}>Zapisz i przelicz</Button>} />
        <CardContent className="space-y-3">
          {qs.length > 0 && <ul className="list-disc rounded bg-amber-50 p-2 pl-6 text-sm text-amber-900">{qs.map((q, i) => <li key={i}>{q}</li>)}</ul>}
          <FeaturesForm value={f} onChange={setF} />
          {a.input_text && <details className="text-sm"><summary className="cursor-pointer text-slate-600">Opis, z którego odczytano cechy</summary><p className="mt-1 whitespace-pre-line text-slate-700">{a.input_text}</p></details>}
        </CardContent>
      </Card>
    </div>
  )
}
