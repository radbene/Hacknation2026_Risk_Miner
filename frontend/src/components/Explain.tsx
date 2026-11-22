/** Plain-language explanations: a section intro, glossary terms with a popover, and "how was it calculated". */
import { ChevronDown, HelpCircle } from 'lucide-react'
import { useId, useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export const GLOSSARY: Record<string, string> = {
  'P50': 'Wartość środkowa: połowa podobnych przypadków miała mniej, połowa więcej. To „typowy” wynik.',
  'P80': '8 na 10 podobnych przypadków miało nie więcej. Dobra wartość do planowania z zapasem.',
  'P95': '19 na 20 podobnych przypadków miało nie więcej. Scenariusz pesymistyczny.',
  'przedział 95%': 'Zakres, w którym z 95-procentową pewnością leży prawdziwa wartość. Im mniej przypadków, tym jest szerszy.',
  'percentyl': 'Pozycja na tle innych: P70 oznacza, że wartość jest wyższa niż w 70 na 100 podobnych przypadków.',
  'n': 'Liczba przypadków, na których policzono wynik. Przy małym n traktuj wynik ostrożnie.',
  'waga': 'Jak bardzo dana cecha liczy się przy ocenie podobieństwa (suma wag = 100%). Wagi ustawia ekspert w „Wiedzy eksperckiej”.',
  'podobieństwo': 'Od 0% do 100%: jak bardzo inna inwestycja przypomina opisaną. Liczymy je z cech (podsektor, skala, formuła, województwo) i ze słów w opisie.',
  'wygładzenie': 'Gdy podobnych przypadków jest mało, do ich wyniku dokładamy 8 „przeciętnych” przypadków z szerszej grupy (np. całego podsektora). Dzięki temu kilka nietypowych inwestycji nie daje skrajnej liczby, np. 0% albo 100%. Im więcej podobnych przypadków, tym mniejszy wpływ szerszej grupy.',
  'poziom odniesienia': 'Na jakiej grupie policzono wynik: najbardziej podobne inwestycje, a gdy jest ich za mało, cały podsektor albo wszystkie inwestycje wodno-kanalizacyjne.',
  'pewność': 'Jak bardzo system jest pewny swojej propozycji (0–100%). Pozycje mniej pewne są wyżej w kolejce eksperta.',
  'rezerwa P80': 'Kwota ponad budżet na zmiany umowy i roboty dodatkowe, wystarczająca w 8 na 10 podobnych przypadków: budżet × (P80 stosunku wypłaty do wartości umowy − 1). Nie obejmuje ryzyka, że oferty w przetargu będą droższe od kosztorysu.',
  'kategoria ryzyka': 'Kod R01–R15 z katalogu ekspertów MFiPR, np. R03: dostęp do terenu, R06: nierealny harmonogram.',
}

/** Box at the top of every section/tab: what it shows and what you can do here. */
export function Intro({ title, children, can, className }: { title?: ReactNode; children: ReactNode; can?: ReactNode[]; className?: string }) {
  return (
    <div className={cn('mb-5 border-2 border-ink border-l-[6px] border-l-brand bg-surface px-4 py-3 text-sm text-slate-700', className)}>
      <div>
        <div className="space-y-1">
          {title && <div className="font-bold text-ink">{title}</div>}
          <div>{children}</div>
          {can && can.length > 0 && (
            <div><span className="font-medium text-slate-900">Co możesz tu zrobić: </span>
              <ul className="mt-0.5 list-disc pl-5">{can.map((c, i) => <li key={i}>{c}</li>)}</ul></div>)}
        </div>
      </div>
    </div>
  )
}

/** A term with a small "?" that explains it in plain words. */
export function Term({ t, children, explain }: { t: string; children?: ReactNode; explain?: string }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const text = explain ?? GLOSSARY[t] ?? ''
  return (
    <span className="relative inline-flex items-baseline gap-0.5">
      <span className="underline decoration-dotted decoration-slate-400 underline-offset-2">{children ?? t}</span>
      {text && <button type="button" aria-describedby={open ? id : undefined} aria-label={`Wyjaśnij: ${t}`}
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o) }} onBlur={() => setOpen(false)}
        className="cursor-pointer text-slate-400 hover:text-brand"><HelpCircle size={12} /></button>}
      {open && <span role="tooltip" id={id}
        className="absolute left-0 top-full z-30 mt-1 w-72 border-2 border-ink bg-surface p-2 text-xs font-normal normal-case text-slate-800 shadow-sm">{text}</span>}
    </span>
  )
}

/** Collapsible "Jak to policzono?" with a formula whose symbols are explained in words. */
export function HowCalculated({ children, label = 'Jak to policzono?' }: { children: ReactNode; label?: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="text-xs">
      <button type="button" onClick={() => setOpen((o) => !o)} className="inline-flex cursor-pointer items-center gap-1 text-slate-500 hover:text-brand" aria-expanded={open}>
        <ChevronDown size={12} className={cn('transition-transform', open && 'rotate-180')} />{label}
      </button>
      {open && <div className="mt-1 border-2 border-dashed border-ink/40 bg-violet-50/60 px-3 py-2 leading-relaxed text-slate-800">{children}</div>}
    </div>
  )
}
