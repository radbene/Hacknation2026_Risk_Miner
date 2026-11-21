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
      className={cn('m-auto w-[min(42rem,calc(100vw-2rem))] rounded-lg border border-slate-200 bg-white p-0 shadow-xl backdrop:bg-slate-900/40', className)}>
      {open && (
        <div className="flex max-h-[85vh] flex-col">
          <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-3">
            <div>
              <h2 className="text-base font-semibold">{title}</h2>
              {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
            </div>
            <button onClick={onClose} aria-label="Zamknij" className="rounded p-1 text-slate-500 hover:bg-slate-100 cursor-pointer"><X size={16} /></button>
          </div>
          <div className="overflow-auto px-5 py-4">{children}</div>
          {footer && <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">{footer}</div>}
        </div>
      )}
    </dialog>
  )
}
