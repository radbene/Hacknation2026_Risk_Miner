import { ExternalLink } from 'lucide-react'
import { useEffect, useState } from 'react'
import { rawFetch } from '@/api/client'
import { useDocument } from '@/api/cases'
import { PdfViewer } from '@/components/evidence/PdfViewer'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Card, CardContent, Loading, QueryState } from '@/components/ui'
import { MOCK_DOC_FILES } from '@/mocks'
import { documentRoute } from '@/router'

/** Resolves the file URL: backend /api/documents/{id}/file, or the bundled mock file. */
export function useDocumentFileUrl(id: string) {
  const [url, setUrl] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    const api = `/api/documents/${id}/file`
    rawFetch(api, { method: 'HEAD' }).then(() => !cancelled && setUrl(api)).catch(() => !cancelled && setUrl(MOCK_DOC_FILES[id] ?? api))
    return () => { cancelled = true }
  }, [id])
  return url
}

export function DocumentViewer({ documentId, page, quote }: { documentId: string; page?: number; quote?: string }) {
  const q = useDocument(documentId)
  const url = useDocumentFileUrl(documentId)
  return (
    <QueryState q={q}>{(d) => (
      <Card>
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-4 py-2 text-sm">
          <span className="font-medium">{d.title ?? d.file_name}</span>
          {d.doc_type && <Badge variant="brand">{d.doc_type}</Badge>}
          {d.phase && <Badge>{d.phase}</Badge>}
          <span className="text-xs text-slate-500">{d.pages ?? '?'} str.</span>
          {d.url && <a href={d.url} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-xs text-brand hover:underline">Źródło <ExternalLink size={11} /></a>}
        </div>
        <CardContent>
          {!url ? <Loading /> : d.mime?.includes('pdf') || url.endsWith('.pdf') ? <PdfViewer url={url} page={page ?? 1} quote={quote} />
            : <p className="text-sm text-slate-600">Podgląd dostępny dla PDF. <a className="text-brand hover:underline" href={url}>Pobierz plik</a></p>}
        </CardContent>
      </Card>
    )}</QueryState>
  )
}

export default function DocumentPage() {
  const { documentId } = documentRoute.useParams()
  const { page, quote } = documentRoute.useSearch()
  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title="Dokument" back description={quote ? `Cytat: „${quote}”` : undefined} />
      <DocumentViewer documentId={documentId} page={page} quote={quote} />
    </div>
  )
}
