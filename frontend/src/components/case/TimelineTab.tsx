import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceArea, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { Link } from '@tanstack/react-router'
import { useTimeline } from '@/api/cases'
import type { Schemas } from '@/api/client'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { Card, CardContent, CardHeader, Empty, QueryState } from '@/components/ui'
import { fmtDate, fmtPln } from '@/lib/utils'

type Item = Schemas['TimelineItem']
type Kind = Item['kind'] | 'new_end'
type Pt = Item & { x: number; y: number; k: Kind; row: string }

const COLOR: Record<string, string> = { budget: '#64748b', estimate: '#6d28d9', published: '#1d4f91', offers: '#0284c7', contract: '#0f766e', planned_end: '#64748b',
  actual_end: '#dc2626', change: '#ea580c', new_end: '#ea580c', paid: '#059669', cancelled: '#be123c', event: '#a21caf', notice: '#1d4f91', other: '#64748b' }
const KIND: Record<string, string> = { budget: 'Budżet', estimate: 'Szacunek', published: 'Ogłoszenie o zamówieniu', offers: 'Oferty', contract: 'Podpisanie umowy',
  planned_end: 'Termin planowany', actual_end: 'Faktyczne wykonanie', change: 'Zmiana umowy', new_end: 'Nowy termin po zmianie', paid: 'Wypłata',
  cancelled: 'Unieważnienie', event: 'Zdarzenie ryzyka', notice: 'Inne ogłoszenie', other: 'Inne' }
const PROCEDURE_KINDS = new Set(['budget', 'estimate', 'published', 'offers', 'cancelled', 'notice'])
const LOT_KINDS = new Set(['contract', 'planned_end', 'actual_end', 'change', 'new_end'])
const MONTHS = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
const DAY = 86400e3
const ts = (d?: string | null) => (d ? new Date(d).getTime() : NaN)

/** Evenly spaced month ticks (1/2/3/6/12-month step) so labels never pile up on data dates. */
function monthTicks(min: number, max: number): number[] {
  const a = new Date(min), b = new Date(max)
  const span = (b.getFullYear() - a.getFullYear()) * 12 + b.getMonth() - a.getMonth() + 1
  const step = [1, 2, 3, 6, 12].find((s) => span / s <= 8) ?? 24
  const t = new Date(a.getFullYear(), Math.ceil(a.getMonth() / step) * step, 1)
  const out: number[] = []
  while (t.getTime() <= max) { if (t.getTime() >= min) out.push(t.getTime()); t.setMonth(t.getMonth() + step) }
  return out
}
const tickLabel = (v: number) => { const d = new Date(v); return `${MONTHS[d.getMonth()]} ${d.getFullYear()}` }

/** Marker shape per kind; also used in the legend. */
function Marker({ k, cx, cy, size = 6 }: { k: Kind; cx: number; cy: number; size?: number }) {
  const c = COLOR[k] ?? COLOR.other
  const r = size
  switch (k) {
    case 'planned_end': return <circle cx={cx} cy={cy} r={r} fill="white" stroke={c} strokeWidth={2.5} />
    case 'change': return <polygon points={`${cx},${cy - r - 1} ${cx + r + 1},${cy} ${cx},${cy + r + 1} ${cx - r - 1},${cy}`} fill={c} stroke="white" strokeWidth={1} />
    case 'new_end': return <rect x={cx - 1.5} y={cy - r - 4} width={3} height={2 * r + 8} fill={c} />
    case 'event': return <polygon points={`${cx},${cy - r - 1} ${cx + r + 1},${cy + r} ${cx - r - 1},${cy + r}`} fill={c} stroke="white" strokeWidth={1} />
    case 'contract': return <rect x={cx - r} y={cy - r} width={2 * r} height={2 * r} fill={c} stroke="white" strokeWidth={1} />
    default: return <circle cx={cx} cy={cy} r={r} fill={c} stroke="white" strokeWidth={1} />
  }
}

export function TimelineTab({ projectId }: { projectId: string }) {
  const q = useTimeline(projectId)
  return <QueryState q={q}>{(t) => (t.items.length ? <TimelineBody t={t} /> : <Empty>Brak danych o przebiegu tej inwestycji w BZP.</Empty>)}</QueryState>
}

