/** Source preview: the original file with the cited value marked – the notice with its section highlighted, the
 * spreadsheet row with the cell marked, the document page with the quote, or the inputs of a calculation. */
import { Calculator, ExternalLink, FileSpreadsheet, FileText, Globe } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { Empty, ErrorState, Loading } from '@/components/ui'
import { highlight } from '@/lib/highlight'
import { cn, fmtDate } from '@/lib/utils'
import { NoticeView } from './NoticeView'
import { PdfViewer } from './PdfViewer'

type Ev = Schemas['EvidenceOut']
interface SheetCtx { type: 'sheet'; file: string; sheet?: string; row: number; column?: string; header?: string; cells: { header: string; value: unknown }[]; project_code?: string }

export function useEvidence(ids: string[]) {
  const key = ids.slice().sort().join(',')
  return useApi<Ev[]>(['evidence', key], async () => {
    if (!ids.length) return []
    return unwrap(await api.GET('/api/evidence', { params: { query: { ids } } }))
  }, undefined, { enabled: ids.length > 0, staleTime: 5 * 60_000 })
}

const NOTICE_PL: Record<string, string> = {
  ContractNotice: 'Ogłoszenie o zamówieniu', TenderResultNotice: 'Ogłoszenie o wyniku', AgreementUpdateNotice: 'Ogłoszenie o zmianie umowy',
  ContractPerformingNotice: 'Ogłoszenie o wykonaniu umowy',
}
const FIELD_PL: Record<string, string> = {
  noticeNumber: 'numer ogłoszenia', organizationNationalId: 'NIP zamawiającego', organizationName: 'nazwa zamawiającego',
  orderObject: 'przedmiot zamówienia', cpvCode: 'kod CPV', publicationDate: 'data publikacji', tenderId: 'identyfikator postępowania',
}

/** Human title of one source, no ids or hashes. */
export function sourceTitle(e: Ev): string {
  const l = (e.locator ?? {}) as Record<string, unknown>
  if (e.derivation) return 'Obliczenie RISK MINER'
  if (e.kind === 'xlsx_cell') return `Plik organizatora: wiersz ${l.row}, kolumna „${l.header ?? l.column}”`
  if (e.document_id) return `Dokument${l.file_name ? ` „${l.file_name}”` : ''}${l.page != null ? `, str. ${l.page}` : ''}`
  if (e.notice_id) {
    const t = NOTICE_PL[String(l.notice_type)] ?? 'Ogłoszenie BZP'
    const where = l.section ? `pkt ${l.section}${l.label ? ` „${String(l.label).replace(/\)$/, '')}”` : ''}` : l.field ? FIELD_PL[String(l.field)] ?? 'pole ogłoszenia' : ''
    return `${t} ${l.notice_number ?? ''}${where ? ` – ${where}` : ''}`
  }
  return 'Źródło'
}

function Icon({ e }: { e: Ev }) {
  if (e.derivation) return <Calculator size={14} className="text-calc" />
  if (e.kind === 'xlsx_cell') return <FileSpreadsheet size={14} className="text-src" />
  if (e.document_id) return <FileText size={14} className="text-src" />
  return <Globe size={14} className="text-src" />
}

/** List of sources on the left, preview of the selected one on the right. */
export function EvidenceList({ ids, depth = 0 }: { ids: string[]; depth?: number }) {
  const q = useEvidence(ids)
  const [sel, setSel] = useState(0)
  if (!ids.length) return <Empty>Brak źródła – wynik nieudokumentowany.</Empty>
  if (q.isLoading) return <Loading label="Wczytywanie źródeł…" />
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />
  const items = q.data ?? []
  if (!items.length) return <Empty>Nie znaleziono źródła w bazie.</Empty>
  const cur = items[Math.min(sel, items.length - 1)]
  return (
    <div className={cn('grid gap-3', items.length > 1 && 'md:grid-cols-[15rem_1fr]')}>
      {items.length > 1 && (
        <ul className="space-y-1 text-xs" aria-label="Źródła">{items.map((e, i) => (
          <li key={e.id}><button onClick={() => setSel(i)} className={cn('flex w-full cursor-pointer items-start gap-1.5 rounded border p-2 text-left',
            i === sel ? 'border-brand bg-brand-soft' : 'border-slate-200 hover:bg-slate-50')}>
            <Icon e={e} /><span>{sourceTitle(e)}</span></button></li>))}</ul>)}
      <SourcePreview e={cur} depth={depth} />
    </div>
  )
}

