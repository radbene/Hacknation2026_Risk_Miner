import { useBlocker, useNavigate } from '@tanstack/react-router'
import { History, Plus, Redo2, RotateCcw, Save, Search, Trash2, Undo2, Upload } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi, useApiMutation } from '@/api/hooks'
import { Intro } from '@/components/Explain'
import { ExpertOnly } from '@/components/Layout'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, CardContent, CardHeader, Dialog, Input, Label, QueryState, Textarea, useToast } from '@/components/ui'
import { cn, fmtDateTime } from '@/lib/utils'
import { knowledgeRoute } from '@/router'

const SECTOR = 'wodkan'
type Row = Record<string, unknown> & { _k: string }

/** What each table is and how the system uses it – shown above the editor. */
const TABLE_HELP: Record<string, { what: string; used: string; source: 'eksperci' | 'zespół' }> = {
  risks: { what: 'Katalog 15 kategorii ryzyka (R01–R15) z ich typowymi skutkami.', used: 'Każde zdarzenie i każda czerwona flaga dostaje kod z tego katalogu.', source: 'eksperci' },
  subsectors: { what: 'Podsektory gospodarki wodno-ściekowej (sieć wodociągowa, kanalizacja, oczyszczalnie…).', used: 'Do grupowania inwestycji i wyboru porównywalnych przypadków.', source: 'eksperci' },
  phases: { what: 'Fazy inwestycji od przygotowania do eksploatacji.', used: 'Przypisanie dokumentów i zdarzeń do etapu inwestycji.', source: 'eksperci' },
  documents: { what: 'Rodzaje dokumentów inwestycji i co z nich wynika.', used: 'Rozpoznawanie rodzaju wgranego dokumentu i wskazywanie braków.', source: 'eksperci' },
  event_sources: { what: 'W jakim dokumencie szukać informacji o danym zdarzeniu.', used: 'Podpowiedzi „co uzupełnić” w brakach danych.', source: 'eksperci' },
  art455: { what: 'Podstawy prawne zmian umowy z art. 455 Prawa zamówień publicznych.', used: 'Opis zmian umów w zdarzeniach.', source: 'eksperci' },
  art455_map: { what: 'Która podstawa zmiany umowy oznacza jaki typ zmiany i jakie kategorie ryzyka.', used: 'Automatyczne kategoryzowanie zmian umów.', source: 'zespół' },
  checklist: { what: 'Lista kontrolna 9 punktów przygotowania inwestycji wodociągowej.', used: 'Flaga „brak informacji” w analizie nowej inwestycji.', source: 'eksperci' },
  checklist_rcodes: { what: 'Do jakich kategorii ryzyka odnosi się każdy punkt listy kontrolnej.', used: 'Łączenie braków na liście z kategoriami ryzyka.', source: 'zespół' },
  clauses: { what: 'Proponowane zapisy umowne i działania zapobiegawcze, po jednym na kategorię ryzyka.', used: 'Rekomendacje w analizie nowej inwestycji (sekcja „Działania i klauzule”).', source: 'zespół' },
  completeness_states: { what: 'Cztery stany kompletności danych (np. „nie ma w zebranych materiałach” ≠ „potwierdzono, że nie wykonano”).', used: 'Zakładka „Braki w danych” na karcie projektu.', source: 'eksperci' },
  doc_fragments: { what: 'Wzorce fragmentów dokumentów wskazujących ryzyko.', used: 'Wyszukiwanie ryzykownych zapisów w wgranych dokumentach.', source: 'zespół' },
  event_rules: { what: 'Reguły rozpoznawania zdarzeń z danych BZP (opóźnienie, wypłata ponad wartość, kary…).', used: 'Wyliczanie zdarzeń dla każdej inwestycji.', source: 'zespół' },
  guide_sections: { what: 'Rozdziały poradnika eksperckiego przygotowania inwestycji.', used: 'Odnośniki z listy kontrolnej do poradnika.', source: 'eksperci' },
  porady: { what: 'Zasady pracy z dokumentami (chronologia, hierarchia, brak dokumentu a brak działania…).', used: 'Reguły sprawdzania sprzeczności i braków.', source: 'eksperci' },
  risk_signals: { what: 'Słowa i zwroty, które w opisie przyczyny wskazują daną kategorię ryzyka.', used: 'Klasyfikacja przyczyn zmian umów regułami (bez modelu).', source: 'zespół' },
  similarity_weights: { what: 'Jak bardzo każda cecha liczy się przy szukaniu podobnych inwestycji (podsektor, skala, formuła…).', used: 'Wyszukiwanie i ranking podobnych inwestycji w analizie.', source: 'zespół' },
  sources: { what: 'Źródła informacji o inwestycjach.', used: 'Opis pochodzenia danych.', source: 'eksperci' },
  subsector_rules: { what: 'Kody CPV i słowa kluczowe przypisujące postępowanie do podsektora.', used: 'Klasyfikacja tysięcy postępowań pobranych z BZP.', source: 'zespół' },
  texts: { what: 'Teksty objaśniające z materiałów eksperckich.', used: 'Opisy w aplikacji.', source: 'eksperci' },
  thresholds: { what: 'Progi liczbowe (np. ile podobnych inwestycji brać, od ilu przypadków liczyć zakresy).', used: 'Analiza nowej inwestycji i dopasowanie projektów.', source: 'zespół' },
}
const KEY_LABEL: Record<string, string> = {
  code: 'Kod', name: 'Nazwa', effects: 'Skutki', description: 'Opis', patterns: 'Wzorce (słowa)', status: 'Status', subsector: 'Podsektor',
  cpv: 'Kody CPV', keywords: 'Słowa kluczowe', key: 'Parametr', value: 'Wartość', note: 'Uwagi', no: 'Nr', item: 'Punkt listy',
  guide_sections: 'Rozdziały poradnika', risk_codes: 'Kategorie ryzyka', applies_to: 'Dotyczy podsektorów', weight: 'Waga', feature: 'Cecha',
  title: 'Tytuł', text: 'Treść', trigger: 'Kiedy stosować', legal_basis: 'Podstawa prawna', risk_code: 'Kategoria ryzyka', mechanic: 'Zasada', advice: 'Porada',
  state: 'Stan', label: 'Etykieta', meaning: 'Znaczenie', event_type: 'Rodzaj zdarzenia', basis: 'Podstawa', meaning_pl: 'Znaczenie',
}

