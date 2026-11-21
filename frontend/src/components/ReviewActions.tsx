import { Check, GitCompareArrows, Link2, PencilLine, RotateCcw, Star, X } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApiMutation } from '@/api/hooks'
import { Button, Dialog, Input, Label, Select, Textarea, useToast } from '@/components/ui'
import { ACTION_LABEL } from '@/lib/labels'
import { mockReview } from '@/mocks'

type ObjectType = Schemas['QueueItem']['object_type']
type Action = Schemas['ReviewActionIn']['action']

export interface EditField { key: string; label: string; type?: 'text' | 'longtext' | 'number' | 'rcodes' | 'date' | 'enum'; options?: string[] }

/** Accept / edit / reject / relink / exemplary with comment + confirmation. Calls POST /api/review/{type}/{id}. */
export function ReviewActions({ objectType, objectId, status, exemplary, proposal, editFields, values, onRelink, invalidate = [], size = 'sm', compact }: {
  objectType: ObjectType; objectId: string; status?: string | null; exemplary?: boolean; proposal?: Record<string, unknown> | null
  editFields?: EditField[]; values?: Record<string, unknown>; onRelink?: () => void; invalidate?: unknown[][]; size?: 'sm' | 'md'; compact?: boolean
}) {
  const { toast } = useToast()
  const [dlg, setDlg] = useState<null | Action | 'proposal'>(null)
  const [comment, setComment] = useState('')
  const [edits, setEdits] = useState<Record<string, unknown>>({})

  const m = useApiMutation<Schemas['ReviewActionIn'], Schemas['ReviewOut']>({
    fn: async (body) => unwrap(await api.POST('/api/review/{object_type}/{object_id}', { params: { path: { object_type: objectType, object_id: objectId } }, body })),
    mock: (body) => mockReview(objectType, objectId, body),
    invalidate: [['review'], ['history'], ['projects'], ['project'], ['events'], ['links'], ['analysis'], ...invalidate],
    onSuccess: (r) => { toast({ kind: 'success', title: `Zapisano: ${ACTION_LABEL[r.action] ?? r.action}`, description: r.comment ?? undefined }); close() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zapisać decyzji', description: String(e) }),
  })

  type Body = Omit<Schemas['ReviewActionIn'], 'accept_proposal'> & { accept_proposal?: boolean }
  const send = (b: Body) => m.mutate({ accept_proposal: false, ...b })

  function open(a: Action | 'proposal') {
    setComment('')
    setEdits(Object.fromEntries((editFields ?? []).map((f) => [f.key, values?.[f.key] ?? ''])))
    setDlg(a)
  }
  function close() { setDlg(null) }
  function submit() {
    if (dlg === 'proposal') return send({ action: 'accept', accept_proposal: true, comment: comment || null })
    if (!dlg) return
    const changes = dlg === 'edit' ? normaliseEdits(edits, editFields ?? []) : null
    send({ action: dlg, changes, comment: comment || null })
  }

  const decided = status === 'approved' || status === 'edited' || status === 'rejected'
  return (
    <div className="flex flex-wrap items-center gap-1" onClick={(e) => e.stopPropagation()}>
      {!decided && <Button size={size} variant="success" onClick={() => send({ action: 'accept', comment: null })} loading={m.isPending && !dlg}
        aria-label="Akceptuj"><Check size={13} />{!compact && 'Akceptuj'}</Button>}
      {editFields && editFields.length > 0 && <Button size={size} variant="outline" onClick={() => open('edit')} aria-label="Popraw"><PencilLine size={13} />{!compact && 'Popraw'}</Button>}
      {!decided && <Button size={size} variant="outline" className="text-rose-700" onClick={() => open('reject')} aria-label="Odrzuć"><X size={13} />{!compact && 'Odrzuć'}</Button>}
      {onRelink && <Button size={size} variant="outline" onClick={onRelink} aria-label="Powiąż ponownie"><Link2 size={13} />{!compact && 'Powiąż ponownie'}</Button>}
      {proposal && <Button size={size} variant="outline" className="text-sky-700" onClick={() => open('proposal')}><GitCompareArrows size={13} />Propozycja z ponownej analizy</Button>}
      <Button size={size} variant="ghost" onClick={() => send({ action: exemplary ? 'unexemplary' : 'exemplary', comment: null })}
        aria-pressed={!!exemplary} title={exemplary ? 'Zdejmij oznaczenie wzorcowe' : 'Oznacz jako wzorcowe (few-shot)'}>
        <Star size={13} className={exemplary ? 'fill-amber-400 text-amber-500' : ''} />{!compact && (exemplary ? 'Wzorcowe' : 'Wzorcowe?')}
      </Button>
      {decided && <Button size={size} variant="ghost" onClick={() => open('reopen')} title="Otwórz ponownie"><RotateCcw size={13} />{!compact && 'Otwórz'}</Button>}

      <Dialog open={dlg !== null} onClose={close}
        title={dlg === 'reject' ? 'Odrzucić?' : dlg === 'edit' ? 'Popraw wartości' : dlg === 'proposal' ? 'Przyjąć propozycję z ponownej analizy?' : 'Otworzyć ponownie?'}
        description="Decyzja trafia do historii zmian (kto, kiedy, przed/po, komentarz)."
        footer={<><Button variant="outline" onClick={close}>Anuluj</Button>
          <Button variant={dlg === 'reject' ? 'danger' : 'default'} onClick={submit} loading={m.isPending}
            disabled={dlg === 'reject' && !comment.trim()}>{dlg === 'reject' ? 'Odrzuć' : 'Zapisz'}</Button></>}>
        {dlg === 'edit' && (
          <div className="mb-3 grid gap-3">
            {(editFields ?? []).map((f) => (
              <div key={f.key}>
                <Label htmlFor={`ef-${f.key}`}>{f.label}</Label>
                {f.type === 'longtext' ? <Textarea id={`ef-${f.key}`} value={String(edits[f.key] ?? '')} onChange={(e) => setEdits({ ...edits, [f.key]: e.target.value })} />
                  : f.type === 'enum' ? <Select id={`ef-${f.key}`} value={String(edits[f.key] ?? '')} options={(f.options ?? []).map((o) => ({ value: o, label: o }))} placeholder="—"
                    onChange={(e) => setEdits({ ...edits, [f.key]: e.target.value })} />
                  : <Input id={`ef-${f.key}`} type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'}
                    value={Array.isArray(edits[f.key]) ? (edits[f.key] as string[]).join(', ') : String(edits[f.key] ?? '')}
                    placeholder={f.type === 'rcodes' ? 'np. R02, R03' : undefined} onChange={(e) => setEdits({ ...edits, [f.key]: e.target.value })} />}
              </div>
            ))}
          </div>
        )}
        {dlg === 'proposal' && proposal && <ProposalDiff current={values ?? {}} proposal={proposal} />}
        <Label htmlFor="rv-comment">Komentarz {dlg === 'reject' ? '(wymagany)' : '(opcjonalny)'}</Label>
        <Textarea id="rv-comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Uzasadnienie decyzji eksperta" />
      </Dialog>
    </div>
  )
}

function normaliseEdits(edits: Record<string, unknown>, fields: EditField[]) {
  const out: Record<string, unknown> = {}
  for (const f of fields) {
    const v = edits[f.key]
    if (f.type === 'number') out[f.key] = v === '' || v == null ? null : Number(v)
    else if (f.type === 'rcodes') out[f.key] = Array.isArray(v) ? v : String(v ?? '').split(/[,\s]+/).map((s) => s.trim().toUpperCase()).filter(Boolean)
    else out[f.key] = v
  }
  return out
}

/** Side-by-side diff of current values vs a rerun proposal (keys starting with "_" are metadata). */
export function ProposalDiff({ current, proposal }: { current: Record<string, unknown>; proposal: Record<string, unknown> }) {
  const keys = Object.keys(proposal).filter((k) => !k.startsWith('_'))
  const fmt = (v: unknown) => (v == null ? '—' : Array.isArray(v) ? v.join(', ') : typeof v === 'object' ? JSON.stringify(v) : String(v))
  return (
    <div className="mb-3 overflow-x-auto rounded border border-slate-200">
      <table className="w-full text-xs">
        <thead className="bg-slate-50 text-left"><tr><th className="px-2 py-1">Pole</th><th className="px-2 py-1">Obecnie (decyzja eksperta)</th><th className="px-2 py-1">Propozycja</th></tr></thead>
        <tbody>
          {keys.map((k) => {
            const changed = fmt(current[k]) !== fmt(proposal[k])
            return (
              <tr key={k} className="border-t border-slate-100">
                <td className="px-2 py-1 font-medium">{k}</td>
                <td className={changed ? 'bg-rose-50 px-2 py-1 line-through decoration-rose-400' : 'px-2 py-1'}>{fmt(current[k])}</td>
                <td className={changed ? 'bg-emerald-50 px-2 py-1' : 'px-2 py-1'}>{fmt(proposal[k])}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {'_rerun_at' in proposal && <p className="px-2 py-1 text-[11px] text-slate-500">Ponowna analiza: {String(proposal._rerun_at)}. Decyzja eksperta nie została nadpisana.</p>}
    </div>
  )
}