export function SourcePreview({ e, depth = 0 }: { e: Ev; depth?: number }) {
  return (
    <div className="min-w-0 space-y-2">
      <div className="flex flex-wrap items-center gap-2 text-sm font-medium"><Icon e={e} />{sourceTitle(e)}</div>
      <div className="text-xs text-slate-500">
        {e.retrieved_at && <>pobrano {fmtDate(e.retrieved_at)}</>}
        {e.quote_verified === true && <> · cytat sprawdzony w treści źródła</>}
        {e.url && <> · <a href={e.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-brand hover:underline">oryginał w e-Zamówieniach<ExternalLink size={10} /></a></>}
      </div>
      {e.derivation ? <Calculation e={e} depth={depth} />
        : e.kind === 'xlsx_cell' ? <SheetRow e={e} />
        : e.document_id ? <DocumentPreview e={e} />
        : e.notice_id ? <NoticeView noticeId={e.notice_id} section={(e.locator?.section as string) || undefined} quote={e.quote ?? undefined} compact />
        : e.quote ? <blockquote className="rounded bg-slate-50 px-3 py-2 text-sm">{highlight(e.quote, [e.quote])}</blockquote> : null}
    </div>
  )
}

function SheetRow({ e }: { e: Ev }) {
  const q = useApi<SheetCtx>(['evidence-context', e.id], async () => (await (await fetch(`/api/evidence/${e.id}/context`)).json()) as SheetCtx)
  if (q.isLoading) return <Loading />
  const d = q.data
  if (!d || d.type !== 'sheet') return null
  return (
    <div className="rounded-md border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-3 py-1.5 text-xs text-slate-500">
        Plik „{d.file}”, arkusz „{d.sheet}”, wiersz {d.row} – zaznaczona komórka, z której pochodzi wartość</div>
      <div className="max-h-[55vh] overflow-auto p-2">
        <div className="grid gap-1 sm:grid-cols-2">{d.cells.map((c) => {
          const hit = c.header === d.header
          return (
            <div key={c.header} className={cn('rounded px-2 py-1 text-xs', hit ? 'bg-yellow-100 ring-2 ring-yellow-400' : 'bg-slate-50')}
              ref={hit ? (el) => el?.scrollIntoView({ block: 'center' }) : undefined}>
              <div className="text-slate-500">{c.header}</div>
              <div className={cn('break-words', hit ? 'font-semibold text-slate-900' : 'text-slate-800')}>{c.value == null || c.value === '' ? '—' : String(c.value)}</div>
            </div>)
        })}</div>
      </div>
    </div>
  )
}

function DocumentPreview({ e }: { e: Ev }) {
  const doc = useApi(['document', e.document_id], async () => unwrap(await api.GET('/api/documents/{document_id}', { params: { path: { document_id: e.document_id! } } })))
  const chunks = useApi(['document', e.document_id, 'chunks'], async () => unwrap(await api.GET('/api/documents/{document_id}/chunks', { params: { path: { document_id: e.document_id! } } })))
  if (doc.isLoading) return <Loading />
  const d = doc.data
  const page = (e.locator?.page as number | undefined) ?? 1
  if (d?.mime?.includes('pdf') || d?.file_name?.toLowerCase().endsWith('.pdf')) {
    return <PdfViewer url={`/api/documents/${e.document_id}/file`} page={page} quote={e.quote ?? undefined} />
  }
  const cs = (chunks.data ?? []).filter((c) => c.page == null || c.page === page)
  return (
    <div className="max-h-[60vh] space-y-1 overflow-auto rounded-md border border-slate-200 bg-white p-3 text-sm">
      {cs.map((c) => <p key={c.id}>{highlight(c.text, [e.quote], true)}</p>)}
      {!cs.length && e.quote && <p>{highlight(e.quote, [e.quote], true)}</p>}
    </div>
  )
}

function Calculation({ e, depth }: { e: Ev; depth: number }) {
  const d = e.derivation as { formula?: string; inputs?: string[]; result?: unknown; values?: Record<string, unknown> }
  return (
    <div className="space-y-2 rounded-md border-l-calc bg-violet-50/40 px-3 py-2 text-sm">
      {d.formula && <p>{d.formula}</p>}
      {d.result !== undefined && <p>Wynik: <b>{typeof d.result === 'number' ? d.result.toLocaleString('pl-PL') : String(d.result)}</b></p>}
      {d.inputs && d.inputs.length > 0 && depth < 2 && (
        <details className="text-xs" open={depth === 0}>
          <summary className="cursor-pointer text-slate-600">Dane wejściowe obliczenia ({d.inputs.length}) – kliknij, aby zobaczyć źródło każdej</summary>
          <div className="mt-2"><EvidenceList ids={d.inputs} depth={depth + 1} /></div>
        </details>)}
    </div>
  )
}
