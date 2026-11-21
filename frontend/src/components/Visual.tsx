/** Visual building blocks instead of tables: proportions, ranges, score bars, key facts. */
import type { ReactNode } from 'react'
import { cn, fmtNum } from '@/lib/utils'

const pct = (x?: number | null) => (x == null ? '—' : `${Math.round(x * 100)}%`)

/** "W 5 z 12 podobnych …" + bar with the 95% interval as a lighter band. */
export function Proportion({ k, n, estimate, low, high, what, tone = 'rose' }:
  { k?: number | null; n?: number | null; estimate?: number | null; low?: number | null; high?: number | null; what: string; tone?: 'rose' | 'amber' | 'brand' }) {
  const fill = { rose: 'bg-rose-500', amber: 'bg-amber-500', brand: 'bg-brand' }[tone]
  const band = { rose: 'bg-rose-200', amber: 'bg-amber-200', brand: 'bg-brand-soft' }[tone]
  return (
    <div>
      <div className="text-sm">
        {k != null && n ? <>W <b>{k}</b> z <b>{n}</b> {what}</> : <>Brak danych</>}
        {estimate != null && <>, po wygładzeniu <b>{pct(estimate)}</b></>}
      </div>
      <div className="relative mt-1 h-2.5 w-full rounded-full bg-slate-100" aria-hidden>
        {low != null && high != null && <div className={cn('absolute inset-y-0 rounded-full', band)} style={{ left: `${low * 100}%`, width: `${Math.max(1, (high - low) * 100)}%` }} />}
        {estimate != null && <div className={cn('absolute inset-y-0 w-1 rounded-full', fill)} style={{ left: `calc(${estimate * 100}% - 2px)` }} />}
      </div>
      {low != null && high != null && <div className="mt-0.5 text-[11px] text-slate-500">prawdopodobnie między {pct(low)} a {pct(high)}</div>}
    </div>
  )
}

/** Typical / cautious / pessimistic values on one line (P50 · P80 · P95). */
export function Spread({ p50, p80, p95, unit = '', digits = 0, third = 'pesymistycznie' }: { p50?: number | null; p80?: number | null; p95?: number | null; unit?: string; digits?: number; third?: string }) {
  const f = (v?: number | null) => (v == null ? '—' : `${fmtNum(v, digits)}${unit}`)
  return (
    <div className="grid grid-cols-3 gap-2 text-center">
      {[['typowo', p50, 'P50'], ['z zapasem', p80, 'P80'], [third, p95, 'P95']].map(([l, v, code]) => (
        <div key={String(code)} className="rounded-md bg-slate-50 px-2 py-1.5">
          <div className="text-[11px] text-slate-500">{l as string}</div>
          <div className="text-base font-semibold tabular-nums">{f(v as number | null)}</div>
        </div>))}
    </div>
  )
}

/** Horizontal bar 0..1 with a label and a verdict. */
export function ScoreBar({ value, label, detail, className }: { value?: number | null; label: ReactNode; detail?: ReactNode; className?: string }) {
  const v = value ?? null
  const color = v == null ? 'bg-slate-300' : v >= 0.8 ? 'bg-emerald-500' : v >= 0.5 ? 'bg-amber-500' : 'bg-rose-400'
  return (
    <div className={cn('text-xs', className)}>
      <div className="flex items-baseline justify-between gap-2"><span className="font-medium text-slate-700">{label}</span>
        <span className="text-slate-500">{v == null ? 'brak danych' : v >= 0.8 ? 'zgodne' : v >= 0.5 ? 'częściowo' : 'różne'}</span></div>
      <div className="mt-0.5 h-1.5 w-full rounded-full bg-slate-100"><div className={cn('h-full rounded-full', color)} style={{ width: `${Math.round((v ?? 0) * 100)}%` }} /></div>
      {detail && <div className="mt-0.5 text-slate-500">{detail}</div>}
    </div>
  )
}

/** Key fact: label above, value below (used instead of table rows). */
export function Fact({ label, value, warn, hint }: { label: ReactNode; value: ReactNode; warn?: boolean; hint?: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={cn('font-medium', warn && 'text-rose-700')}>{value ?? '—'}</div>
      {hint && <div className="text-[11px] text-slate-500">{hint}</div>}
    </div>
  )
}

/** Confidence in words. */
export function confidenceWords(c?: number | null) {
  if (c == null) return 'nieokreślona'
  if (c >= 0.95) return 'bardzo wysoka'
  if (c >= 0.8) return 'wysoka'
  if (c >= 0.6) return 'średnia'
  return 'niska'
}
