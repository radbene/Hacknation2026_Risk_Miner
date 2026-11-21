import { Calculator, Database, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

export type BlockKind = 'dane_zrodlowe' | 'obliczenia' | 'wniosek_modelu'
const META: Record<BlockKind, { text: string; cls: string; Icon: typeof Database; hint: string }> = {
  dane_zrodlowe: { text: 'Dane źródłowe', cls: 'block-src', Icon: Database, hint: 'Fakt odczytany ze źródła – kliknij „Źródło”, by zobaczyć cytat.' },
  obliczenia: { text: 'Obliczenia', cls: 'block-calc', Icon: Calculator, hint: 'Wynik deterministycznego obliczenia – źródło pokazuje dane wejściowe i wzór.' },
  wniosek_modelu: { text: 'Wniosek modelu', cls: 'block-model', Icon: Sparkles, hint: 'Propozycja modelu językowego – wymaga akceptacji eksperta.' },
}

/** [Dane źródłowe] / [Obliczenia] / [Wniosek modelu] label (colours in index.css). */
export function BlockLabel({ label, className }: { label: BlockKind | string; className?: string }) {
  const m = META[label as BlockKind] ?? META.dane_zrodlowe
  return (
    <span className={cn('block-label', m.cls, className)} title={m.hint}>
      <m.Icon size={11} aria-hidden />[{m.text}]
    </span>
  )
}
