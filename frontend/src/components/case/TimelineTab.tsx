import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceArea, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { useTimeline } from '@/api/cases'
import type { Schemas } from '@/api/client'
import { BlockLabel } from '@/components/BlockLabel'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { Card, CardContent, CardHeader, Empty, QueryState } from '@/components/ui'
import { fmtDate, fmtPln } from '@/lib/utils'

type Item = Schemas['TimelineItem']
const LANE: Record<string, number> = { budget: 4, estimate: 4, published: 4, offers: 4, contract: 3, planned_end: 3, actual_end: 3, change: 2, event: 2, paid: 1, cancelled: 4, notice: 4, other: 1 }
const LANE_NAME: Record<number, string> = { 4: 'Postępowanie', 3: 'Umowa', 2: 'Zmiany', 1: 'Płatności' }
const COLOR: Record<string, string> = { budget: '#64748b', estimate: '#6d28d9', published: '#1d4f91', offers: '#0284c7', contract: '#0f766e', planned_end: '#94a3b8',
  actual_end: '#dc2626', change: '#d97706', paid: '#059669', cancelled: '#be123c', event: '#b45309', notice: '#1d4f91', other: '#64748b' }
const KIND: Record<string, string> = { budget: 'Budżet', estimate: 'Szacunek', published: 'Ogłoszenie', offers: 'Oferty', contract: 'Umowa', planned_end: 'Termin planowany',
  actual_end: 'Wykonanie', change: 'Zmiana', paid: 'Wypłata', cancelled: 'Unieważnienie', event: 'Zdarzenie', notice: 'Ogłoszenie', other: 'Inne' }
const ts = (d?: string | null) => (d ? new Date(d).getTime() : NaN)

export function TimelineTab({ projectId }: { projectId: string }) {
  const q = useTimeline(projectId)
  return <QueryState q={q}>{(t) => (t.items.length ? <TimelineBody t={t} /> : <Empty>Brak danych o przebiegu – uruchom „Wzbogać”.</Empty>)}</QueryState>
}

