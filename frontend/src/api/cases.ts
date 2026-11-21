/** Query hooks for the case base (Area 2), each with a mock fallback. */
import { api, unwrap, type Schemas } from './client'
import { useApi } from './hooks'
import { caseBundle, mockChunks, mockDocuments, mockHistory, mockProjects } from '@/mocks'

const P = (id: string) => ({ params: { path: { project_id: id } } })
const EMPTY_GRAPH: Schemas['GraphOut'] = { nodes: [], edges: [] }

export interface ProjectFilters { q?: string; tier?: string; subsector?: string; link_status?: string; pending?: boolean }

export function useProjects(f: ProjectFilters) {
  return useApi(['projects', f], async () => {
    const r = unwrap(await api.GET('/api/projects', { params: { query: { q: f.q || null, tier: f.tier || null, subsector: f.subsector || null, link_status: f.link_status || null, limit: 200 } } }))
    return f.pending ? { ...r, items: r.items.filter((p) => p.n_pending_review > 0) } : r
  }, () => mockProjects(f))
}
export const useProject = (id: string) =>
  useApi(['project', id], async () => unwrap(await api.GET('/api/projects/{project_id}', P(id))), () => caseBundle(id)?.detail)
export const useTimeline = (id: string) =>
  useApi(['project', id, 'timeline'], async () => unwrap(await api.GET('/api/projects/{project_id}/timeline', P(id))),
    () => caseBundle(id)?.timeline ?? { project_id: id, items: [], planned_vs_actual: {} })
export const useGraph = (id: string) =>
  useApi(['project', id, 'graph'], async () => unwrap(await api.GET('/api/projects/{project_id}/graph', P(id))), () => caseBundle(id)?.graph ?? EMPTY_GRAPH)
export const useProcedures = (id: string) =>
  useApi(['project', id, 'procedures'], async () => unwrap(await api.GET('/api/projects/{project_id}/procedures', P(id))), () => caseBundle(id)?.procedures ?? [])
export const useContracts = (id: string) =>
  useApi(['project', id, 'contracts'], async () => unwrap(await api.GET('/api/projects/{project_id}/contracts', P(id))), () => caseBundle(id)?.contracts ?? [])
export const useNotices = (id: string) =>
  useApi(['project', id, 'notices'], async () => unwrap(await api.GET('/api/projects/{project_id}/notices', P(id))), () => caseBundle(id)?.notices ?? [])
export const useCandidates = (id: string) =>
  useApi(['project', id, 'candidates'], async () => unwrap(await api.GET('/api/projects/{project_id}/candidates', P(id))), () => caseBundle(id)?.candidates ?? [])
export const useIssues = (id: string) =>
  useApi(['project', id, 'issues'], async () => unwrap(await api.GET('/api/projects/{project_id}/issues', P(id))), () => caseBundle(id)?.issues ?? [])
export const useLinks = (projectId: string) =>
  useApi(['links', projectId], async () => unwrap(await api.GET('/api/links', { params: { query: { project_id: projectId } } })).items,
    () => caseBundle(projectId)?.links ?? [])
export const useEvents = (projectId: string) =>
  useApi(['events', projectId], async () => unwrap(await api.GET('/api/events', { params: { query: { project_id: projectId } } })).items,
    () => caseBundle(projectId)?.events ?? [])
export const useHistory = (projectId: string) =>
  useApi(['history', projectId], async () => unwrap(await api.GET('/api/history', { params: { query: { project_id: projectId } } })).items,
    () => mockHistory({ project_id: projectId }).items)
export const useDocuments = (projectId?: string, analysisId?: string) =>
  useApi(['documents', projectId ?? '', analysisId ?? ''], async () => unwrap(await api.GET('/api/documents', { params: { query: { project_id: projectId ?? null, analysis_id: analysisId ?? null } } })),
    () => mockDocuments.filter((d) => (!projectId || d.project_id === projectId) && (!analysisId || d.analysis_id === analysisId)))
export const useDocument = (id: string) =>
  useApi(['document', id], async () => unwrap(await api.GET('/api/documents/{document_id}', { params: { path: { document_id: id } } })),
    () => mockDocuments.find((d) => d.id === id))
export const useChunks = (id: string) =>
  useApi(['document', id, 'chunks'], async () => unwrap(await api.GET('/api/documents/{document_id}/chunks', { params: { path: { document_id: id } } })),
    () => mockChunks[id] ?? [])
