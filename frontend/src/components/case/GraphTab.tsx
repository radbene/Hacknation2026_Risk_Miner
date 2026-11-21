import { Background, Controls, ReactFlow, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useMemo } from 'react'
import { useGraph } from '@/api/cases'
import type { Schemas } from '@/api/client'
import { QueryState } from '@/components/ui'

const COL: Record<string, number> = { entity: 0, project: 1, procedure: 2, document: 2, notice: 3, contract: 3, change: 4, event: 5, source: 5 }
const COLOR: Record<string, string> = {
  project: '#1e3a8a', entity: '#0f766e', procedure: '#7c3aed', notice: '#64748b', contract: '#0369a1', change: '#b45309', event: '#be123c',
  document: '#475569', source: '#475569',
}
const TYPE_PL: Record<string, string> = {
  project: 'projekt', entity: 'podmiot', procedure: 'postępowanie', notice: 'ogłoszenie', contract: 'umowa', change: 'zmiana', event: 'zdarzenie',
  document: 'dokument', source: 'źródło',
}

export function GraphTab({ projectId }: { projectId: string }) {
  const g = useGraph(projectId)
  return <QueryState q={g} empty={(d) => d.nodes.length === 0}>{(d) => <Graph g={d} />}</QueryState>
}

function Graph({ g }: { g: Schemas['GraphOut'] }) {
  const { nodes, edges } = useMemo(() => {
    const rows: Record<number, number> = {}
    const nodes: Node[] = g.nodes.map((n) => {
      const c = COL[n.type] ?? 5
      const r = (rows[c] = (rows[c] ?? -1) + 1)
      return {
        id: n.id, position: { x: c * 230, y: r * 74 },
        data: { label: <div className="text-left"><div className="text-[9px] uppercase opacity-70">{TYPE_PL[n.type] ?? n.type}</div><div className="line-clamp-2 text-[11px] font-medium">{n.label}</div></div> },
        style: { borderColor: COLOR[n.type] ?? '#64748b', borderWidth: 1.5, width: 200, padding: 6, fontSize: 11 },
      }
    })
    const edges: Edge[] = g.edges.map((e, i) => ({
      id: `e${i}`, source: e.source, target: e.target,
      label: e.confidence != null ? `${e.label ?? ''} ${e.method ?? ''} ${e.confidence.toFixed(2)}`.trim() : e.label ?? undefined,
      style: { stroke: e.status === 'rejected' ? '#e11d48' : '#94a3b8', strokeDasharray: e.status === 'proposed' && e.confidence != null ? '4 3' : undefined },
      labelStyle: { fontSize: 9 },
    }))
    return { nodes, edges }
  }, [g])
  return (
    <div>
      <p className="mb-2 text-xs text-slate-500">Projekt ↔ beneficjent ↔ postępowania ↔ ogłoszenia ↔ umowy ↔ zmiany ↔ zdarzenia. Linia przerywana = powiązanie zaproponowane przez system, czerwona = odrzucone.</p>
      <div className="h-[560px] rounded-lg border border-slate-200 bg-white">
        <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable proOptions={{ hideAttribution: true }}>
          <Background /><Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  )
}
