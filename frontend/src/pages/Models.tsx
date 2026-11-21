import { Plus } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { Intro } from '@/components/Explain'
import { JobRunner } from '@/components/JobRunner'
import { ExpertOnly } from '@/components/Layout'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Input, Label, QueryState, Select, Textarea, useToast } from '@/components/ui'
import { fmtNum } from '@/lib/utils'

type R = Schemas['LLMRoutingOut']
type Prof = Schemas['LLMProfileOut']

const TASK_PL: Record<string, { name: string; what: string }> = {
  causes: { name: 'Rozpoznawanie przyczyn zdarzeń', what: 'czyta opis zmiany umowy i przypisuje kategorię ryzyka z cytatem' },
  features: { name: 'Odczytywanie cech nowej inwestycji', what: 'uzupełnia cechy z opisu inwestycji (tylko z cytatem)' },
  recommendations: { name: 'Podsumowanie analizy i zalecenia', what: 'pisze krótkie podsumowanie wyników analizy' },
  doc_fragments: { name: 'Ryzykowne fragmenty dokumentów', what: 'wskazuje w dokumentach zapisy mogące świadczyć o ryzyku' },
  clauses: { name: 'Propozycje zapisów umownych', what: 'proponuje treść klauzul' },
  category_proposal: { name: 'Nowe kategorie ryzyka', what: 'proponuje kategorię, gdy żadna z R01–R15 nie pasuje' },
  lessons: { name: 'Wnioski z raportów kontroli', what: 'wyciąga wnioski z raportów NIK' },
}
const WHERE: Record<string, string> = {
  local: 'na naszym serwerze, dane nie opuszczają systemu', eu: 'w chmurze w UE', non_eu: 'w usłudze poza UE', none: 'same reguły',
}
const KIND: Record<string, string> = {
  openai_compatible: 'serwer zgodny z API OpenAI (Ollama, vLLM, LM Studio)', anthropic: 'Anthropic (Claude)', gemini: 'Google Gemini',
  openai: 'OpenAI', litellm: 'pośrednik LiteLLM', none: 'reguły',
}
const nameOf = (r: R, n: string) => r.profiles.find((p) => p.name === n)?.display_name ?? n

export default function Models() {
  return <ExpertOnly what="Modele językowe"><ModelsInner /></ExpertOnly>
}

function ModelsInner() {
  const q = useApi(['settings', 'llm'], async () => unwrap(await api.GET('/api/settings/llm')))
  const usage = useApi(['ops', 'llm-usage'], async () => unwrap(await api.GET('/api/ops/llm-usage')))
  const [add, setAdd] = useState(false)
  return (
    <div>
      <PageHeader title="Modele językowe" actions={<Button onClick={() => setAdd(true)}><Plus size={14} />Dodaj własny model</Button>} />
      <Intro can={['zmienić kolejność modeli dla zadania', 'sprawdzić połączenie z modelem', 'dodać własny model, np. serwer z Bielikiem lub PLLuM w instytucji, bez zmian w programie']}>
        System używa pierwszego dostępnego modelu z listy zadania. Gdy żaden nie odpowie, działa na samych regułach. Wynik modelu ma etykietę „Wniosek modelu”, musi mieć cytat sprawdzony w źródle i czeka na decyzję eksperta.
      </Intro>
      <QueryState q={q}>{(r) => (
        <div className="space-y-6">
          <section>
            <h2 className="mb-2 text-sm font-semibold text-slate-700">Które modele wykonują które zadania</h2>
            <div className="grid gap-3 md:grid-cols-2">{Object.entries(r.tasks).map(([task, chain]) => <TaskCard key={task} r={r} task={task} chain={chain} />)}</div>
          </section>
          <section>
            <h2 className="mb-2 text-sm font-semibold text-slate-700">Dostępne modele</h2>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{r.profiles.filter((p) => p.provider !== 'none').map((p) => <ModelCard key={p.name} p={p} />)}</div>
          </section>
          <QueryState q={usage}>{(rows) => rows.length ? (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-slate-700">Wykorzystanie modeli</h2>
              <ul className="space-y-1 text-sm">{rows.map((u, i) => (
                <li key={i} className="rounded border border-slate-200 bg-white px-3 py-2">
                  <b>{TASK_PL[u.task]?.name ?? u.task}</b>: {u.calls} wywołań{u.cached ? ` (w tym ${u.cached} z zapisanych odpowiedzi)` : ''}{u.errors ? `, ${u.errors} nieudanych` : ''}
                  {', '}{nameOf(r, (r.profiles.find((p) => p.model === u.model)?.name) ?? u.model ?? '')}
                  {u.cost_usd > 0 ? `, koszt ok. ${fmtNum(u.cost_usd, 2)} USD` : ', bez kosztów usług'}
                </li>))}</ul>
            </section>) : null}</QueryState>
        </div>
      )}</QueryState>
      <AddModelDialog open={add} onClose={() => setAdd(false)} />
    </div>
  )
}

