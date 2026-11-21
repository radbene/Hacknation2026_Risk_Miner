import { Link } from '@tanstack/react-router'
import { ClipboardCheck, Database, FlaskConical, Library, Sparkles, Activity } from 'lucide-react'
import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Card, CardContent, CardHeader, QueryState } from '@/components/ui'
import { fmtDateTime } from '@/lib/utils'

const COUNT_PL: Record<string, string> = {
  projects: 'Projekty', procedures: 'Postępowania', notices: 'Ogłoszenia BZP', contracts: 'Umowy', changes: 'Zmiany umów', contract_changes: 'Zmiany umów',
  events: 'Zdarzenia', pending_review: 'Do decyzji eksperta', analyses: 'Analizy', documents: 'Dokumenty', evidence: 'Dowody (źródła)', lessons: 'Lekcje',
  op_log: 'Zapytania do źródeł', data_issues: 'Braki danych',
}
const AREAS = [
  { to: '/projekty', icon: Database, title: 'Baza przypadków', text: '22 projekty organizatora powiązane z BZP + tysiące automatycznie zebranych postępowań wod-kan; oś czasu plan vs wykonanie, zmiany umów, przyczyny z cytatami.' },
  { to: '/kolejka', icon: ClipboardCheck, title: 'Kolejka eksperta', text: 'Każda propozycja systemu czeka na decyzję: akceptuj, popraw, odrzuć, zmień powiązanie. Decyzje przetrwają ponowne przeliczenie.' },
  { to: '/wiedza', icon: Library, title: 'Wiedza ekspercka', text: 'Katalog ryzyk R01–R15, podsektory, fazy, dokumenty, checklisty, klauzule – edytowalne, wersjonowane, z przywracaniem.' },
  { to: '/nowa-inwestycja', icon: Sparkles, title: 'Nowa inwestycja', text: 'Opis lub dokument → cechy → podobne inwestycje z wyjaśnieniem → zakresy opóźnień i kosztów → czerwone flagi → klauzule → karta DOCX.' },
  { to: '/zrodla', icon: Activity, title: 'Źródła i operacje', text: 'Konektory, dziennik zapytań, jakość dopasowania (precyzja/czułość), modele i miejsce przetwarzania danych.' },
  { to: '/jak-testowac', icon: FlaskConical, title: 'Jak testować', text: 'Scenariusze dla jury – krok po kroku, z odnośnikami do konkretnych przypadków.' },
] as const

export default function Start() {
  const d = useApi(['dashboard'], async () => unwrap(await api.GET('/api/dashboard')))
  return (
    <div>
      <PageHeader title="RISK MINER" description="Inteligentna baza doświadczeń inwestycji publicznych – pilotaż: gospodarka wodno-ściekowa. Każda liczba ma źródło, każdy wniosek czeka na decyzję eksperta." />
      <QueryState q={d}>{(x) => (
        <div className="mb-6 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Object.entries(x.counts).slice(0, 12).map(([k, v]) => (
            <Card key={k} className="p-3"><div className="text-xs text-slate-500">{COUNT_PL[k] ?? k}</div><div className="text-2xl font-semibold tabular-nums">{v.toLocaleString('pl-PL')}</div></Card>))}
        </div>
      )}</QueryState>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {AREAS.map((a) => (
          <Link key={a.to} to={a.to} className="group">
            <Card className="h-full transition-colors group-hover:border-brand">
              <CardHeader title={<span className="flex items-center gap-2"><a.icon size={16} className="text-brand" />{a.title}</span>} />
              <CardContent className="text-sm text-slate-600">{a.text}</CardContent>
            </Card>
          </Link>))}
      </div>
      <QueryState q={d}>{(x) => x.last_jobs?.length ? (
        <Card className="mt-6"><CardHeader title="Ostatnie zadania" />
          <CardContent><ul className="space-y-1 text-xs">{(x.last_jobs ?? []).slice(0, 8).map((j, i) => (
            <li key={i} className="flex items-center gap-2"><Badge variant={j.state === 'done' ? 'success' : j.state === 'failed' ? 'danger' : 'info'}>{String(j.state)}</Badge>
              <span className="font-mono">{String(j.kind)}</span><span className="text-slate-500">{fmtDateTime(String(j.created_at ?? ''))}</span><span className="truncate">{String(j.message ?? '')}</span></li>))}</ul></CardContent></Card>
      ) : null}</QueryState>
    </div>
  )
}