let seq = 0
const withKeys = (rows: Record<string, unknown>[]): Row[] => rows.map((r) => ({ ...r, _k: `r${++seq}` }))
const strip = (rows: Row[]) => rows.map(({ _k, ...r }) => r) // eslint-disable-line @typescript-eslint/no-unused-vars

export default function Knowledge() {
  return <ExpertOnly what="Wiedza ekspercka"><KnowledgeInner /></ExpertOnly>
}

function KnowledgeInner() {
  const s = knowledgeRoute.useSearch()
  const navigate = useNavigate({ from: '/wiedza' })
  const tables = useApi(['knowledge', SECTOR], async () => unwrap(await api.GET('/api/knowledge/{sector}/tables', { params: { path: { sector: SECTOR } } })))
  const { toast } = useToast()
  const reimport = useApiMutation<void, Schemas['KnowledgeImportReport']>({
    fn: async () => unwrap(await api.POST('/api/knowledge/{sector}/import', { params: { path: { sector: SECTOR } } })),
    invalidate: [['knowledge']],
    onSuccess: (r) => toast({ kind: 'success', title: 'Wiedza wczytana z plików', description: r.written.length ? `Nowe wersje tabel: ${r.written.join(', ')}` : 'Pliki nie zawierały zmian.' }),
    onError: (e) => toast({ kind: 'error', title: 'Wczytanie nie powiodło się', description: String(e) }),
  })
  return (
    <div>
      <PageHeader title="Wiedza ekspercka"
        actions={<Button variant="outline" loading={reimport.isPending} onClick={() => reimport.mutate()} title="Tabele z katalogu knowledge/, np. po imporcie nowego dokumentu eksperckiego"><Upload size={14} aria-hidden />Wczytaj z plików</Button>} />
      <Intro can={['zmieniać wartości, dodawać i usuwać wiersze; każdą zmianę cofniesz przyciskiem „Cofnij”', 'zapisać zmiany jako nową wersję; dopiero wtedy obowiązują, a wyjście bez zapisu je porzuca', 'przywrócić poprzednią wersję']}>
        Wiedza, której system używa w każdej analizie: katalog ryzyk, podsektory, listy kontrolne, zapisy umowne, reguły rozpoznawania zdarzeń i wagi podobieństwa. Część tabel pochodzi z materiałów eksperckich MFiPR, część to propozycje zespołu do zatwierdzenia. Nowy sektor to nowy zestaw tabel, bez zmian w programie.
      </Intro>
      <QueryState q={tables} empty={(t) => t.length === 0}>{(ts) => {
        const cur = s.table ?? 'risks'
        const group = (src: 'eksperci' | 'zespół') => ts.filter((t) => (TABLE_HELP[t.name]?.source ?? 'zespół') === src)
        return (
          <div className="grid gap-4 lg:grid-cols-[17rem_1fr]">
            <nav aria-label="Tabele wiedzy" className="space-y-3">
              {(['eksperci', 'zespół'] as const).map((src) => (
                <div key={src}>
                  <div className="mb-1 px-1 text-xs font-medium text-slate-500">{src === 'eksperci' ? 'Z materiałów eksperckich MFiPR' : 'Propozycje zespołu'}</div>
                  <div className="space-y-1">{group(src).map((t) => (
                    <button key={t.name} onClick={() => navigate({ search: { table: t.name }, replace: true })}
                      className={cn('w-full cursor-pointer rounded border px-2 py-1.5 text-left text-xs', cur === t.name ? 'border-brand bg-brand-soft' : 'border-slate-200 bg-white hover:bg-slate-50')}>
                      <div className="font-medium">{t.title && t.title !== t.name ? t.title : TABLE_HELP[t.name]?.what.split('.')[0] ?? t.name}</div>
                      <div className="text-slate-500">{t.n_rows} {t.n_rows === 1 ? 'wiersz' : 'wierszy'}</div>
                    </button>))}</div>
                </div>))}
            </nav>
            <TableEditor key={cur} name={cur} />
          </div>
        )
      }}</QueryState>
    </div>
  )
}

