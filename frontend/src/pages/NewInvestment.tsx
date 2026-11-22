import { useNavigate } from '@tanstack/react-router'
import { FileUp, Plus, Trash2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { FeaturesForm, type Features } from '@/components/analysis/FeaturesForm'
import { Intro } from '@/components/Explain'
import { MiningLoader } from '@/components/MiningLoader'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Input, Label, Select, Textarea, useToast } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { HINTS, LocationNote, PROVIDERS, SERVER_URL_HINT } from '@/lib/llmModels'

const WHERE: Record<string, string> = { local: 'dane zostają na naszym serwerze', eu: 'dane przetwarzane w chmurze w UE', non_eu: 'dane przetwarzane poza UE' }

type Routing = Schemas['LLMRoutingOut']

/** The user picks which language model reads the description and writes the summary for this analysis,
 *  and can add their own model (own server or own API key). Experts set the default order. */
function ModelPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const { user, isExpert } = useAuth()
  const { toast } = useToast()
  const [adding, setAdding] = useState(false)
  const q = useApi(['settings', 'llm'], async () => unwrap(await api.GET('/api/settings/llm')))
  const r = q.data
  const models = (r?.profiles ?? []).filter((p) => p.provider !== 'none' && p.available)
  const short = (s: string) => s.replace(/\s*\(.*\)\s*$/, '') // display names carry the location in brackets; the hint shows it
  const name = (n?: string) => { const p = r?.profiles.find((x) => x.name === n); return short(p?.display_name ?? n ?? '') }
  const auto = r?.tasks?.features?.find((n) => models.some((m) => m.name === n))
  const chosen = r?.profiles.find((m) => m.name === value)
  const mine = (r?.profiles ?? []).filter((p) => p.added_by && (p.added_by === user.username || isExpert))
  const remove = useApiMutation<string, Routing>({
    fn: async (n) => unwrap(await api.DELETE('/api/settings/llm/user-models/{name}', { params: { path: { name: n } } })),
    invalidate: [['settings', 'llm']],
    onSuccess: (_r, n) => { if (n === value) onChange(''); toast({ kind: 'success', title: 'Usunięto model' }) },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się usunąć modelu', description: String(e) }),
  })
  const hint = value === 'rules'
    ? 'Bez modelu językowego cechy odczytujemy z tekstu stałymi wzorcami (np. „4,2 km”, „5 000 000 zł netto”, słowa kluczowe podsektorów). Wynik od razu, ale słabiej rozumie opis; analiza nie dostanie też podsumowania pisanego przez model.'
    : chosen ? `${WHERE[chosen.data_location] ?? chosen.data_location}.${chosen.available ? '' : ` Model jest teraz niedostępny (${chosen.unavailable_reason ?? 'brak połączenia'}).`} Jeśli model nie odpowie, użyjemy kolejnego z ustawień eksperta.`
    : auto ? `Teraz: ${name(auto)} (${WHERE[r!.profiles.find((p) => p.name === auto)!.data_location] ?? ''}). Domyślną kolejność modeli ustala ekspert.`
    : 'Żaden model nie jest teraz dostępny – cechy odczytamy stałymi wzorcami tekstu.'
  return (
    <div>
      <div className="flex items-end justify-between gap-2">
        <Label htmlFor="ni-m">Model językowy</Label>
        <button type="button" className="mb-1 inline-flex cursor-pointer items-center gap-1 text-xs text-brand hover:underline" onClick={() => setAdding(true)}>
          <Plus size={12} />Dodaj własny model</button>
      </div>
      <Select id="ni-m" value={value} onChange={(e) => onChange(e.target.value)} options={[
        { value: '', label: `Automatycznie${auto ? ` (${name(auto)})` : ''}` },
        ...models.map((m) => ({ value: m.name, label: `${name(m.name)}${m.added_by ? ' – dodany przez użytkownika' : ''}` })),
        { value: 'rules', label: 'Bez modelu językowego (stałe wzorce tekstu)' },
      ]} />
      <p className="mt-0.5 text-xs text-slate-500">{hint}</p>
      {mine.length > 0 && (
        <ul className="mt-1 space-y-0.5 text-xs text-slate-600" aria-label="Modele dodane przez użytkowników">
          {mine.map((m) => (
            <li key={m.name} className="flex items-center gap-2">
              <span>{name(m.name)}{m.available ? '' : ' (niedostępny)'} · dodał: {m.added_by}</span>
              <button type="button" className="inline-flex cursor-pointer items-center gap-0.5 text-rose-700 hover:underline" disabled={remove.isPending}
                onClick={() => remove.mutate(m.name)} aria-label={`Usuń model ${name(m.name)}`}><Trash2 size={11} />usuń</button>
            </li>))}
        </ul>)}
      <AddUserModel open={adding} onClose={() => setAdding(false)} onAdded={onChange} />
    </div>
  )
}

