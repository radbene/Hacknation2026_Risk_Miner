import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import * as pdfjs from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { Button, ErrorState, Input, Loading } from '@/components/ui'
import { normalise } from '@/lib/highlight'

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

type Doc = Awaited<ReturnType<typeof pdfjs.getDocument>['promise']>
interface TextItem { str: string; transform: number[]; width: number; height: number }

/** PDF.js viewer: page navigation, zoom, and the quote highlighted on the page (text-layer match). */
/** searchAll: look for the quote on every page and open the first page that contains it.
 *  onError: called when the PDF cannot be loaded (e.g. the source is offline) – the caller shows a fallback. */
export function PdfViewer({ url, page: initialPage = 1, quote, searchAll, onError, height = 'h-[72vh]' }:
  { url: string; page?: number; quote?: string; searchAll?: boolean; onError?: (e: unknown) => void; height?: string }) {
  const [doc, setDoc] = useState<Doc | null>(null)
  const [err, setErr] = useState<unknown>(null)
  const [page, setPage] = useState(initialPage)
  const [scale, setScale] = useState(1.2)
  const [boxes, setBoxes] = useState<{ x: number; y: number; w: number; h: number }[]>([])
  const [found, setFound] = useState<boolean | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  useEffect(() => { setPage(initialPage) }, [initialPage])
  useEffect(() => {
    let cancelled = false
    setDoc(null); setErr(null)
    const task = pdfjs.getDocument({ url })
    task.promise.then(async (d) => {
      if (cancelled) return
      if (searchAll && quote) {
        const needle = normalise(quote).toLowerCase()
        for (let i = 1; i <= d.numPages; i++) {
          const tc = await (await d.getPage(i)).getTextContent()
          const txt = (tc.items as unknown as TextItem[]).map((it) => normalise(it.str)).join(' ').toLowerCase().replace(/\s+/g, ' ')
          if (txt.includes(needle)) { if (!cancelled) setPage(i); break }
        }
      }
      if (!cancelled) setDoc(d)
    }, (e) => { if (!cancelled) { setErr(e); onError?.(e) } })
    return () => { cancelled = true; task.destroy() }
  }, [url]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!doc || !canvasRef.current) return
    let cancelled = false
    let renderTask: { cancel: () => void; promise: Promise<unknown> } | null = null
    ;(async () => {
      const p = await doc.getPage(Math.min(Math.max(1, page), doc.numPages))
      const viewport = p.getViewport({ scale })
      const canvas = canvasRef.current!
      const ratio = window.devicePixelRatio || 1
      canvas.width = viewport.width * ratio; canvas.height = viewport.height * ratio
      canvas.style.width = `${viewport.width}px`; canvas.style.height = `${viewport.height}px`
      const ctx = canvas.getContext('2d')!
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      const rt = p.render({ canvas, canvasContext: ctx, viewport } as never) as unknown as { cancel: () => void; promise: Promise<unknown> }
      renderTask = rt
      await rt.promise.catch(() => {})
      if (cancelled) return
      if (!quote) { setBoxes([]); setFound(null); return }
      const tc = await p.getTextContent()
      const items = (tc.items as unknown as TextItem[]).filter((i) => typeof i.str === 'string')
      // concatenate items, remember char → item index
      let joined = ''
      const owner: number[] = []
      items.forEach((it, idx) => { const s = normalise(it.str) + ' '; joined += s; for (let k = 0; k < s.length; k++) owner.push(idx) })
      const hay = joined.toLowerCase().replace(/\s+/g, ' ')
      const needle = normalise(quote).toLowerCase()
      const at = hay.indexOf(needle)
      if (at < 0) { setBoxes([]); setFound(false); return }
      const hit = new Set(owner.slice(at, at + needle.length))
      const bs = Array.from(hit).map((i) => {
        const it = items[i]
        const t = pdfjs.Util.transform(viewport.transform, it.transform)
        const h = Math.hypot(t[2], t[3]) || it.height * scale
        return { x: t[4], y: t[5] - h, w: it.width * scale, h: h * 1.15 }
      })
      setBoxes(bs); setFound(true)
      requestAnimationFrame(() => wrapRef.current?.querySelector('[data-hl]')?.scrollIntoView({ block: 'center', behavior: 'smooth' }))
    })()
    return () => { cancelled = true; renderTask?.cancel() }
  }, [doc, page, scale, quote])

  if (err) return onError ? null : <ErrorState error={err} />
  if (!doc) return <Loading label="Wczytywanie PDF…" />
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Button size="icon" variant="outline" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} aria-label="Poprzednia strona"><ChevronLeft size={14} /></Button>
        <label className="flex items-center gap-1">Strona
          <Input type="number" min={1} max={doc.numPages} value={page} onChange={(e) => setPage(Number(e.target.value) || 1)} className="h-8 w-16" aria-label="Numer strony" /> / {doc.numPages}</label>
        <Button size="icon" variant="outline" onClick={() => setPage((p) => Math.min(doc.numPages, p + 1))} disabled={page >= doc.numPages} aria-label="Następna strona"><ChevronRight size={14} /></Button>
        <Button size="icon" variant="outline" onClick={() => setScale((s) => Math.max(0.6, s - 0.2))} aria-label="Pomniejsz"><ZoomOut size={14} /></Button>
        <Button size="icon" variant="outline" onClick={() => setScale((s) => Math.min(2.5, s + 0.2))} aria-label="Powiększ"><ZoomIn size={14} /></Button>
        {quote && found === true && <span className="text-xs text-emerald-700">Cytat znaleziony na stronie {page}.</span>}
        {quote && found === false && <span className="text-xs text-amber-700">Cytatu nie znaleziono na tej stronie.</span>}
        <a href={url} target="_blank" rel="noreferrer" className="ml-auto text-xs text-brand hover:underline">Pobierz plik</a>
      </div>
      <div ref={wrapRef} className={`${height} overflow-auto rounded border border-slate-200 bg-slate-100 p-2`}>
        <div className="relative mx-auto w-fit bg-white shadow">
          <canvas ref={canvasRef} aria-label={`Strona ${page} dokumentu`} />
          {boxes.map((b, i) => <div key={i} data-hl className="pointer-events-none absolute rounded-sm bg-yellow-300/50 ring-1 ring-yellow-500"
            style={{ left: b.x, top: b.y, width: b.w, height: b.h }} />)}
        </div>
      </div>
    </div>
  )
}