interface Draft { rows: Row[]; note: string }

function TableEditor({ name }: { name: string }) {
  const t = useApi(['knowledge', SECTOR, name], async () => unwrap(await api.GET('/api/knowledge/{sector}/tables/{name}', { params: { path: { sector: SECTOR, name } } })))
  const [hist, setHist] = useState<Draft[]>([])
  const [idx, setIdx] = useState(0)
  const [filter, setFilter] = useState('')
  const [save, setSave] = useState(false)
  const [versions, setVersions] = useState(false)
  useEffect(() => { if (t.data) { setHist([{ rows: withKeys(t.data.rows as Record<string, unknown>[]), note: 'wersja zapisana' }]); setIdx(0) } }, [t.data])
  const rows = hist[idx]?.rows ?? []
  const dirty = idx > 0
  useBlocker({ shouldBlockFn: () => dirty && !window.confirm('Masz niezapisane zmiany w tabeli. Wyjść i porzucić je?'), enableBeforeUnload: dirty })
  const push = (next: Row[], note: string) => { setHist((h) => [...h.slice(0, idx + 1), { rows: next, note }]); setIdx((i) => i + 1) }
  const help = TABLE_HELP[name]
  const cols = useMemo(() => {
    const declared = (t.data?.columns ?? []).map((c) => ({ key: c.key, label: c.label && c.label !== c.key ? c.label : KEY_LABEL[c.key] ?? c.key }))
    const keys = new Set(declared.map((c) => c.key))
    for (const r of rows) for (const k of Object.keys(r)) if (k !== '_k' && !keys.has(k)) { keys.add(k); declared.push({ key: k, label: KEY_LABEL[k] ?? k }) }
    return declared
  }, [t.data, rows])
  const titleKey = cols.find((c) => ['name', 'title', 'item', 'code', 'key', 'mechanic', 'subsector', 'state', 'event_type'].includes(c.key))?.key
  const shown = rows.map((r, i) => ({ r, i })).filter(({ r }) => !filter || JSON.stringify(r).toLowerCase().includes(filter.toLowerCase()))

  return (
    <QueryState q={t}>{(d) => (
      <div className="min-w-0 space-y-3">
        <Card>
          <CardHeader title={d.title && d.title !== d.name ? d.title : help?.what.split('.')[0] ?? d.name}
            description={<>Wersja {d.version}{d.edited_by ? `, ${d.edited_by}` : ''}{d.updated_at ? `, ${fmtDateTime(d.updated_at)}` : ''}</>}
            actions={<Button size="sm" variant="outline" onClick={() => setVersions(true)}><History size={14} />Poprzednie wersje</Button>} />
          {help && <CardContent className="space-y-1 text-sm">
            <p><b>Co zawiera:</b> {help.what}</p>
            <p><b>Do czego system jej używa:</b> {help.used}</p>
            {help.source === 'zespół' && <p className="text-xs text-slate-500">Propozycja zespołu do weryfikacji przez eksperta.</p>}
          </CardContent>}
        </Card>
        <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white/95 p-2 backdrop-blur">
          <Button size="sm" variant="outline" disabled={idx === 0} onClick={() => setIdx((i) => i - 1)} title={hist[idx]?.note ? `Cofnij: ${hist[idx].note}` : 'Cofnij'}><Undo2 size={14} />Cofnij</Button>
          <Button size="sm" variant="outline" disabled={idx >= hist.length - 1} onClick={() => setIdx((i) => i + 1)}><Redo2 size={14} />Ponów</Button>
          <Button size="sm" variant="outline" onClick={() => push([...rows, { _k: `r${++seq}` }], 'dodano wiersz')}><Plus size={14} />Dodaj wiersz</Button>
          <label className="relative ml-auto"><span className="sr-only">Szukaj w tabeli</span><Search size={13} className="absolute left-2 top-2 text-slate-400" />
            <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Szukaj w tabeli" className="h-8 w-48 pl-7 text-xs" /></label>
          {dirty ? <Badge variant="warning">{idx} {idx === 1 ? 'niezapisana zmiana' : 'niezapisanych zmian'}</Badge> : <Badge variant="success">bez zmian</Badge>}
          <Button size="sm" disabled={!dirty} onClick={() => setSave(true)}><Save size={14} />Zapisz jako nową wersję</Button>
        </div>
        {dirty && <p className="text-xs text-slate-500">Ostatnia zmiana: {hist[idx]?.note}</p>}
        <div className="space-y-2">{shown.map(({ r, i }) => (
          <Card key={r._k} className="p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className="text-sm font-semibold">{titleKey && r[titleKey] != null ? String(r[titleKey]) : `Wiersz ${i + 1}`}</span>
              <button aria-label={`Usuń: ${titleKey && r[titleKey] ? String(r[titleKey]) : `wiersz ${i + 1}`}`} className="cursor-pointer rounded p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                onClick={() => push(rows.filter((x) => x._k !== r._k), `usunięto „${titleKey && r[titleKey] ? String(r[titleKey]).slice(0, 40) : `wiersz ${i + 1}`}”`)}><Trash2 size={15} /></button>
            </div>
            <div className="grid gap-x-4 gap-y-2 md:grid-cols-2">{cols.map((c) => (
              <Field key={c.key} label={c.label} value={r[c.key]} id={`${r._k}-${c.key}`}
                onCommit={(v) => push(rows.map((x) => (x._k === r._k ? { ...x, [c.key]: v } : x)), `${c.label} w „${titleKey && r[titleKey] ? String(r[titleKey]).slice(0, 30) : `wierszu ${i + 1}`}”`)} />))}</div>
          </Card>))}
          {!shown.length && <p className="py-6 text-center text-sm text-slate-500">Brak wierszy{filter ? ' pasujących do wyszukiwania' : ''}.</p>}
        </div>
        <SaveDialog open={save} onClose={() => setSave(false)} name={name} rows={strip(rows)} onSaved={() => setIdx(0)} />
        <VersionsDialog open={versions} onClose={() => setVersions(false)} name={name} current={d.version} />
      </div>
    )}</QueryState>
  )
}

