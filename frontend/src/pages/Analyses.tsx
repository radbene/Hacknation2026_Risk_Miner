import { Link, useNavigate } from '@tanstack/react-router'
import { Plus } from 'lucide-react'
import { api, unwrap, type Schemas } from '@/api/client'
import { useApi } from '@/api/hooks'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { Badge, Button, DataTable, QueryState, type ColumnDef } from '@/components/ui'
import { fmtDateTime } from '@/lib/utils'
import { analysesRoute } from '@/router'

type L = Schemas['AnalysisListItem']

export default function Analyses() {
  const s = analysesRoute.useSearch()
  const navigate = useNavigate()
  const q = useApi(['analyses', s], async () => unwrap(await api.GET('/api/analyses', { params: { query: { q: s.q ?? null, status: s.status ?? null, subsector: s.subsector ?? null, limit: 200 } } })))
  return (
    <div>
      <PageHeader title="Analizy nowych inwestycji" description="Zapisane analizy – każdą można otworzyć, zmienić cechy, wykluczyć sąsiadów i wyeksportować (DOCX, JSON, CSV)."
        actions={<Link to="/nowa-inwestycja"><Button><Plus size={14} />Nowa analiza</Button></Link>} />
      <QueryState q={q}>{(d) => (
        <DataTable data={d.items} getRowId={(r) => r.id} onRowClick={(r) => navigate({ to: '/analizy/$analysisId', params: { analysisId: r.id }, search: {} })}
          empty="Brak analiz – utwórz pierwszą w „Nowa inwestycja”."
          columns={[
            { accessorKey: 'title', header: 'Analiza', cell: ({ getValue }) => <span className="font-medium">{String(getValue())}</span> },
            { accessorKey: 'subsector_main', header: 'Podsektor', cell: ({ getValue }) => <span className="text-xs">{String(getValue() ?? '—')}</span> },
            { accessorKey: 'n_neighbours', header: 'Sąsiedzi' },
            { accessorKey: 'n_flags', header: 'Flagi', cell: ({ getValue }) => <Badge variant={Number(getValue()) ? 'warning' : 'default'}>{String(getValue())}</Badge> },
            { accessorKey: 'created_by', header: 'Autor' },
            { accessorKey: 'created_at', header: 'Utworzono', cell: ({ getValue }) => <span className="text-xs">{fmtDateTime(getValue() as string)}</span> },
            { accessorKey: 'status', header: 'Status', cell: ({ getValue }) => <StatusBadge status={getValue() as string} /> },
          ] as ColumnDef<L>[]} />
      )}</QueryState>
    </div>
  )
}
