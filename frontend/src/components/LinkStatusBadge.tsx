import { Badge } from '@/components/ui'
import { LINK_STATUS_LABEL } from '@/lib/labels'

const V = { linked: 'success', uncertain: 'warning', unlinked: 'default', rejected: 'danger' } as const
export function LinkStatusBadge({ status }: { status: string }) {
  return <Badge variant={V[status as keyof typeof V] ?? 'default'}>{LINK_STATUS_LABEL[status] ?? status}</Badge>
}
export function RiskCodes({ codes }: { codes?: string[] | null }) {
  return <span className="inline-flex flex-wrap gap-1">{(codes ?? []).map((c) => <RiskCode key={c} code={c} />)}</span>
}
import { RISK_NAMES } from '@/lib/labels'
export function RiskCode({ code }: { code: string }) {
  return <Badge variant="violet" title={RISK_NAMES[code] ?? code} className="font-mono">{code}</Badge>
}
export function Completeness({ value }: { value?: number | null }) {
  if (value == null) return <span className="text-xs text-slate-400">—</span>
  const pct = Math.round(value * 100)
  const c = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <span className="inline-flex items-center gap-1.5 text-xs tabular-nums" title={`Kompletność ${pct}%`}>
      <span className="h-1.5 w-14 overflow-hidden rounded-full bg-slate-200"><span className={`block h-full ${c}`} style={{ width: `${pct}%` }} /></span>{pct}%
    </span>
  )
}
