import { X } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Modal dialog on the native <dialog> element (focus trap, Esc to close, backdrop). */
export function Dialog({ open, onClose, title, description, children, footer, className }:
  { open: boolean; onClose: () => void; title: ReactNode; description?: ReactNode; children?: ReactNode; footer?: ReactNode; className?: string }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal?.()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog ref={ref} onClose={onClose} onCancel={(e) => { e.preventDefault(); onClose() }}
      onClick={(e) => { if (e.target === ref.current) onClose() }}
      className={cn('m-auto w-[min(42rem,calc(100vw-2rem))] border-2 border-ink bg-surface p-0 shadow-lg backdrop:bg-ink/40', className)}>
      {open && (
        <div className="flex max-h-[85vh] flex-col">
          <div className="flex items-center gap-3 border-b-2 border-ink px-4 py-2">
            <span className="h-3.5 w-3.5 shrink-0 border-2 border-ink" aria-hidden />
            <div className="min-w-0">
              <h2 className="font-mono text-sm font-semibold">{title}</h2>
              {description && <p className="mt-0.5 text-xs text-slate-600">{description}</p>}
            </div>
            <span className="stripes h-3 min-w-6 flex-1" aria-hidden />
            <button onClick={onClose} aria-label="Zamknij" className="border-2 border-ink p-0.5 text-ink hover:bg-ink hover:text-paper cursor-pointer"><X size={14} /></button>
          </div>
          <div className="overflow-auto px-5 py-4">{children}</div>
          {footer && <div className="flex justify-end gap-3 border-t-2 border-ink px-5 py-3">{footer}</div>}
        </div>
      )}
    </dialog>
  )
}