function TimelineBody({ t }: { t: Schemas['TimelineOut'] }) {
  const pva = t.planned_vs_actual as Record<string, unknown> & { evidence?: Record<string, string> }
  const pts = t.items.filter((i) => i.date).map((i) => ({ ...i, x: ts(i.date), y: LANE[i.kind] ?? 1 }))
  const contract = t.items.find((i) => i.kind === 'contract')
  const planned = t.items.find((i) => i.kind === 'planned_end')
  const actual = t.items.find((i) => i.kind === 'actual_end')
  const changes = t.items.filter((i) => i.kind === 'change')
  const xs = pts.map((p) => p.x)
  const pad = 20 * 86400e3
  const money: { name: string; value: number; kind: string; ev: string[] }[] = []
  const add = (kind: string, name: string) => { const i = t.items.find((x) => x.kind === kind && x.value); if (i?.value) money.push({ name, value: i.value, kind, ev: i.evidence_ids ?? [] }) }
  add('budget', 'Budżet projektu'); add('estimate', 'Szacunek (netto)'); add('offers', 'Najniższa oferta'); add('contract', 'Umowa'); add('paid', 'Wypłacono')

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Fact label="Termin planowany" value={fmtDate(pva.planned_end as string)} ev={pva.evidence?.planned_end ? [pva.evidence.planned_end] : planned?.evidence_ids} calc />
        <Fact label="Termin po zmianach" value={fmtDate((pva.amended_end as string) ?? null)} ev={changes.at(-1)?.evidence_ids} />
        <Fact label="Wykonanie" value={fmtDate(pva.actual_end as string)} ev={actual?.evidence_ids} />
        <Fact label="Opóźnienie" value={pva.delay_days != null ? `${pva.delay_days} dni${pva.delay_vs_amended_days ? ` (${pva.delay_vs_amended_days} po aneksie)` : ''}` : '—'}
          ev={pva.evidence?.delay_days ? [pva.evidence.delay_days] : []} calc warn={Number(pva.delay_days) > 0} />
        <Fact label="Wartość umowy" value={fmtPln(pva.value as number)} ev={contract?.evidence_ids} />
        <Fact label="Wypłacono" value={fmtPln(pva.paid as number)} ev={t.items.find((i) => i.kind === 'paid')?.evidence_ids} />
        <Fact label="Wypłata / wartość" value={pva.paid_ratio != null ? String(pva.paid_ratio).replace('.', ',') : '—'} ev={pva.evidence?.paid_ratio ? [pva.evidence.paid_ratio] : []} calc
          warn={Number(pva.paid_ratio) > 1.05} />
        <Fact label="Oferta / szacunek" value={pva.evidence?.offer_vs_estimate ? 'netto vs brutto – nie porównujemy' : '—'} ev={pva.evidence?.offer_vs_estimate ? [pva.evidence.offer_vs_estimate] : []} calc />
      </div>

      <Card>
        <CardHeader title="Przebieg: plan vs rzeczywistość" description="Szary pas – okres planowany (umowa → termin pierwotny); czerwony – faktyczny; pomarańczowe linie – terminy po zmianach." actions={<BlockLabel label="dane_zrodlowe" />} />
        <CardContent>
          <div className="h-72" role="img" aria-label="Oś czasu projektu: postępowanie, umowa, zmiany, płatności">
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" dataKey="x" domain={[Math.min(...xs) - pad, Math.max(...xs) + pad]} scale="time"
                  tickFormatter={(v) => new Date(v).toLocaleDateString('pl-PL', { month: 'short', year: '2-digit' })} fontSize={11} />
                <YAxis type="number" dataKey="y" domain={[0.5, 4.5]} ticks={[1, 2, 3, 4]} tickFormatter={(v) => LANE_NAME[v] ?? ''} width={90} fontSize={11} />
                <ZAxis range={[90, 90]} />
                {contract?.date && planned?.date && <ReferenceArea x1={ts(contract.date)} x2={ts(planned.date)} y1={2.75} y2={3.25} fill="#94a3b8" fillOpacity={0.35} />}
                {planned?.date && actual?.date && ts(actual.date) > ts(planned.date) && <ReferenceArea x1={ts(planned.date)} x2={ts(actual.date)} y1={2.75} y2={3.25} fill="#dc2626" fillOpacity={0.25} />}
                {changes.map((c, i) => <ReferenceLine key={i} x={ts(c.date)} stroke="#d97706" strokeDasharray="4 3" />)}
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ payload }) => {
                  const p = payload?.[0]?.payload as (Item & { x: number }) | undefined
                  if (!p) return null
                  return <div className="rounded border border-slate-200 bg-white p-2 text-xs shadow"><div className="font-semibold">{KIND[p.kind]} · {fmtDate(p.date)}</div>
                    <div>{p.label}</div>{p.value != null && p.value !== 0 && <div>{fmtPln(p.value)}</div>}{p.planned && <div className="text-slate-500">(plan)</div>}</div>
                }} />
                <Scatter data={pts} shape={(props: { cx?: number; cy?: number; payload?: Item }) => {
                  const { cx = 0, cy = 0, payload } = props
                  const c = COLOR[payload?.kind ?? 'other']
                  return payload?.planned ? <circle cx={cx} cy={cy} r={6} fill="white" stroke={c} strokeWidth={2} /> : <circle cx={cx} cy={cy} r={6} fill={c} />
                }} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-600" aria-label="Legenda">
            {Object.entries(KIND).filter(([k]) => t.items.some((i) => i.kind === k)).map(([k, l]) => (
              <li key={k} className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR[k] }} />{l}</li>))}
            <li className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full border-2 border-slate-400 bg-white" />plan</li>
          </ul>
        </CardContent>
      </Card>

      {money.length > 0 && (
        <Card>
          <CardHeader title="Budżet → oferty → umowa → wypłata" description="Kwoty z ogłoszeń; podstawa VAT podana przy wartości (szacunek jest netto)." actions={<BlockLabel label="dane_zrodlowe" />} />
          <CardContent>
            <div className="h-56" role="img" aria-label="Porównanie kwot">
              <ResponsiveContainer>
                <BarChart data={money} layout="vertical" margin={{ left: 20, right: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                  <XAxis type="number" tickFormatter={(v) => `${(v / 1e6).toLocaleString('pl-PL', { maximumFractionDigits: 1 })} mln`} fontSize={11} />
                  <YAxis type="category" dataKey="name" width={120} fontSize={11} />
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
        <CardHeader title="Kroki przebiegu" description="Każdy krok z dowodem." />
        <ol className="divide-y divide-slate-100">
          {t.items.map((i, k) => (
            <li key={k} className="flex flex-wrap items-center gap-3 px-4 py-2 text-sm">
              <span className="w-24 shrink-0 font-mono text-xs text-slate-500">{fmtDate(i.date)}</span>
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: COLOR[i.kind] }} aria-hidden />
              <span className="w-32 shrink-0 text-xs text-slate-500">{KIND[i.kind]}{i.planned ? ' (plan)' : ''}</span>
              <span className="min-w-0 flex-1">{i.label}</span>
              {i.value != null && i.value !== 0 && <span className="tabular-nums">{fmtPln(i.value)}</span>}
              <EvidenceChip ids={i.evidence_ids} />
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
