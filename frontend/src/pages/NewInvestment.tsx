import { useNavigate } from '@tanstack/react-router'
import { FileUp } from 'lucide-react'
import { useRef, useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApiMutation } from '@/api/hooks'
import { FeaturesForm, type Features } from '@/components/analysis/FeaturesForm'
import { Intro } from '@/components/Explain'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, Input, Label, Textarea, useToast } from '@/components/ui'

const EXAMPLE = `Gmina planuje budowę sieci kanalizacji sanitarnej o długości ok. 6,5 km wraz z 3 przepompowniami ścieków i 120 przykanalikami.
Trasa przebiega w pasie dróg gminnych i powiatowej oraz przez działki prywatne. Formuła: zaprojektuj i wybuduj (PFU).
Szacunkowa wartość: 9 800 000 zł brutto. Planowany okres realizacji: 18 miesięcy, start II kwartał 2027. Finansowanie: FEnIKS.`

export default function NewInvestment() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [docs, setDocs] = useState<Schemas['DocumentOut'][]>([])
  const [fx, setFx] = useState<Schemas['FeatureExtractOut'] | null>(null)
  const [features, setFeatures] = useState<Features | null>(null)
  const [busy, setBusy] = useState(false)
  const ref = useRef<HTMLInputElement>(null)

  const extract = useApiMutation<Schemas['FeatureExtractIn'], Schemas['FeatureExtractOut']>({
    fn: async (body) => unwrap(await api.POST('/api/analyses/extract-features', { body })),
    onSuccess: (r) => { setFx(r); setFeatures(r.features) },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się odczytać cech', description: String(e) }),
  })
  const create = useApiMutation<Schemas['AnalysisCreateIn'], Schemas['AnalysisOut']>({
    fn: async (body) => unwrap(await api.POST('/api/analyses', { body })),
    invalidate: [['analyses']],
    onSuccess: (a) => navigate({ to: '/analizy/$analysisId', params: { analysisId: a.id }, search: {} }),
    onError: (e) => toast({ kind: 'error', title: 'Analiza nie powiodła się', description: String(e) }),
  })

  async function upload(f: File) {
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', f)
      const headers: Record<string, string> = {}
      const token = localStorage.getItem('rm_token'); if (token) headers.Authorization = `Bearer ${token}`
      const r = await fetch('/api/documents', { method: 'POST', body: fd, headers })
      if (!r.ok) throw new Error(await r.text())
      const d = (await r.json()) as Schemas['DocumentOut']
      setDocs((x) => [...x, d])
      if (!title) setTitle(d.title ?? f.name)
    } catch (e) { toast({ kind: 'error', title: 'Nie udało się wczytać dokumentu', description: String(e) }) } finally {
      setBusy(false); if (ref.current) ref.current.value = ''
    }
  }
  const docIds = docs.map((d) => d.id)
  const canExtract = text.trim().length > 20 || docIds.length > 0

  return (
    <div>
      <PageHeader title="Nowa analiza" />
      <Intro can={['wkleić opis albo wgrać dokument (PDF, Word)', 'poprawić odczytane cechy', 'zapisać analizę w „Moich analizach”']}>
        Opisz planowaną inwestycję wodno-kanalizacyjną: zakres i skalę, lokalizację, wartość netto lub brutto, czas realizacji, formułę oraz stan przygotowania terenu, decyzji i uzgodnień. Odczytanie cech trwa 1–2 minuty, bo opis czyta model językowy na naszym serwerze.
      </Intro>
      <div className="grid gap-4 xl:grid-cols-[1fr_1.2fr]">
        <Card>
          <CardHeader title="1. Opis inwestycji" />
          <CardContent className="space-y-3">
            <div><Label htmlFor="ni-t">Nazwa analizy</Label><Input id="ni-t" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="np. Kanalizacja sanitarna, Gmina X" /></div>
            <div><Label htmlFor="ni-x">Opis</Label><Textarea id="ni-x" rows={12} value={text} onChange={(e) => setText(e.target.value)} placeholder="Zakres, skala (km, RLM, m³/d), lokalizacja, wartość (netto/brutto), czas realizacji, formuła, stan przygotowania (grunty, decyzje)…" />
              <button className="mt-1 text-xs text-brand hover:underline cursor-pointer" onClick={() => { setText(EXAMPLE); if (!title) setTitle('Przykład: kanalizacja sanitarna') }}>Wstaw przykładowy opis</button></div>
            <div className="flex flex-wrap items-center gap-2">
              <input ref={ref} type="file" className="hidden" accept=".pdf,.docx,.txt,.html" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} aria-label="Dokument inwestycji" />
              <Button variant="outline" loading={busy} onClick={() => ref.current?.click()}><FileUp size={14} />Wgraj dokument</Button>
              {docs.map((d) => <Badge key={d.id} variant="info">{d.file_name}</Badge>)}
            </div>
            <Button disabled={!canExtract} loading={extract.isPending} onClick={() => extract.mutate({ text: text || null, document_ids: docIds })}>
              Odczytaj cechy</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader title="2. Sprawdź odczytane cechy"
            actions={fx?.model_label ? <Badge variant="violet">uzupełnił: {fx.model_label.replace(/\s*\(.*\)$/, '')}</Badge> : undefined} />
          <CardContent className="space-y-3">
            {!features && <p className="text-sm text-slate-500">Najpierw odczytaj cechy z opisu.</p>}
            {fx && (fx.questions ?? []).length > 0 && (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-sm">
                <div className="mb-1 font-medium text-amber-900">Pytania do uzupełnienia</div>
                <ul className="list-disc pl-5 text-xs text-amber-900">{(fx.questions ?? []).map((q, i) => <li key={i}>{q}</li>)}</ul>
              </div>)}
            {features && <FeaturesForm value={features} onChange={setFeatures} />}
            {features && (
              <Button size="lg" loading={create.isPending} disabled={!title.trim()}
                onClick={() => create.mutate({ title, text: text || null, document_ids: docIds, features, params: {}, project_id: null })}>
                Analizuj ryzyko</Button>)}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
