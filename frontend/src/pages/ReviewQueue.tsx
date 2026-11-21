import { Link, useNavigate } from '@tanstack/react-router'
import { CheckCheck } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { MethodConfidence } from '@/components/MethodConfidence'
import { PageHeader } from '@/components/PageHeader'
import { ReviewActions } from '@/components/ReviewActions'
import { StatusBadge } from '@/components/StatusBadge'
import { Badge, Button, Card, Dialog, Label, QueryState, Select, Tabs, Textarea, useToast } from '@/components/ui'
import { OBJECT_TYPE_LABEL } from '@/lib/labels'
import { fmtDateTime } from '@/lib/utils'
import { queueRoute } from '@/router'

type Q = Schemas['QueueItem']
type ObjType = Q['object_type']
const TYPES: ObjType[] = ['project_procedure', 'event', 'data_issue', 'contract_change', 'project', 'document', 'lesson', 'clause', 'risk_category', 'analysis_item']

export default function ReviewQueue() {
  const s = queueRoute.useSearch()
  const navigate = useNavigate({ from: '/kolejka' })
  const type = (s.type ?? 'project_procedure') as ObjType
  const status = s.status ?? 'proposed'
  const counts = useApi(['review', 'counts'], async () => unwrap(await api.GET('/api/review/counts')))
  const q = useApi(['review', 'queue', type, status, s.project ?? ''], async () => unwrap(await api.GET('/api/review/queue', {
    params: { query: { object_type: type, status, project_id: s.project ?? null, limit: 200 } },
  })))
  const [bulk, setBulk] = useState(false)
  const tabs = TYPES.map((t) => ({ value: t, label: OBJECT_TYPE_LABEL[t] ?? t, count: counts.data?.[t] }))

  return (
    <div>
      <PageHeader title="Kolejka eksperta"
        description="Wszystko, co zaproponował system (powiązania, zdarzenia, przyczyny, braki danych, elementy analiz), czeka tutaj na decyzję. Najpierw pozycje najmniej pewne. Decyzje eksperta nie są nadpisywane przy ponownym przeliczeniu – system zapisuje wtedy tylko propozycję zmiany."
        actions={<Button variant="success" onClick={() => setBulk(true)}><CheckCheck size={14} />Zatwierdź hurtowo</Button>} />
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Select aria-label="Status" value={status} onChange={(e) => navigate({ search: { ...s, status: e.target.value }, replace: true })} className="w-48"
          options={[{ value: 'proposed', label: 'Do decyzji' }, { value: 'approved', label: 'Zatwierdzone' }, { value: 'edited', label: 'Poprawione' },
            { value: 'rejected', label: 'Odrzucone' }, { value: 'all', label: 'Wszystkie' }]} />
        {s.project && <Badge variant="info">filtr: jeden projekt <button className="ml-1 cursor-pointer" onClick={() => navigate({ search: { ...s, project: undefined } })}>×</button></Badge>}
      </div>
      <Tabs value={type} onChange={(t) => navigate({ search: { ...s, type: t }, replace: true })} tabs={tabs}>
        <QueryState q={q} empty={(d) => d.items.length === 0}>{(d) => (
          <div className="space-y-2">
            <p className="text-xs text-slate-500">{d.total} pozycji</p>
            {d.items.map((it) => <QueueRow key={it.object_id} it={it} />)}
          </div>
        )}</QueryState>
      </Tabs>
      <BulkDialog open={bulk} onClose={() => setBulk(false)} type={type} />
    </div>
  )
}

function QueueRow({ it }: { it: Q }) {
  return (
    <Card className="p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
            {it.project_code && it.project_id && (
              <Link to="/projekty/$projectId" params={{ projectId: it.project_id }} search={{}} className="font-mono text-xs text-brand hover:underline">{it.project_code}</Link>)}
            <span>{it.title}</span>
            {it.has_proposal && <Badge variant="info" title="Ponowne przeliczenie dało inny wynik niż decyzja eksperta">propozycja zmiany</Badge>}
          </div>
          {it.summary && <p className="mt-1 line-clamp-3 text-xs text-slate-600">{it.summary}</p>}
          <div className="mt-1 text-[11px] text-slate-400">{fmtDateTime(it.created_at)}</div>
        </div>
        <div className="flex items-center gap-2">
          <MethodConfidence method={it.method} confidence={it.confidence} />
          <EvidenceChip ids={it.evidence_ids} />
          <StatusBadge status={it.status} />
        </div>
      </div>
      <div className="mt-2"><ReviewActions objectType={it.object_type} objectId={it.object_id} status={it.status}
        invalidate={[['review']]} /></div>
    </Card>
  )
}

function BulkDialog({ open, onClose, type }: { open: boolean; onClose: () => void; type: ObjType }) {
  const { toast } = useToast()
  const [minConf, setMinConf] = useState('1')
  const [method, setMethod] = useState('')
  const [comment, setComment] = useState('Zatwierdzenie hurtowe – dopasowanie po kluczu')
  const m = useApiMutation<Schemas['BulkConfirmIn'], Schemas['BulkResult']>({
    fn: async (body) => unwrap(await api.POST('/api/review/bulk-confirm', { body })),
    invalidate: [['review'], ['projects'], ['links'], ['events'], ['history']],
    onSuccess: (r) => { toast({ kind: 'success', title: `Zatwierdzono ${r.confirmed}`, description: `Pominięto ${r.skipped} (poniżej progu lub już rozstrzygnięte).` }); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title={`Zatwierdź hurtowo: ${OBJECT_TYPE_LABEL[type] ?? type}`}
      description="Zatwierdza tylko propozycje o pewności co najmniej podanej (np. powiązania po numerze KPO / ogłoszenia = 1,0). Każda decyzja trafia do historii."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button>
        <Button variant="success" loading={m.isPending} onClick={() => m.mutate({ object_type: type, min_confidence: Number(minConf), method: method || null, comment, ids: null, project_id: null })}>Zatwierdź</Button></>}>
      <div className="space-y-3 text-sm">
        <div><Label htmlFor="b-c">Minimalna pewność</Label>
          <Select id="b-c" value={minConf} onChange={(e) => setMinConf(e.target.value)} options={['1', '0.95', '0.9', '0.8'].map((v) => ({ value: v, label: v.replace('.', ',') }))} /></div>
        {type === 'project_procedure' && <div><Label htmlFor="b-m">Metoda</Label>
          <Select id="b-m" value={method} onChange={(e) => setMethod(e.target.value)} placeholder="każda"
            options={[{ value: 'kpo_ref', label: 'numer KPO' }, { value: 'notice_no', label: 'numer ogłoszenia' }, { value: 'xref', label: 'łańcuch ogłoszeń' }, { value: 'fuzzy', label: 'dopasowanie rozmyte' }]} /></div>}
        <div><Label htmlFor="b-k">Komentarz</Label><Textarea id="b-k" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} /></div>
      </div>
    </Dialog>
  )
}
