import { Link } from '@tanstack/react-router'
import { AlertTriangle, Calculator, ExternalLink, FileSpreadsheet, FileText, Globe, ShieldCheck } from 'lucide-react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { Badge, Empty, ErrorState, Loading } from '@/components/ui'
import { highlight } from '@/lib/highlight'
import { SOURCE_LABEL } from '@/lib/labels'
import { fmtDateTime } from '@/lib/utils'
import { mockEvidence } from '@/mocks'

type Ev = Schemas['EvidenceOut']

/** Loads evidence from /api/evidence?ids=; ids not (yet) in the DB are filled from mocks. */
export function useEvidence(ids: string[]) {
  const key = ids.slice().sort().join(',')
  return useApi<Ev[]>(['evidence', key], async () => {
    if (!ids.length) return []
    const got = unwrap(await api.GET('/api/evidence', { params: { query: { ids } } }))
    const have = new Set(got.map((e) => e.id))
    const missing = ids.filter((i) => !have.has(i))
    return [...got, ...mockEvidence(missing)]
  }, () => mockEvidence(ids), { enabled: ids.length > 0, staleTime: 5 * 60_000 })
}

export function locatorText(e: Ev): string {
  const l = e.locator ?? {}
  const parts: string[] = []
  if (l.notice_number) parts.push(`ogłoszenie ${l.notice_number}`)
  if (l.section) parts.push(`sekcja ${l.section}${l.label ? ` („${String(l.label).slice(0, 60)}”)` : ''}`)
  if (l.file && e.kind === 'xlsx_cell') parts.push(String(l.file))
  if (l.sheet) parts.push(`arkusz „${l.sheet}”`)
  if (l.row != null) parts.push(`wiersz ${l.row}`)
  if (l.column) parts.push(`kolumna „${l.column}”`)
  if (l.cell) parts.push(`komórka ${l.cell}`)
  if (l.page != null) parts.push(`str. ${l.page}`)
  if (l.paragraph != null) parts.push(`akapit ${l.paragraph}`)
  if (l.field) parts.push(`pole ${l.field}`)
  for (const [k, v] of Object.entries(l)) {
    if (!['notice_number', 'notice_type', 'section', 'label', 'file', 'sheet', 'row', 'column', 'cell', 'page', 'paragraph', 'field'].includes(k) && v != null && typeof v !== 'object')
      parts.push(`${k}: ${v}`)
  }
  return parts.join(' · ') || '—'
}

function KindIcon({ e }: { e: Ev }) {
  if (e.derivation) return <Calculator size={14} className="text-calc" />
  if (e.kind === 'xlsx_cell') return <FileSpreadsheet size={14} className="text-src" />
  if (e.kind === 'document_chunk') return <FileText size={14} className="text-src" />
  return <Globe size={14} className="text-src" />
}

export function EvidenceItem({ e, depth = 0 }: { e: Ev; depth?: number }) {
  const d = e.derivation as { formula?: string; inputs?: string[]; result?: unknown; values?: Record<string, unknown> } | null | undefined
  return (
    <article className="rounded-md border border-slate-200 bg-white p-3 text-sm" aria-label="Dowód">
      <div className="flex flex-wrap items-center gap-2">
        <KindIcon e={e} />
        <span className="font-medium">{SOURCE_LABEL[e.source_code] ?? e.source_code}</span>
        <Badge variant="outline">{e.kind}</Badge>
        {e.quote_verified === true && <Badge variant="success" title="Cytat zweryfikowany z treścią źródła"><ShieldCheck size={11} />cytat zweryfikowany</Badge>}
        {e.quote_verified === false && <Badge variant="danger"><AlertTriangle size={11} />cytat niezweryfikowany</Badge>}
      </div>
      <dl className="mt-2 grid grid-cols-[8rem_1fr] gap-x-3 gap-y-1 text-xs">
        <dt className="text-slate-500">Lokalizacja</dt><dd>{locatorText(e)}</dd>
        {e.url && (<><dt className="text-slate-500">Link stały</dt>
          <dd className="break-all"><a href={e.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand hover:underline">{e.url}<ExternalLink size={11} /></a></dd></>)}
        {e.retrieved_from && e.retrieved_from !== e.url && (<><dt className="text-slate-500">Pobrano z</dt><dd className="break-all text-slate-600">{e.retrieved_from}</dd></>)}
        <dt className="text-slate-500">Data pobrania</dt><dd>{fmtDateTime(e.retrieved_at)}</dd>
        {e.import_sha256 && (<><dt className="text-slate-500">SHA-256 pliku</dt><dd className="font-mono text-[11px] break-all">{e.import_sha256}</dd></>)}
      </dl>
      {e.quote && (
        <blockquote className="mt-2 rounded border-l-src bg-slate-50 px-3 py-2 text-sm">
          {highlight(e.quote, [e.quote])}
        </blockquote>
      )}
      {d && (
        <div className="mt-2 rounded border-l-calc bg-violet-50/40 px-3 py-2 text-xs">
          <div><span className="text-slate-500">Wzór: </span><code className="font-mono">{d.formula}</code></div>
          {d.values && Object.keys(d.values).length > 0 && (
            <div className="mt-1"><span className="text-slate-500">Wartości: </span>{Object.entries(d.values).map(([k, v]) => `${k} = ${typeof v === 'number' ? v.toLocaleString('pl-PL') : String(v)}`).join('; ')}</div>
          )}
          {d.result !== undefined && <div className="mt-1"><span className="text-slate-500">Wynik: </span><b>{String(d.result)}</b></div>}
          {d.inputs && d.inputs.length > 0 && depth < 2 && (
            <div className="mt-2"><div className="mb-1 text-slate-500">Dane wejściowe ({d.inputs.length}):</div><EvidenceList ids={d.inputs} depth={depth + 1} /></div>
          )}
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-3 text-xs">
        {e.notice_id && (
          <Link to="/ogloszenia/$noticeId" params={{ noticeId: e.notice_id }} search={{ section: e.locator?.section as string | undefined, quote: e.quote ?? undefined }}
            className="text-brand hover:underline">Pokaż w treści ogłoszenia →</Link>
        )}
        {e.document_id && (
          <Link to="/dokumenty/$documentId" params={{ documentId: e.document_id }} search={{ page: e.locator?.page as number | undefined, quote: e.quote ?? undefined }}
            className="text-brand hover:underline">Pokaż w dokumencie (str. {String(e.locator?.page ?? '?')}) →</Link>
        )}
      </div>
    </article>
  )
}

export function EvidenceList({ ids, depth = 0 }: { ids: string[]; depth?: number }) {
  const q = useEvidence(ids)
  if (!ids.length) return <Empty>Brak źródła – wynik nieudokumentowany.</Empty>
  if (q.isLoading) return <Loading label="Wczytywanie źródeł…" />
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />
  const items = q.data ?? []
  return (
    <div className="flex flex-col gap-2">
      {items.map((e) => <EvidenceItem key={e.id} e={e} depth={depth} />)}
      {items.length < ids.length && <p className="text-xs text-amber-700">{ids.length - items.length} z {ids.length} dowodów nie znaleziono w bazie.</p>}
    </div>
  )
}
