import { useNavigate } from '@tanstack/react-router'
import { History, Plus, RotateCcw, Save, Trash2, Upload } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Input, Label, QueryState, Textarea, useToast } from '@/components/ui'
import { cn, fmtDateTime } from '@/lib/utils'
import { knowledgeRoute } from '@/router'

const SECTOR = 'wodkan'
type Row = Record<string, unknown>

export default function Knowledge() {
  const s = knowledgeRoute.useSearch()
  const navigate = useNavigate({ from: '/wiedza' })
  const tables = useApi(['knowledge', SECTOR], async () => unwrap(await api.GET('/api/knowledge/{sector}/tables', { params: { path: { sector: SECTOR } } })))
  const { toast } = useToast()
  const reimport = useApiMutation<void, Schemas['KnowledgeImportReport']>({
    fn: async () => unwrap(await api.POST('/api/knowledge/{sector}/import', { params: { path: { sector: SECTOR } } })),
    invalidate: [['knowledge']],
    onSuccess: (r) => toast({ kind: 'success', title: 'Wiedza wczytana', description: `Nowe wersje: ${r.written.join(', ') || 'brak (bez zmian)'}` }),
    onError: (e) => toast({ kind: 'error', title: 'Import nie powiódł się', description: String(e) }),
  })
  return (
    <div>
      <PageHeader title="Wiedza ekspercka"
        description="Tabele wygenerowane z materiałów eksperckich MFiPR (katalog ryzyk R01–R15, podsektory, fazy, dokumenty, checklisty, art. 455) i robocze tabele zespołu (reguły, wagi podobieństwa, progi, klauzule). Każdy zapis tworzy nową wersję; starą można przywrócić. Nowy sektor = nowy katalog plików, bez zmian w kodzie."
        actions={<Button variant="outline" loading={reimport.isPending} onClick={() => reimport.mutate()}><Upload size={14} />Wczytaj ponownie z plików</Button>} />
      <QueryState q={tables} empty={(t) => t.length === 0}>{(ts) => {
        const cur = s.table ?? ts[0]?.name
        return (
          <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
            <nav aria-label="Tabele wiedzy" className="space-y-1">{ts.map((t) => (
              <button key={t.name} onClick={() => navigate({ search: { table: t.name }, replace: true })}
                className={cn('w-full rounded border px-2 py-1.5 text-left text-xs cursor-pointer', cur === t.name ? 'border-brand bg-brand-soft' : 'border-slate-200 bg-white hover:bg-slate-50')}>
                <div className="font-medium">{t.title ?? t.name}</div>
                <div className="text-slate-500">{t.name} · v{t.version} · {t.n_rows} wierszy</div>
              </button>))}</nav>
            {cur && <TableEditor key={cur} name={cur} />}
          </div>
        )
      }}</QueryState>
    </div>
  )
}

function TableEditor({ name }: { name: string }) {
  const t = useApi(['knowledge', SECTOR, name], async () => unwrap(await api.GET('/api/knowledge/{sector}/tables/{name}', { params: { path: { sector: SECTOR, name } } })))
  const [rows, setRows] = useState<Row[]>([])
  const [dirty, setDirty] = useState(false)
  const [save, setSave] = useState(false)
  const [hist, setHist] = useState(false)
  useEffect(() => { if (t.data) { setRows(t.data.rows as Row[]); setDirty(false) } }, [t.data])
  const cols = useMemo(() => {
    const declared = (t.data?.columns ?? []).map((c) => ({ key: c.key, label: c.label, type: c.type }))
    const keys = new Set(declared.map((c) => c.key))
    for (const r of rows) for (const k of Object.keys(r)) if (!keys.has(k)) { keys.add(k); declared.push({ key: k, label: k, type: 'text' }) }
    return declared
  }, [t.data, rows])
  const set = (i: number, k: string, v: unknown) => { setRows((rs) => rs.map((r, j) => (j === i ? { ...r, [k]: v } : r))); setDirty(true) }

  return (
    <QueryState q={t}>{(d) => (
      <Card>
        <CardHeader title={d.title ?? d.name}
          description={<>Wersja {d.version}{d.edited_by && ` · ${d.edited_by}`}{d.updated_at && ` · ${fmtDateTime(d.updated_at)}`}{d.source_file && ` · źródło: ${d.source_file}`}{d.comment && ` · „${d.comment}”`}</>}
          actions={<>
            {dirty && <Badge variant="warning">niezapisane zmiany</Badge>}
            <Button size="sm" variant="outline" onClick={() => setHist(true)}><History size={14} />Wersje</Button>
            <Button size="sm" variant="outline" onClick={() => { setRows((r) => [...r, {}]); setDirty(true) }}><Plus size={14} />Wiersz</Button>
            <Button size="sm" disabled={!dirty} onClick={() => setSave(true)}><Save size={14} />Zapisz nową wersję</Button>
          </>} />
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 text-left text-slate-500"><tr>{cols.map((c) => <th key={c.key} className="px-2 py-1.5 font-medium">{c.label}</th>)}<th /></tr></thead>
            <tbody>{rows.map((r, i) => (
              <tr key={i} className="border-t border-slate-100 align-top">
                {cols.map((c) => <td key={c.key} className="px-1 py-1"><Cell value={r[c.key]} onChange={(v) => set(i, c.key, v)} label={`${c.label}, wiersz ${i + 1}`} /></td>)}
                <td className="px-1 py-1"><button aria-label={`Usuń wiersz ${i + 1}`} className="cursor-pointer text-slate-400 hover:text-rose-600"
                  onClick={() => { setRows((rs) => rs.filter((_, j) => j !== i)); setDirty(true) }}><Trash2 size={14} /></button></td>
              </tr>))}</tbody>
          </table>
        </CardContent>
        <SaveDialog open={save} onClose={() => setSave(false)} name={name} rows={rows} onSaved={() => setDirty(false)} />
        <VersionsDialog open={hist} onClose={() => setHist(false)} name={name} current={d.version} />
      </Card>
    )}</QueryState>
  )
}