function AddUserModel({ open, onClose, onAdded }: { open: boolean; onClose: () => void; onAdded: (name: string) => void }) {
  const { toast } = useToast()
  const empty = { display_name: '', provider: 'openai_compatible', base_url: '', model: '', api_key: '' }
  const [f, setF] = useState(empty)
  const set = (k: keyof typeof f, v: string) => setF((x) => ({ ...x, [k]: v }))
  const m = useApiMutation<Schemas['UserModelIn'], Routing>({
    fn: async (body) => unwrap(await api.POST('/api/settings/llm/user-models', { body })),
    invalidate: [['settings', 'llm']],
    onSuccess: (r, body) => {
      const added = r.profiles.filter((p) => p.added_by && p.display_name === body.display_name.trim()).at(-1)
      if (added) onAdded(added.name)
      toast({ kind: 'success', title: 'Model dodany', description: added && !added.available ? `Na razie niedostępny: ${added.unavailable_reason}` : 'Wybrano go dla tej analizy.' })
      setF(empty); onClose()
    },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się dodać modelu', description: String(e) }),
  })
  const compat = f.provider === 'openai_compatible'
  const h = HINTS[f.provider]
  const ok = f.display_name.trim() && f.model.trim() && (compat ? f.base_url.trim() : f.api_key.trim())
  const submit = () => ok && m.mutate({ display_name: f.display_name, provider: f.provider, model: f.model,
    base_url: compat ? f.base_url.trim() : null, api_key: f.api_key.trim() || null })
  return (
    <Dialog open={open} onClose={onClose} title="Dodaj własny model językowy"
      description="Model będzie widoczny na liście wyboru przy nowej analizie. Klucz API zapisujemy na serwerze i nigdy go nie wyświetlamy; nie da się tu użyć kluczy instytucji."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button><Button loading={m.isPending} disabled={!ok} onClick={submit}>Dodaj model</Button></>}>
      <form className="space-y-3 text-sm" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div><Label htmlFor="um-p">Rodzaj</Label><Select id="um-p" value={f.provider} onChange={(e) => set('provider', e.target.value)} options={PROVIDERS} /></div>
        <div><Label htmlFor="um-n">Nazwa</Label><Input id="um-n" value={f.display_name} onChange={(e) => set('display_name', e.target.value)} placeholder={h.name} /></div>
        {compat && <div><Label htmlFor="um-u">Adres serwera</Label><Input id="um-u" value={f.base_url} onChange={(e) => set('base_url', e.target.value)}
          placeholder={SERVER_URL_HINT} />
          <p className="mt-0.5 text-xs text-slate-500">Adres API zgodnego z OpenAI, zwykle kończy się na /v1.</p></div>}
        <div><Label htmlFor="um-m">Identyfikator modelu</Label><Input id="um-m" value={f.model} onChange={(e) => set('model', e.target.value)} placeholder={h.model} />
          {h.modelHelp && <p className="mt-0.5 text-xs text-slate-500">{h.modelHelp}</p>}</div>
        <div><Label htmlFor="um-k">Klucz API{compat ? ' (jeśli serwer go wymaga)' : ''}</Label><Input id="um-k" type="password" autoComplete="off" value={f.api_key}
          onChange={(e) => set('api_key', e.target.value)} placeholder={h.key} />
          <p className="mt-0.5 text-xs text-slate-500">{h.keyHelp}</p></div>
        <LocationNote provider={f.provider} url={f.base_url} />
      </form>
    </Dialog>
  )
}

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
  const [resultId, setResultId] = useState<string | null>(null)
  const [model, setModel] = useState('')
  const ref = useRef<HTMLInputElement>(null)

  const extract = useApiMutation<Schemas['FeatureExtractIn'], Schemas['FeatureExtractOut']>({
    fn: async (body) => unwrap(await api.POST('/api/analyses/extract-features', { body })),
    onSuccess: (r) => { setFx(r); setFeatures(r.features) },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się odczytać cech', description: String(e) }),
  })
  const create = useApiMutation<Schemas['AnalysisCreateIn'], Schemas['AnalysisOut']>({
    fn: async (body) => unwrap(await api.POST('/api/analyses', { body })),
    invalidate: [['analyses']],
    onSuccess: (a) => setResultId(a.id), // the mining screen shatters the rock first, then opens the result
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
      <MiningLoader pending={create.isPending} failed={create.isError}
        onFinished={() => resultId && navigate({ to: '/analizy/$analysisId', params: { analysisId: resultId }, search: {} })} />
      <Intro can={['wkleić opis albo wgrać dokument (PDF, Word)', 'poprawić odczytane cechy', 'zapisać analizę w „Moich analizach”']}>
        Opisz planowaną inwestycję wodno-kanalizacyjną: zakres i skalę, lokalizację, wartość netto lub brutto, czas realizacji, formułę oraz stan przygotowania terenu, decyzji i uzgodnień. Możesz wybrać, który model językowy przeczyta opis. Lokalny model na naszym serwerze potrzebuje 1–2 minut.
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
            <ModelPicker value={model} onChange={setModel} />
            <Button disabled={!canExtract} loading={extract.isPending} onClick={() => extract.mutate({ text: text || null, document_ids: docIds, llm_profile: model || null })}>
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
                onClick={() => create.mutate({ title, text: text || null, document_ids: docIds, features, params: model ? { llm_profile: model } : {}, project_id: null })}>
                Analizuj ryzyko</Button>)}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