/** One field: lists as comma-separated text, longer text as a text area; committed on leaving the field. */
function Field({ label, value, id, onCommit }: { label: string; value: unknown; id: string; onCommit: (v: unknown) => void }) {
  const isList = Array.isArray(value)
  const isObj = value !== null && typeof value === 'object' && !isList
  const shown = value == null ? '' : isList ? (value as unknown[]).map(String).join(', ') : isObj ? JSON.stringify(value) : String(value)
  const [v, setV] = useState(shown)
  useEffect(() => setV(shown), [shown])
  const commit = () => {
    if (v === shown) return
    if (isList) onCommit(v.split(',').map((x) => x.trim()).filter(Boolean))
    else if (isObj) { try { onCommit(JSON.parse(v)) } catch { setV(shown) } }
    else if (typeof value === 'number' && v.trim() !== '' && !Number.isNaN(Number(v.replace(',', '.')))) onCommit(Number(v.replace(',', '.')))
    else onCommit(v)
  }
  const long = shown.length > 70 || isObj
  return (
    <div className={long ? 'md:col-span-2' : undefined}>
      <Label htmlFor={id} className="text-xs text-slate-500">{label}{isList && <span className="font-normal"> (oddziel przecinkami)</span>}</Label>
      {long ? <Textarea id={id} rows={Math.min(5, Math.ceil(shown.length / 90) + 1)} value={v} onChange={(e) => setV(e.target.value)} onBlur={commit} className="text-sm" />
        : <Input id={id} value={v} onChange={(e) => setV(e.target.value)} onBlur={commit} onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }} className="h-8 text-sm" />}
    </div>
  )
}

