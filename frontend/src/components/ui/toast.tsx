import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react'
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Kind = 'success' | 'error' | 'info'
interface ToastItem { id: number; kind: Kind; title: string; description?: string }
interface Ctx { toast: (t: Omit<ToastItem, 'id'>) => void }

const ToastCtx = createContext<Ctx>({ toast: () => {} })
export const useToast = () => useContext(ToastCtx)

let seq = 0
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const dismiss = useCallback((id: number) => setItems((xs) => xs.filter((x) => x.id !== id)), [])
  const toast = useCallback((t: Omit<ToastItem, 'id'>) => {
    const id = ++seq
    setItems((xs) => [...xs.slice(-3), { ...t, id }])
    setTimeout(() => dismiss(id), 5000)
  }, [dismiss])
  return (
    <ToastCtx.Provider value={{ toast }}>
      {children}
      <div aria-live="polite" role="status" className="fixed bottom-4 right-4 z-[100] flex w-80 flex-col gap-2">
        {items.map((t) => {
          const Icon = t.kind === 'success' ? CheckCircle2 : t.kind === 'error' ? TriangleAlert : Info
          return (
            <div key={t.id} className={cn('flex items-start gap-2 rounded-md border bg-white p-3 text-sm shadow-lg',
              t.kind === 'success' && 'border-emerald-200', t.kind === 'error' && 'border-rose-200')}>
              <Icon size={16} className={cn('mt-0.5 shrink-0', t.kind === 'success' ? 'text-emerald-600' : t.kind === 'error' ? 'text-rose-600' : 'text-brand')} />
              <div className="min-w-0 flex-1">
                <div className="font-medium">{t.title}</div>
                {t.description && <div className="mt-0.5 text-xs text-slate-600">{t.description}</div>}
              </div>
              <button onClick={() => dismiss(t.id)} aria-label="Zamknij powiadomienie" className="text-slate-400 hover:text-slate-700 cursor-pointer"><X size={14} /></button>
            </div>
          )
        })}
      </div>
    </ToastCtx.Provider>
  )
}
