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
      className={cn('m-auto w-[min(42rem,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white p-0 shadow-lg backdrop:bg-black/50', className)}>
      {open && (
        <div className="flex max-h-[85vh] flex-col">
          <div className="flex items-start justify-between gap-4 px-6 pt-5 pb-3">
            <div>
              <h2 className="text-lg font-semibold leading-none tracking-tight">{title}</h2>
              {description && <p className="mt-1.5 text-sm text-slate-500">{description}</p>}
            </div>
            <button onClick={onClose} aria-label="Zamknij" className="rounded p-1 text-slate-500 hover:bg-slate-100 cursor-pointer"><X size={16} /></button>
          </div>
          <div className="overflow-auto px-6 py-3">{children}</div>
          {footer && <div className="flex justify-end gap-2 px-6 pt-3 pb-5">{footer}</div>}
        </div>
      )}
    </dialog>
  )
}
