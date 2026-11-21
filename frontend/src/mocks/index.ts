/** Mock data in the shape of the API contract, used while backend routers return 501. */
import type { Schemas } from '@/api/client'
import { mockProjectItems } from './projects'

export * from './cases'
export * from './documents'
export * from './jobs'
export * from './evidence'
export * from './projects'
export * from './store'

export function mockProjects(q: { q?: string | null; tier?: string | null; subsector?: string | null; link_status?: string | null; pending?: boolean }): Schemas['Page_ProjectListItem_'] {
  let items = mockProjectItems
  if (q.tier) items = items.filter((p) => p.tier === q.tier)
  if (q.subsector) items = items.filter((p) => p.subsector_main === q.subsector || p.subsector_extra?.includes(q.subsector!))
  if (q.link_status) items = items.filter((p) => p.link_status === q.link_status)
  if (q.pending) items = items.filter((p) => p.n_pending_review > 0)
  if (q.q) {
    const s = q.q.toLowerCase()
    items = items.filter((p) => [p.code, p.title, p.beneficiary_name, p.public_id_value, p.beneficiary_nip].some((v) => v?.toLowerCase().includes(s)))
  }
  return { items, total: items.length, offset: 0, limit: 50 }
}
