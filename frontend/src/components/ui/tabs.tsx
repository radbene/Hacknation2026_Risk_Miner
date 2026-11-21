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
      <div className="overflow-x-auto pb-1 [scrollbar-width:thin]"><div role="tablist" className="inline-flex h-9 items-center gap-0.5 rounded-lg bg-slate-100 p-[3px] text-slate-500">
        {tabs.map((t, i) => {
          const active = t.value === value
          return (
            <button key={t.value} ref={(el) => { refs.current[i] = el }} role="tab" id={`${id}-t-${t.value}`}
              aria-selected={active} aria-controls={`${id}-p-${t.value}`} tabIndex={active ? 0 : -1}
              onClick={() => onChange(t.value)} onKeyDown={(e) => onKey(e, i)}
              className={cn('flex h-full items-center gap-1.5 whitespace-nowrap rounded-md px-3 text-sm font-medium cursor-pointer transition-colors duration-150',
                'outline-none focus-visible:ring-[3px] focus-visible:ring-brand/30',
                active ? 'bg-white text-slate-950 shadow-xs' : 'hover:text-slate-900')}>
              {t.label}
              {t.count !== undefined && <span className="rounded-md bg-slate-200/70 px-1.5 text-[11px] tabular-nums text-slate-600">{t.count}</span>}
            </button>
          )
        })}
      </div></div>
      <div role="tabpanel" id={`${id}-p-${value}`} aria-labelledby={`${id}-t-${value}`} className="pt-4">{children}</div>
    </div>
  )
}
