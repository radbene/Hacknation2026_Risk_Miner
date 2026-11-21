import { Link } from '@tanstack/react-router'
import { Flag, Plus, Users } from 'lucide-react'
import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'
import { Intro } from '@/components/Explain'
import { PageHeader } from '@/components/PageHeader'
import { Badge, Button, Card, QueryState } from '@/components/ui'
import { useAuth } from '@/lib/auth'
import { fmtDateTime } from '@/lib/utils'
import { analysesRoute } from '@/router'

export default function Analyses() {
  const s = analysesRoute.useSearch()
  const { isExpert } = useAuth()
  const q = useApi(['analyses', s], async () => unwrap(await api.GET('/api/analyses', { params: { query: { q: s.q ?? null, status: s.status ?? null, subsector: s.subsector ?? null, limit: 200 } } })))
  return (
    <div>
      <PageHeader title={isExpert ? 'Analizy użytkowników' : 'Moje analizy'}
        actions={!isExpert ? <Link to="/nowa-inwestycja"><Button><Plus size={14} />Nowa analiza</Button></Link> : undefined} />
      <Intro can={isExpert ? ['otworzyć analizę i zatwierdzić lub odrzucić jej flagi, zakresy i rekomendacje'] : ['otworzyć analizę, zmienić cechy inwestycji, pominąć niepasujące podobne inwestycje', 'pobrać kartę analizy jako dokument Word']}>
        {isExpert ? 'Analizy nowych inwestycji przygotowane przez użytkowników. Ekspert ocenia ich elementy – zatwierdzone wnioski są wyraźnie oznaczone.'
          : 'Zapisane analizy planowanych inwestycji. Każdą można otworzyć ponownie – wyniki są przeliczane na aktualnej bazie przypadków.'}
      </Intro>
      <QueryState q={q}>{(d) => (
        d.items.length === 0
          ? <p className="py-8 text-center text-sm text-slate-500">Nie ma jeszcze analiz. <Link to="/nowa-inwestycja" className="text-brand hover:underline">Rozpocznij pierwszą</Link>.</p>
          : <div className="grid gap-3 md:grid-cols-2">{d.items.map((a) => (
            <Link key={a.id} to="/analizy/$analysisId" params={{ analysisId: a.id }} search={{}} className="group">
              <Card className="h-full p-4 group-hover:border-brand">
                <h2 className="font-medium">{a.title}</h2>
                <div className="mt-1 text-xs text-slate-500">{a.subsector_main ?? 'podsektor nieustalony'} · {fmtDateTime(a.created_at)}{isExpert && a.created_by ? ` · ${a.created_by}` : ''}</div>
                <div className="mt-2 flex flex-wrap gap-3 text-xs">
                  <span className="inline-flex items-center gap-1"><Users size={12} />{a.n_neighbours} podobnych inwestycji</span>
                  <span className="inline-flex items-center gap-1"><Flag size={12} />{a.n_flags} {a.n_flags === 1 ? 'flaga' : 'flag'}</span>
                  {a.status !== 'proposed' && <Badge variant={a.status === 'rejected' ? 'danger' : 'success'}>{a.status === 'rejected' ? 'odrzucona przez eksperta' : 'zatwierdzona przez eksperta'}</Badge>}
                </div>
              </Card>
            </Link>))}</div>
      )}</QueryState>
    </div>
  )
}