function TimelineBody({ t }: { t: Schemas['TimelineOut'] }) {
  const pva = t.planned_vs_actual as Record<string, unknown> & { evidence?: Record<string, string> }
  const lots = [...new Set(t.items.filter((i) => LOT_KINDS.has(i.kind)).map((i) => i.part_no ?? 1))].sort((a, b) => a - b)
  if (!lots.length) lots.push(1)
  const multi = lots.length > 1
  const lotRow = (n: number) => (multi ? `Umowa – część ${n}` : 'Umowa')
  const hasEvents = t.items.some((i) => i.kind === 'event' && i.date)
  const hasPaid = t.items.some((i) => i.kind === 'paid' && i.date)
  const rows = ['Postępowanie', ...lots.map(lotRow), ...(hasEvents ? ['Zdarzenia ryzyka'] : []), ...(hasPaid ? ['Płatności'] : [])]
  const yOf = (row: string) => rows.length - rows.indexOf(row) // first row on top
  const rowOf = (i: Item) => (PROCEDURE_KINDS.has(i.kind) ? 'Postępowanie' : LOT_KINDS.has(i.kind) ? lotRow(i.part_no ?? 1)
    : i.kind === 'event' ? 'Zdarzenia ryzyka' : 'Płatności')

  const raw: Omit<Pt, 'y'>[] = []
  for (const i of t.items) {
    if (i.date) raw.push({ ...i, x: ts(i.date), k: i.kind, row: rowOf(i) })
    if (i.kind === 'change' && i.new_end && i.new_end !== i.date) raw.push({ ...i, date: i.new_end, x: ts(i.new_end), k: 'new_end', row: rowOf(i), label: `Nowy termin po zmianie: ${fmtDate(i.new_end)}` })
  }
  // spread markers that fall on the same row and (nearly) the same day so none hides another
  const groups = new Map<string, number>()
  const pts: Pt[] = raw.map((p) => {
    const key = `${p.row}|${Math.round(p.x / (10 * DAY))}`
    const n = groups.get(key) ?? 0
    groups.set(key, n + 1)
    return { ...p, y: yOf(p.row) + (n === 0 ? 0 : (n % 2 ? 1 : -1) * Math.ceil(n / 2) * 0.17) }
  })
  const xs = pts.map((p) => p.x)
  const pad = Math.max(20 * DAY, (Math.max(...xs) - Math.min(...xs)) * 0.03)
  const domain: [number, number] = [Math.min(...xs) - pad, Math.max(...xs) + pad]

  const bands = lots.flatMap((n) => {
    const of = (k: string) => t.items.find((i) => i.kind === k && (i.part_no ?? 1) === n)
    const sign = of('contract'), plan = of('planned_end'), act = of('actual_end')
    const y = yOf(lotRow(n))
    const out: { x1: number; x2: number; y: number; fill: string; op: number }[] = []
    if (sign?.date && plan?.date) out.push({ x1: ts(sign.date), x2: ts(plan.date), y, fill: '#94a3b8', op: 0.35 })
    if (plan?.date && act?.date && ts(act.date) > ts(plan.date)) out.push({ x1: ts(plan.date), x2: ts(act.date), y, fill: '#dc2626', op: 0.3 })
    return out
  })
  const late = bands.some((b) => b.fill === '#dc2626')
  const shownKinds = [...new Set(pts.map((p) => p.k))]
  const legendOrder: Kind[] = ['published', 'notice', 'estimate', 'budget', 'offers', 'cancelled', 'contract', 'planned_end', 'change', 'new_end', 'actual_end', 'event', 'paid']

  // money: sum over lots so a two-lot project is not shown with lot 1 only
  const money: { name: string; value: number; kind: string }[] = []
  const sum = (kind: string, name: string) => {
    const xsv = t.items.filter((x) => x.kind === kind && x.value).map((x) => x.value as number)
    if (xsv.length) money.push({ name: xsv.length > 1 ? `${name} (${xsv.length} części)` : name, value: xsv.reduce((a, b) => a + b, 0), kind })
  }
  sum('budget', 'Budżet projektu'); sum('estimate', 'Szacunek (netto)'); sum('offers', 'Najniższa oferta'); sum('contract', 'Umowa'); sum('paid', 'Wypłacono')
  const contract = t.items.find((i) => i.kind === 'contract' && (i.part_no ?? 1) === ((pva.part_no as number) ?? 1)) ?? t.items.find((i) => i.kind === 'contract')
  const planned = t.items.find((i) => i.kind === 'planned_end')
  const actual = t.items.find((i) => i.kind === 'actual_end')
  const changes = t.items.filter((i) => i.kind === 'change')
  const lotNote = multi && pva.part_no ? ` (część ${pva.part_no})` : ''

  return (
    <div className="flex flex-col gap-4">
      {multi && <p className="text-sm text-slate-600">Ta inwestycja ma {lots.length} umowy (części zamówienia). Kafelki poniżej dotyczą największej z nich{lotNote}; wykres pokazuje każdą część osobno.</p>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Fact label={`Termin planowany${lotNote}`} value={fmtDate(pva.planned_end as string)} ev={pva.evidence?.planned_end ? [pva.evidence.planned_end] : planned?.evidence_ids} calc />
        <Fact label="Termin po zmianach" value={fmtDate((pva.amended_end as string) ?? null)} ev={changes.at(-1)?.evidence_ids} />
        <Fact label={`Wykonanie${lotNote}`} value={fmtDate(pva.actual_end as string)} ev={actual?.evidence_ids} />
        <Fact label="Opóźnienie" value={pva.delay_days != null ? `${pva.delay_days} dni${pva.delay_vs_amended_days ? ` (${pva.delay_vs_amended_days} po aneksie)` : ''}` : '—'}
          ev={pva.evidence?.delay_days ? [pva.evidence.delay_days] : []} calc warn={Number(pva.delay_days) > 0} />
        <Fact label={`Wartość umowy${lotNote}`} value={fmtPln(pva.value as number)} ev={contract?.evidence_ids} />
        <Fact label={`Wypłacono${lotNote}`} value={fmtPln(pva.paid as number)} ev={t.items.find((i) => i.kind === 'paid')?.evidence_ids} />
        <Fact label="Wypłata / wartość" value={pva.paid_ratio != null ? String(pva.paid_ratio).replace('.', ',') : '—'} ev={pva.evidence?.paid_ratio ? [pva.evidence.paid_ratio] : []} calc
          warn={Number(pva.paid_ratio) > 1.05} />
        <Fact label="Oferta / szacunek" value={pva.evidence?.offer_vs_estimate ? 'netto i brutto, nie porównujemy' : '—'} ev={pva.evidence?.offer_vs_estimate ? [pva.evidence.offer_vs_estimate] : []} calc />
      </div>

      <Card>
        <CardHeader title="Przebieg: plan a rzeczywistość"
          description={`Każdy wiersz to etap inwestycji${multi ? ', a każda część zamówienia ma własny wiersz umowy' : ''}. Szary pas: okres od podpisania umowy do planowanego terminu.${late ? ' Czerwony pas: wykonanie po planowanym terminie.' : ''} Najedź na znacznik, żeby zobaczyć szczegóły.`}
          actions={<BlockLabel label="dane_zrodlowe" />} />
        <CardContent>
          <div style={{ height: 70 + rows.length * 52 }} role="img" aria-label={`Oś czasu projektu: ${rows.join(', ')}`}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 12, right: 28, bottom: 6, left: 8 }}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="2 4" horizontal={false} />
                <XAxis type="number" dataKey="x" domain={domain} scale="time" ticks={monthTicks(domain[0], domain[1])} tickFormatter={tickLabel}
                  fontSize={11} tickMargin={6} interval={0} allowDataOverflow />
                <YAxis type="number" dataKey="y" domain={[0.4, rows.length + 0.6]} ticks={rows.map((_, i) => i + 1)} interval={0}
                  tickFormatter={(v) => rows[rows.length - v] ?? ''} width={multi ? 130 : 100} fontSize={11} />
                <ZAxis range={[90, 90]} />
                {rows.map((r) => <ReferenceArea key={r} y1={yOf(r) - 0.5} y2={yOf(r) + 0.5} fill={yOf(r) % 2 ? '#f8fafc' : '#ffffff'} fillOpacity={0.6} ifOverflow="hidden" />)}
                {bands.map((b, i) => <ReferenceArea key={i} x1={b.x1} x2={b.x2} y1={b.y - 0.22} y2={b.y + 0.22} fill={b.fill} fillOpacity={b.op} ifOverflow="hidden" />)}
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ payload }) => {
                  const p = payload?.[0]?.payload as Pt | undefined
                  if (!p) return null
                  return <div className="rounded border border-slate-200 bg-white p-2 text-xs shadow"><div className="font-semibold">{KIND[p.k]} · {fmtDate(p.date)}</div>
                    <div className="text-slate-500">{p.row}</div><div>{p.label}</div>{p.value != null && p.value !== 0 && <div>{fmtPln(p.value)}</div>}</div>
                }} />
                <Scatter data={pts} isAnimationActive={false} shape={(props: { cx?: number; cy?: number; payload?: Pt }) =>
                  <Marker k={props.payload?.k ?? 'other'} cx={props.cx ?? 0} cy={props.cy ?? 0} />} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-slate-600" aria-label="Legenda">
            {legendOrder.filter((k) => shownKinds.includes(k)).map((k) => (
              <li key={k} className="flex items-center gap-1.5"><svg width="16" height="18" aria-hidden><Marker k={k} cx={8} cy={9} size={5} /></svg>{KIND[k]}</li>))}
            {bands.length > 0 && <li className="flex items-center gap-1.5"><span className="h-2.5 w-5 rounded-sm bg-slate-400/40" />okres planowany</li>}
            {late && <li className="flex items-center gap-1.5"><span className="h-2.5 w-5 rounded-sm bg-red-600/30" />po terminie</li>}
          </ul>
        </CardContent>
      </Card>

      {money.length > 0 && (
        <Card>
          <CardHeader title="Budżet → oferty → umowa → wypłata" description="Kwoty z ogłoszeń; podstawa VAT podana przy wartości (szacunek jest netto)." actions={<BlockLabel label="dane_zrodlowe" />} />
          <CardContent>
            <div className="h-56" role="img" aria-label="Porównanie kwot">
              <ResponsiveContainer>
                <BarChart data={money} layout="vertical" margin={{ left: 8, right: 110 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={170} fontSize={11} />
                  <Tooltip formatter={(v) => fmtPln(Number(v))} />
                  <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                    {money.map((m) => <Cell key={m.name} fill={COLOR[m.kind]} />)}
                    <LabelList dataKey="value" position="right" formatter={(v: unknown) => fmtPln(Number(v))} fontSize={11} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader title="Kroki przebiegu" />
        <ol className="divide-y divide-slate-100">
          {t.items.map((i, k) => (
            <li key={k} className="flex flex-wrap items-center gap-3 px-4 py-2 text-sm">
              <span className="w-24 shrink-0 font-mono text-xs text-slate-500">{fmtDate(i.date)}</span>
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: COLOR[i.kind] }} aria-hidden />
              <span className="w-32 shrink-0 text-xs text-slate-500">{KIND[i.kind]}{i.planned ? ' (plan)' : ''}</span>
              <span className="min-w-0 flex-1">{i.label}</span>
              {i.value != null && i.value !== 0 && <span className="tabular-nums">{fmtPln(i.value)}</span>}
              {i.evidence_ids?.length ? <EvidenceChip ids={i.evidence_ids} />
                : i.notice_id ? <Link to="/ogloszenia/$noticeId" params={{ noticeId: i.notice_id }} search={{}} className="text-xs text-brand hover:underline">Zobacz ogłoszenie</Link> : null}
            </li>
          ))}
        </ol>
      </Card>
    </div>
  )
}

function Fact({ label, value, ev, calc, warn }: { label: string; value: string; ev?: string[] | null; calc?: boolean; warn?: boolean }) {
  return (
    <div className={`rounded-lg border bg-white p-3 ${calc ? 'border-l-calc' : 'border-l-src'} ${warn ? 'border-rose-200' : 'border-slate-200'}`}>
      <div className="flex items-center justify-between gap-2 text-xs text-slate-500">{label}<EvidenceChip ids={ev ?? []} /></div>
      <div className={`mt-1 text-base font-semibold ${warn ? 'text-rose-700' : ''}`}>{value}</div>
    </div>
  )
}
