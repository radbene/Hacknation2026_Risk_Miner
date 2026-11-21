import { useId, useRef, type ReactNode, type KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'

export interface TabDef { value: string; label: ReactNode; count?: number }

/** Accessible tab list (WAI-ARIA tabs pattern, arrow-key navigation). Controlled. */
export function Tabs({ tabs, value, onChange, children, className }:
  { tabs: TabDef[]; value: string; onChange: (v: string) => void; children: ReactNode; className?: string }) {
  const id = useId()
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const onKey = (e: KeyboardEvent, i: number) => {
    let n = -1
    if (e.key === 'ArrowRight') n = (i + 1) % tabs.length
    else if (e.key === 'ArrowLeft') n = (i - 1 + tabs.length) % tabs.length
    else if (e.key === 'Home') n = 0
    else if (e.key === 'End') n = tabs.length - 1
    if (n >= 0) { e.preventDefault(); onChange(tabs[n].value); refs.current[n]?.focus() }
  }
  return (
    <div className={className}>
      <div className="overflow-x-auto pb-2 [scrollbar-width:thin]"><div role="tablist" className="inline-flex items-stretch border-2 border-ink bg-surface">
        {tabs.map((t, i) => {
          const active = t.value === value
          return (
            <button key={t.value} ref={(el) => { refs.current[i] = el }} role="tab" id={`${id}-t-${t.value}`}
              aria-selected={active} aria-controls={`${id}-p-${t.value}`} tabIndex={active ? 0 : -1}
              onClick={() => onChange(t.value)} onKeyDown={(e) => onKey(e, i)}
              className={cn('flex items-center gap-1.5 whitespace-nowrap border-r-2 border-ink px-3 py-1.5 font-mono text-xs font-medium uppercase tracking-wide cursor-pointer last:border-r-0',
                'outline-none focus-visible:bg-brand-soft',
                active ? 'bg-ink text-paper' : 'text-ink hover:bg-brand-soft')}>
              {t.label}
              {t.count !== undefined && <span className={cn('px-1 text-[11px] tabular-nums', active ? 'bg-paper text-ink' : 'bg-ink text-paper')}>{t.count}</span>}
            </button>
          )
        })}
      </div></div>
      <div role="tabpanel" id={`${id}-p-${value}`} aria-labelledby={`${id}-t-${value}`} className="pt-4">{children}</div>
    </div>
  )
}
