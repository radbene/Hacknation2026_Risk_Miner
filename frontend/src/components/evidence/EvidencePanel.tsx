import { Link } from '@tanstack/react-router'
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
interface SheetCtx { type: 'sheet'; file: string; sheet?: string; row: number; column?: string; header?: string; headers: string[]; rows: { row: number; values: unknown[] }[]; project_code?: string }

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
    return `${t} ${l.notice_number ?? ''}${where ? `, ${where}` : ''}`
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
  if (!ids.length) return <Empty>Brak źródła.</Empty>
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

export function SourcePreview({ e, depth = 0, full }: { e: Ev; depth?: number; full?: boolean }) {
  const height = full ? 'h-[calc(100vh-12rem)]' : 'h-[68vh]'
  return (
    <div className="min-w-0 space-y-2">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="flex items-center gap-2 font-medium"><Icon e={e} />{sourceTitle(e)}</span>
        {e.retrieved_at && <span className="text-xs text-slate-500">pobrano {fmtDate(e.retrieved_at)}</span>}
        {e.url && <a href={e.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-brand hover:underline">strona w e-Zamówieniach<ExternalLink size={10} aria-hidden /></a>}
        {!full && depth === 0 && <Link to="/zrodlo/$evidenceId" params={{ evidenceId: e.id }} target="_blank" className="ml-auto text-xs text-brand hover:underline">Otwórz na pełnym ekranie</Link>}
      </div>
      {e.derivation ? <Calculation e={e} depth={depth} />
        : e.kind === 'xlsx_cell' ? <SheetFile e={e} height={height} />
        : e.document_id ? <DocumentPreview e={e} height={height} />
        : e.notice_id ? <NoticeOriginal e={e} height={height} />
        : e.quote ? <blockquote className="rounded bg-slate-50 px-3 py-2 text-sm">{highlight(e.quote, [e.quote])}</blockquote> : null}
    </div>
  )
}

/** The notice as published: the official PDF from e-Zamówienia with the quote highlighted; offline → the sections. */
function NoticeOriginal({ e, height }: { e: Ev; height: string }) {
  const [failed, setFailed] = useState(false)
  const quote = e.quote ?? undefined
  if (failed) return (
    <div className="space-y-1">
      <p className="text-xs text-amber-800">Nie udało się pobrać pliku PDF z e-Zamówień. Poniżej treść ogłoszenia zapisana w systemie.</p>
      <NoticeView noticeId={e.notice_id!} section={(e.locator?.section as string) || undefined} quote={quote} />
    </div>)
  return <PdfViewer url={`/api/notices/${e.notice_id}/pdf`} quote={quote} searchAll onError={() => setFailed(true)} height={height} />
}

const colName = (i: number) => { let n = i + 1, s = ''; while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26) } return s }

/** The spreadsheet as imported: every row and column, the cited cell marked and scrolled into view. */
function SheetFile({ e, height }: { e: Ev; height: string }) {
  const q = useApi<SheetCtx>(['evidence-context', e.id], async () => (await (await fetch(`/api/evidence/${e.id}/context`)).json()) as SheetCtx)
  if (q.isLoading) return <Loading />
  const d = q.data
  if (!d || d.type !== 'sheet') return null
  const col = d.headers.indexOf(d.header ?? '')
  return (
    <div className="rounded-md border border-slate-300 bg-white">
      <div className="border-b border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-600">{d.file}, arkusz „{d.sheet}”, komórka {d.column}{d.row}</div>
      <div className={`${height} overflow-auto`}>
        <table className="border-collapse text-xs">
          <thead className="sticky top-0 z-10 bg-slate-100 text-slate-500">
            <tr><th className="sticky left-0 z-20 border border-slate-300 bg-slate-100 px-2" />{d.headers.map((_, i) => (
              <th key={i} className={cn('border border-slate-300 px-2 py-0.5 font-normal', i === col && 'bg-yellow-200 text-slate-900')}>{colName(i)}</th>))}</tr>
          </thead>
          <tbody>
            <tr><td className="sticky left-0 z-10 border border-slate-300 bg-slate-100 px-2 text-center text-slate-500">1</td>{d.headers.map((h, i) => (
              <td key={i} className="max-w-56 border border-slate-300 px-2 py-1 font-semibold">{h}</td>))}</tr>
            {d.rows.map((r) => (
              <tr key={r.row}>
                <td className={cn('sticky left-0 z-10 border border-slate-300 bg-slate-100 px-2 text-center text-slate-500', r.row === d.row && 'bg-yellow-200 text-slate-900')}>{r.row}</td>
                {r.values.map((v, i) => {
                  const hit = r.row === d.row && i === col
                  return <td key={i} ref={hit ? (el) => el?.scrollIntoView({ block: 'center', inline: 'center' }) : undefined}
                    className={cn('max-w-56 truncate border border-slate-300 px-2 py-1', hit ? 'bg-yellow-200 font-semibold outline-2 outline-yellow-500' : r.row === d.row ? 'bg-yellow-50' : '')}
                    title={v == null ? '' : String(v)}>{v == null ? '' : String(v)}</td>
                })}
              </tr>))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function DocumentPreview({ e, height }: { e: Ev; height: string }) {
  const doc = useApi(['document', e.document_id], async () => unwrap(await api.GET('/api/documents/{document_id}', { params: { path: { document_id: e.document_id! } } })))
  const chunks = useApi(['document', e.document_id, 'chunks'], async () => unwrap(await api.GET('/api/documents/{document_id}/chunks', { params: { path: { document_id: e.document_id! } } })))
  if (doc.isLoading) return <Loading />
  const d = doc.data
  const page = (e.locator?.page as number | undefined) ?? 1
  if (d?.mime?.includes('pdf') || d?.file_name?.toLowerCase().endsWith('.pdf')) {
    return <PdfViewer url={`/api/documents/${e.document_id}/file`} page={page} quote={e.quote ?? undefined} searchAll={e.locator?.page == null} height={height} />
  }
  const cs = (chunks.data ?? []).filter((c) => c.page == null || c.page === page)
  return (
    <div className={`${height} space-y-1 overflow-auto rounded-md border border-slate-200 bg-white p-3 text-sm`}>
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
          <summary className="cursor-pointer text-slate-600">Dane wejściowe ({d.inputs.length})</summary>
          <div className="mt-2"><EvidenceList ids={d.inputs} depth={depth + 1} /></div>
        </details>)}
    </div>
  )
}
