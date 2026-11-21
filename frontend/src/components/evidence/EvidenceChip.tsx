import { AlertTriangle, Quote } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Dialog } from '@/components/ui'
import { cn } from '@/lib/utils'
import { EvidenceList } from './EvidencePanel'

/** Small "Źródło (n)" chip; opens the evidence panel. No ids → visible "brak źródła" warning (source test). */
export function EvidenceChip({ ids, title, className, label }: { ids?: string[] | null; title?: ReactNode; className?: string; label?: string }) {
  const [open, setOpen] = useState(false)
  const list = ids ?? []
  if (!list.length) {
    return <span className={cn('inline-flex items-center gap-1 rounded border border-rose-200 bg-rose-50 px-1.5 py-px text-[11px] text-rose-700', className)}
      title="Wynik bez źródła traktujemy jako nieudokumentowany"><AlertTriangle size={11} />brak źródła</span>
  }
  return (
    <>
      <button type="button" onClick={(e) => { e.stopPropagation(); setOpen(true) }}
        className={cn('inline-flex items-center gap-1 rounded border border-teal-200 bg-teal-50 px-1.5 py-px text-[11px] font-medium text-teal-800 hover:bg-teal-100 cursor-pointer',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500', className)}
        aria-label={`Pokaż źródła (${list.length})`}>
        <Quote size={11} aria-hidden />{label ?? 'Źródło'}{list.length > 1 ? ` · ${list.length}` : ''}
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title={title ?? 'Skąd pochodzi ta informacja'} className="w-[min(64rem,calc(100vw-2rem))]"
        description="Podgląd oryginalnego źródła – zaznaczone jest dokładnie to miejsce, z którego system odczytał wartość.">
        {open && <EvidenceList ids={list} />}
      </Dialog>
    </>
  )
}