function SaveDialog({ open, onClose, name, rows, onSaved }: { open: boolean; onClose: () => void; name: string; rows: Record<string, unknown>[]; onSaved: () => void }) {
  const [comment, setComment] = useState('')
  const { toast } = useToast()
  const m = useApiMutation<Schemas['KnowledgeTableIn'], Schemas['KnowledgeTableOut']>({
    fn: async (body) => unwrap(await api.PUT('/api/knowledge/{sector}/tables/{name}', { params: { path: { sector: SECTOR, name } }, body })),
    invalidate: [['knowledge']],
    onSuccess: (t) => { toast({ kind: 'success', title: `Zapisano wersję ${t.version}` }); onSaved(); onClose(); setComment('') },
    onError: (e) => toast({ kind: 'error', title: 'Nie udało się zapisać', description: String(e) }),
  })
  return (
    <Dialog open={open} onClose={onClose} title="Zapisz nową wersję tabeli" description="Poprzednia wersja zostaje w historii."
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
    onSuccess: (t) => { toast({ kind: 'success', title: `Przywrócono, obowiązuje wersja ${t.version}` }); onClose() },
  })
  return (
    <Dialog open={open} onClose={onClose} title="Poprzednie wersje tabeli" description="Przywrócona treść staje się nową wersją. Historia zostaje.">
      <QueryState q={v}>{(vs) => (
        <ul className="space-y-1 text-sm">{vs.map((x) => (
          <li key={x.version} className="flex items-center justify-between gap-2 rounded border border-slate-200 p-2">
            <span>Wersja {x.version}, {fmtDateTime(x.updated_at)}{x.edited_by ? `, ${x.edited_by}` : ''}</span>
            {x.version === current ? <Badge variant="success">obowiązuje</Badge>
              : <Button size="sm" variant="outline" loading={m.isPending} onClick={() => m.mutate(x.version)}><RotateCcw size={12} />Przywróć</Button>}
          </li>))}</ul>
      )}</QueryState>
    </Dialog>
  )
}
