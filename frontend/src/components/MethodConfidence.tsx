import { Tooltip } from '@/components/ui'
import { methodLabel } from '@/lib/labels'
import { cn } from '@/lib/utils'

/** Method + confidence meter (green ≥ 0.9, amber ≥ 0.7, red below). */
export function MethodConfidence({ method, confidence, compact }: { method?: string | null; confidence?: number | null; compact?: boolean }) {
  const c = confidence ?? null
  const color = c == null ? 'bg-slate-300' : c >= 0.9 ? 'bg-emerald-500' : c >= 0.7 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <Tooltip content={`Metoda: ${methodLabel(method)} · pewność ${c == null ? 'brak' : c.toFixed(2)}`}>
      <span className="inline-flex items-center gap-1.5 text-xs text-slate-600" tabIndex={0}>
        {!compact && <span className="max-w-40 truncate">{methodLabel(method)}</span>}
        <span className="relative h-1.5 w-12 overflow-hidden rounded-full bg-slate-200" aria-hidden>
          <span className={cn('absolute inset-y-0 left-0 rounded-full', color)} style={{ width: `${Math.round((c ?? 0) * 100)}%` }} />
        </span>
        <span className="tabular-nums">{c == null ? '—' : c.toFixed(2).replace('.', ',')}</span>
      </span>
    </Tooltip>
  )
}
