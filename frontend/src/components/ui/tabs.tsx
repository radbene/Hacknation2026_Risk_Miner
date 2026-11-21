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
      <div role="tablist" className="flex gap-1 overflow-x-auto border-b border-slate-200">
        {tabs.map((t, i) => {
          const active = t.value === value
          return (
            <button key={t.value} ref={(el) => { refs.current[i] = el }} role="tab" id={`${id}-t-${t.value}`}
              aria-selected={active} aria-controls={`${id}-p-${t.value}`} tabIndex={active ? 0 : -1}
              onClick={() => onChange(t.value)} onKeyDown={(e) => onKey(e, i)}
              className={cn('-mb-px flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2 text-sm cursor-pointer',
                'focus-visible:outline-none focus-visible:bg-brand-soft',
                active ? 'border-brand font-semibold text-brand' : 'border-transparent text-slate-600 hover:text-slate-900')}>
              {t.label}
              {t.count !== undefined && <span className="rounded-full bg-slate-100 px-1.5 text-[10px] text-slate-600">{t.count}</span>}
            </button>
          )
        })}
      </div>
      <div role="tabpanel" id={`${id}-p-${value}`} aria-labelledby={`${id}-t-${value}`} className="pt-4">{children}</div>
    </div>
  )
}