function TaskCard({ r, task, chain }: { r: R; task: string; chain: string[] }) {
  const { toast } = useToast()
  const [edit, setEdit] = useState(false)
  const models = chain.filter((n) => n !== 'rules')
  const [first, setFirst] = useState(models[0] ?? 'rules')
  const [second, setSecond] = useState(models[1] ?? '')
  const m = useApiMutation<Schemas['LLMRoutingIn'], R>({
    fn: async (body) => unwrap(await api.PUT('/api/settings/llm', { body })),
    invalidate: [['settings', 'llm']],
    onSuccess: () => { toast({ kind: 'success', title: 'Zapisano kolejność modeli' }); setEdit(false) },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zapisać', description: String(e) }),
  })
  const opts = r.profiles.filter((p) => p.provider !== 'none').map((p) => ({ value: p.name, label: `${p.display_name ?? p.name}${p.available ? '' : ' (niedostępny)'}` }))
  const meta = TASK_PL[task] ?? { name: task, what: '' }
  return (
    <Card>
      <CardHeader title={meta.name} description={meta.what} actions={<Button size="sm" variant="ghost" onClick={() => setEdit((e) => !e)}>{edit ? 'Anuluj' : 'Zmień'}</Button>} />
      <CardContent className="text-sm">
        {!edit ? (
          <ol className="space-y-1">
            {models.map((n, i) => {
              const p = r.profiles.find((x) => x.name === n)
              return <li key={n} className="flex items-start gap-2">
                <span className="w-24 shrink-0 text-xs text-slate-500">{i === 0 ? 'Najpierw' : 'Jeśli niedostępny'}</span>
                <span>{p?.display_name ?? n}{p && !p.available && <span className="text-xs text-amber-700"> (niedostępny)</span>}</span></li>
            })}
            <li className="flex items-start gap-2"><span className="w-24 shrink-0 text-xs text-slate-500">Na końcu</span><span>reguły bez modelu (zawsze działają)</span></li>
          </ol>
        ) : (
          <div className="space-y-2">
            <div><Label>Najpierw używaj</Label><Select value={first} onChange={(e) => setFirst(e.target.value)} options={opts} /></div>
            <div><Label>Jeśli niedostępny</Label><Select value={second} onChange={(e) => setSecond(e.target.value)} options={opts} placeholder="— od razu reguły —" /></div>
            <Button size="sm" loading={m.isPending} onClick={() => m.mutate({ tasks: { [task]: [first, ...(second && second !== first ? [second] : []), 'rules'] }, comment: `Kolejność modeli: ${meta.name}` })}>Zapisz</Button>
          </div>)}
      </CardContent>
    </Card>
  )
}

function ModelCard({ p }: { p: Prof }) {
  return (
    <Card>
      <CardHeader title={p.display_name ?? p.name}
        actions={p.available ? <Badge variant="success">dostępny</Badge> : <Badge>niedostępny</Badge>} />
      <CardContent className="space-y-1 text-sm">
        <p>Rodzaj: {KIND[p.provider] ?? p.provider}</p>
        <p>Gdzie działa: {WHERE[p.data_location] ?? p.data_location}</p>
        {!p.available && p.unavailable_reason && <p className="text-xs text-amber-800">Dlaczego niedostępny: {p.unavailable_reason}</p>}
        {p.available && <JobRunner label="Sprawdź połączenie" variant="outline"
          start={async () => unwrap(await api.POST('/api/settings/llm/test', { body: { profile: p.name, model: null } }))} />}
      </CardContent>
    </Card>
  )
}

function AddModelDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { toast } = useToast()
  const [f, setF] = useState({ display_name: '', provider: 'openai_compatible', base_url: 'http://localhost:11434/v1', model: '', api_key_env: '', data_location: 'local', use_everywhere: false, note: '' })
  const set = (k: keyof typeof f, v: string | boolean) => setF((x) => ({ ...x, [k]: v }))
  const m = useApiMutation<Schemas['LLMRoutingIn'], R>({
    fn: async (body) => unwrap(await api.PUT('/api/settings/llm', { body })),
    invalidate: [['settings', 'llm']],
    onSuccess: () => { toast({ kind: 'success', title: 'Model dodany', description: 'Sprawdź połączenie na karcie modelu.' }); onClose() },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się dodać modelu', description: String(e) }),
  })
  const slug = 'wlasny_' + (f.display_name || f.model).toLowerCase().normalize('NFD').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 30)
  const submit = () => {
    const profile = { provider: f.provider, display_name: f.display_name, model: f.model, data_location: f.data_location,
      ...(f.provider === 'openai_compatible' ? { base_url: f.base_url } : {}), ...(f.api_key_env ? { api_key_env: f.api_key_env } : {}),
      max_tokens: 2000, extra: f.data_location === 'local' ? { temperature: 0.1, timeout_s: 300 } : {} }
    const tasks = f.use_everywhere ? Object.fromEntries(Object.keys(TASK_PL).map((t) => [t, [slug, 'rules']])) : undefined
    m.mutate({ profiles: { [slug]: profile }, ...(tasks ? { tasks } : {}), comment: f.note || `Dodano model ${f.display_name}` })
  }
  return (
    <Dialog open={open} onClose={onClose} title="Dodaj własny model językowy"
      description="Klucza API nie wpisuj w przeglądarce. Podaj nazwę zmiennej środowiskowej na serwerze, w której zapisał go administrator."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button><Button loading={m.isPending} disabled={!f.display_name.trim() || !f.model.trim()} onClick={submit}>Dodaj model</Button></>}>
      <form className="space-y-3 text-sm" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div><Label htmlFor="m-n">Nazwa wyświetlana</Label><Input id="m-n" value={f.display_name} onChange={(e) => set('display_name', e.target.value)} placeholder="np. PLLuM 12B (serwer w ministerstwie)" /></div>
        <div><Label htmlFor="m-p">Rodzaj</Label><Select id="m-p" value={f.provider} onChange={(e) => set('provider', e.target.value)}
          options={['openai_compatible', 'anthropic', 'gemini', 'openai'].map((v) => ({ value: v, label: KIND[v] }))} /></div>
        {f.provider === 'openai_compatible' && <div><Label htmlFor="m-u">Adres serwera</Label><Input id="m-u" value={f.base_url} onChange={(e) => set('base_url', e.target.value)} />
          <p className="mt-0.5 text-xs text-slate-500">Dla Ollamy na tym samym serwerze: http://localhost:11434/v1 (w kontenerach: http://ollama:11434/v1).</p></div>}
        <div><Label htmlFor="m-m">Identyfikator modelu</Label><Input id="m-m" value={f.model} onChange={(e) => set('model', e.target.value)} placeholder="np. riskminer-bielik albo SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M" /></div>
        <div><Label htmlFor="m-k">Zmienna z kluczem API (jeśli wymagany)</Label><Input id="m-k" value={f.api_key_env} onChange={(e) => set('api_key_env', e.target.value)} placeholder="np. MOJ_MODEL_API_KEY" /></div>
        <div><Label htmlFor="m-l">Gdzie przetwarzane są dane</Label><Select id="m-l" value={f.data_location} onChange={(e) => set('data_location', e.target.value)}
          options={[{ value: 'local', label: 'na naszym serwerze' }, { value: 'eu', label: 'w chmurze w UE' }, { value: 'non_eu', label: 'poza UE' }]} /></div>
        <label className="flex items-center gap-2"><input type="checkbox" className="accent-brand" checked={f.use_everywhere} onChange={(e) => set('use_everywhere', e.target.checked)} />
          Używaj tego modelu jako pierwszego we wszystkich zadaniach</label>
        <div><Label htmlFor="m-c">Uzasadnienie zmiany (do historii)</Label><Textarea id="m-c" rows={2} value={f.note} onChange={(e) => set('note', e.target.value)} /></div>
      </form>
    </Dialog>
  )
}