/** Scalars edit inline; lists as comma-separated; objects as JSON. */
function Cell({ value, onChange, label }: { value: unknown; onChange: (v: unknown) => void; label: string }) {
  if (Array.isArray(value)) {
    return <Input aria-label={label} className="h-7 min-w-40 text-xs" defaultValue={value.map(String).join(', ')}
      onBlur={(e) => onChange(e.target.value.split(',').map((x) => x.trim()).filter(Boolean))} />
  }
  if (value !== null && typeof value === 'object') {
    return <Textarea aria-label={label} className="min-w-56 font-mono text-[11px]" rows={2} defaultValue={JSON.stringify(value)}
      onBlur={(e) => { try { onChange(JSON.parse(e.target.value)) } catch { /* keep */ } }} />
  }
  const s = value == null ? '' : String(value)
  if (s.length > 60) return <Textarea aria-label={label} className="min-w-72 text-xs" rows={3} defaultValue={s} onBlur={(e) => onChange(e.target.value)} />
  return <Input aria-label={label} className="h-7 min-w-24 text-xs" defaultValue={s}
    onBlur={(e) => onChange(typeof value === 'number' && e.target.value !== '' && !Number.isNaN(Number(e.target.value)) ? Number(e.target.value) : e.target.value)} />
}

function SaveDialog({ open, onClose, name, rows, onSaved }: { open: boolean; onClose: () => void; name: string; rows: Row[]; onSaved: () => void }) {
  const [comment, setComment] = useState('')
  const { toast } = useToast()
  const m = useApiMutation<Schemas['KnowledgeTableIn'], Schemas['KnowledgeTableOut']>({
    fn: async (body) => unwrap(await api.PUT('/api/knowledge/{sector}/tables/{name}', { params: { path: { sector: SECTOR, name } }, body })),
    invalidate: [['knowledge']],
    onSuccess: (t) => { toast({ kind: 'success', title: `Zapisano wersję ${t.version}`, description: 'Nowe analizy i przeliczenia użyją tej wersji.' }); onSaved(); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zapisać', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title="Zapisz nową wersję tabeli" description="Poprzednia wersja zostaje zachowana i można ją przywrócić."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button><Button loading={m.isPending} disabled={!comment.trim()} onClick={() => m.mutate({ rows, comment, columns: null })}>Zapisz</Button></>}>
      <Label htmlFor="kc">Co i dlaczego zmieniono (wymagane)</Label>
      <Textarea id="kc" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
    </Dialog>
  )
}

function VersionsDialog({ open, onClose, name, current }: { open: boolean; onClose: () => void; name: string; current: number }) {
  const v = useApi(['knowledge', SECTOR, name, 'versions'], async () => unwrap(await api.GET('/api/knowledge/{sector}/tables/{name}/versions', { params: { path: { sector: SECTOR, name } } })),
    undefined, { enabled: open })
  const { toast } = useToast()
  const m = useApiMutation<number, Schemas['KnowledgeTableOut']>({
    fn: async (version) => unwrap(await api.POST('/api/knowledge/{sector}/tables/{name}/restore/{version}', { params: { path: { sector: SECTOR, name, version } } })),
    invalidate: [['knowledge']],
    onSuccess: (t) => { toast({ kind: 'success', title: `Przywrócono – bieżąca wersja ${t.version}` }); onClose() },
  })
  return (
    <Dialog open={open} onClose={onClose} title={`Wersje tabeli ${name}`}>
      <QueryState q={v}>{(vs) => (
        <ul className="space-y-1 text-sm">{vs.map((x) => (
          <li key={x.version} className="flex items-center justify-between gap-2 rounded border border-slate-200 p-2">
            <span>v{x.version} · {x.n_rows} wierszy · {x.edited_by ?? '—'} · {fmtDateTime(x.updated_at)}</span>
            {x.version === current ? <Badge variant="success">bieżąca</Badge>
              : <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate(x.version)}><RotateCcw size={12} />Przywróć</Button>}
          </li>))}</ul>
      )}</QueryState>
    </Dialog>
  )
}
