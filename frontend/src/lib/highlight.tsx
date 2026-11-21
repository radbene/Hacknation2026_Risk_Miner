import type { ReactNode } from 'react'

/** Normalisation used on both sides of a quote match: NFKC, NBSP, typographic quotes/dashes, whitespace, PDF hyphenation. */
export function normalise(s: string): string {
  return s.normalize('NFKC').replace(/­/g, '').replace(/-\n/g, '').replace(/[   ]/g, ' ')
    .replace(/[„”“"«»]/g, '"').replace(/[‘’‚']/g, "'").replace(/[–—]/g, '-').replace(/\s+/g, ' ').trim()
}

/** Returns `text` with the first occurrence of each quote wrapped in <mark>. Matching is case-insensitive on normalised text. */
export function highlight(text: string, quotes: (string | null | undefined)[], strong = false): ReactNode {
  const t = normalise(text)
  const lower = t.toLowerCase()
  const ranges: [number, number][] = []
  for (const q of quotes) {
    if (!q) continue
    const nq = normalise(q).toLowerCase()
    if (!nq) continue
    const i = lower.indexOf(nq)
    if (i >= 0) ranges.push([i, i + nq.length])
  }
  if (!ranges.length) return t
  ranges.sort((a, b) => a[0] - b[0])
  const out: ReactNode[] = []
  let pos = 0
  ranges.forEach(([a, b], k) => {
    if (a < pos) return
    if (a > pos) out.push(t.slice(pos, a))
    out.push(<mark key={k} className={strong ? 'quote-strong' : 'quote'}>{t.slice(a, b)}</mark>)
    pos = b
  })
  if (pos < t.length) out.push(t.slice(pos))
  return out
}

export function containsQuote(text: string, quote?: string | null) {
  return !!quote && normalise(text).toLowerCase().includes(normalise(quote).toLowerCase())
}
