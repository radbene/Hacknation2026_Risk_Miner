import { ExternalLink, FileDown, Search } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { Badge, Card, CardHeader, Input, QueryState } from '@/components/ui'
import { containsQuote, highlight } from '@/lib/highlight'
import { cn, fmtDate, fmtDateTime } from '@/lib/utils'
import { allBundles, typeLabel } from '@/mocks'

export function mockNotice(id: string): Schemas['NoticeDetail'] | undefined {
  for (const b of allBundles()) { const n = b.notices.find((x) => x.id === id); if (n) return n }
  return undefined
}

export function useNotice(id: string) {
  return useApi(['notice', id], async () => unwrap(await api.GET('/api/notices/{notice_id}', { params: { path: { notice_id: id } } })), () => mockNotice(id))
}

/** Notice in numbered sections; the cited section is highlighted and scrolled into view, the quote marked. */
export function NoticeView({ noticeId, section, quote, compact }: { noticeId: string; section?: string; quote?: string; compact?: boolean }) {
  const q = useNotice(noticeId)
  return <QueryState q={q}>{(n) => <NoticeBody n={n} section={section} quote={quote} compact={compact} />}</QueryState>
}

function NoticeBody({ n, section, quote, compact }: { n: Schemas['NoticeDetail']; section?: string; quote?: string; compact?: boolean }) {
  const [filter, setFilter] = useState('')
  const hitRef = useRef<HTMLDivElement>(null)
  const secs = useMemo(() => {
    const f = filter.trim().toLowerCase()
    return (n.sections ?? []).filter((s) => !f || `${s.section} ${s.label} ${s.value}`.toLowerCase().includes(f))
  }, [n.sections, filter])
  const isHit = (s: Schemas['SectionOut']) => (section ? s.section === section : false) || (!section && !!quote && containsQuote(s.value, quote))
  useEffect(() => { hitRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }) }, [section, quote, n.id])
  let firstHit = true
  return (
    <Card>
      <CardHeader title={<span className="flex flex-wrap items-center gap-2"><Badge variant="brand">{typeLabel(n.notice_type)}</Badge>{n.notice_number}</span>}
        description={<>Opublikowano {fmtDate(n.published_at)}</>}
        actions={<>
          {n.url && <a href={n.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-brand hover:underline">Strona ogłoszenia <ExternalLink size={11} /></a>}
          {n.pdf_url && <a href={n.pdf_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-brand hover:underline">PDF <FileDown size={11} /></a>}
        </>} />
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-4 py-2 text-xs text-slate-500">
        <span>Pobrano: {fmtDateTime(n.retrieved_at)}{n.retrieved_from ? ` z ${new URL(n.retrieved_from).host}` : ''}</span>
        <label className="ml-auto flex items-center gap-1"><Search size={12} aria-hidden /><span className="sr-only">Szukaj w sekcjach</span>
          <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Szukaj w sekcjach" className="h-7 w-48 text-xs" /></label>
      </div>
      <div className={cn('divide-y divide-slate-100 overflow-auto', compact ? 'max-h-[28rem]' : 'max-h-[70vh]')}>
        {secs.map((s, i) => {
          const hit = isHit(s)
          const ref = hit && firstHit ? hitRef : undefined
          if (hit) firstHit = false
          return (
            <div key={`${s.section}-${i}`} ref={ref} id={`sec-${s.section}`} className={cn('grid grid-cols-[4.5rem_1fr] gap-2 px-4 py-1.5 text-sm', hit && 'section-hit')}>
              <span className="font-mono text-xs text-slate-500">{s.section}{s.part_no ? ` (cz. ${s.part_no})` : ''}</span>
              <div><span className="text-slate-600">{s.label}{s.value ? ':' : ''}</span>{' '}
                <span className="text-slate-900">{hit && quote ? highlight(s.value, [quote], true) : s.value}</span></div>
            </div>
          )
        })}
        {!secs.length && <p className="px-4 py-6 text-sm text-slate-500">Brak sekcji.</p>}
      </div>
    </Card>
  )
}
