import { cn } from '@/lib/utils'

export type BlockKind = 'dane_zrodlowe' | 'obliczenia' | 'wniosek_modelu'
const META: Record<BlockKind, { text: string; cls: string; hint: string }> = {
  dane_zrodlowe: { text: 'Dane źródłowe', cls: 'block-src', hint: 'Fakt odczytany ze źródła.' },
  obliczenia: { text: 'Obliczenia', cls: 'block-calc', hint: 'Wynik obliczenia z bazy przypadków.' },
  wniosek_modelu: { text: 'Wniosek modelu', cls: 'block-model', hint: 'Propozycja modelu językowego, wymaga akceptacji eksperta.' },
}

/** [Dane źródłowe] / [Obliczenia] / [Wniosek modelu] label (colours in index.css). */
export function BlockLabel({ label, className }: { label: BlockKind | string; className?: string }) {
  const m = META[label as BlockKind] ?? META.dane_zrodlowe
  return (
    <span className={cn('block-label', m.cls, className)} title={m.hint}>
      [{m.text}]
    </span>
  )
}
