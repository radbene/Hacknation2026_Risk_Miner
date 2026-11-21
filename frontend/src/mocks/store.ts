/** In-memory mock store: queries read from here, mock mutations write here (until backend routers exist). */
import type { Schemas } from '@/api/client'
import { allBundles, caseBundle, NOW } from './cases'
import { EVIDENCE } from './evidence'
import { uid } from './ids'
import { mockProjectItems } from './projects'

type S = Schemas
type Reviewable = { id: string; status: S['ReviewStatus']; confidence?: number | null; method?: string | null; evidence_ids?: string[];
  proposal?: Record<string, unknown> | null; reviewed_by?: string | null; reviewed_at?: string | null; exemplary?: boolean }

export const currentUser = () => localStorage.getItem('rm_user') || 'ekspert'

interface Indexed { type: S['QueueItem']['object_type']; obj: Reviewable; projectId?: string; projectCode?: string; title: string; summary?: string }

function index(): Map<string, Indexed> {
  const m = new Map<string, Indexed>()
  for (const b of allBundles()) {
    const pid = b.detail.id, code = b.detail.code
    for (const l of b.links) m.set(l.id, { type: 'project_procedure', obj: l, projectId: pid, projectCode: code,
      title: `Powiązanie ${code} → ${l.bzp_number ?? l.ocid}`, summary: l.procedure_title ?? undefined })
    for (const e of b.events) m.set(e.id, { type: 'event', obj: e, projectId: pid, projectCode: code, title: e.title ?? e.event_type, summary: e.cause ?? undefined })
    for (const c of b.contracts) {
      m.set(c.id, { type: 'contract', obj: c, projectId: pid, projectCode: code, title: `Umowa ${c.contractor?.name ?? ''}`.trim() })
      for (const ch of c.changes ?? []) m.set(ch.id, { type: 'contract_change', obj: ch, projectId: pid, projectCode: code,
        title: `Zmiana umowy nr ${ch.change_no} (${code})`, summary: ch.reason ?? ch.description ?? undefined })
    }
    for (const i of b.issues) m.set(i.id, { type: 'data_issue', obj: i, projectId: pid, projectCode: code, title: `Brak danych: ${i.field ?? i.kind}`, summary: i.message })
  }
  for (const p of mockProjectItems) m.set(p.id, { type: 'project', obj: p, projectId: p.id, projectCode: p.code, title: `Projekt ${p.code}`, summary: p.title })
  return m
}

const extraHistory: S['ReviewOut'][] = []

export function mockReview(objectType: string, objectId: string, body: S['ReviewActionIn']): S['ReviewOut'] {
  const it = index().get(objectId)
  const before = it ? { status: it.obj.status, ...(body.changes ? pick(it.obj, Object.keys(body.changes)) : {}) } : null
  if (it) {
    const o = it.obj as Reviewable & Record<string, unknown>
    if (body.action === 'accept') {
      if (body.accept_proposal && o.proposal) { Object.assign(o, stripMeta(o.proposal)); o.status = 'edited' } else o.status = 'approved'
      o.proposal = null
    } else if (body.action === 'edit') { Object.assign(o, body.changes ?? {}); o.status = 'edited' }
    else if (body.action === 'reject') o.status = 'rejected'
    else if (body.action === 'reopen') o.status = 'proposed'
    else if (body.action === 'exemplary') o.exemplary = true
    else if (body.action === 'unexemplary') o.exemplary = false
    o.reviewed_by = currentUser()
    o.reviewed_at = new Date().toISOString()
    syncProject(it.projectId)
  }
  const r: S['ReviewOut'] = { id: uid('review', objectId, Date.now()), object_type: objectType, object_id: objectId, action: body.action,
    before, after: it ? { status: it.obj.status, ...(body.changes ?? {}) } : null, comment: body.comment ?? null, reviewer: currentUser(), at: new Date().toISOString() }
  extraHistory.unshift(r)
  return r
}

export function mockBulkConfirm(body: S['BulkConfirmIn']): S['BulkResult'] {
  let confirmed = 0, skipped = 0
  for (const [id, it] of index()) {
    if (it.type !== body.object_type || it.obj.status !== 'proposed') continue
    if (body.project_id && it.projectId !== body.project_id) continue
    if (body.ids && !body.ids.includes(id)) continue
    if (body.min_confidence != null && (it.obj.confidence ?? 0) < body.min_confidence) { skipped++; continue }
    mockReview(it.type, id, { action: 'accept', comment: body.comment ?? 'Zatwierdzenie zbiorcze (pewność 1,0)', accept_proposal: false })
    confirmed++
  }
  return { confirmed, skipped }
}

export function mockQueue(q: { object_type?: string | null; project_id?: string | null; status?: string }): S['Page_QueueItem_'] {
  const status = q.status ?? 'proposed'
  const items: S['QueueItem'][] = []
  for (const [id, it] of index()) {
    if (it.type === 'project') continue
    if (status && it.obj.status !== status) continue
    if (q.object_type && it.type !== q.object_type) continue
    if (q.project_id && it.projectId !== q.project_id) continue
    const conf = it.obj.confidence ?? null
    items.push({ object_type: it.type, object_id: id, title: it.title, summary: it.summary ?? null, status: it.obj.status, method: it.obj.method ?? null,
      confidence: conf, uncertainty: conf == null ? 1 : 1 - conf, project_id: it.projectId ?? null, project_code: it.projectCode ?? null,
      evidence_ids: it.obj.evidence_ids ?? [], has_proposal: !!it.obj.proposal, created_at: NOW })
  }
  items.sort((a, b) => (b.uncertainty ?? 0) - (a.uncertainty ?? 0))
  return { items, total: items.length, offset: 0, limit: 200 }
}

export function mockQueueObject(id: string) { return index().get(id) }

export function mockHistory(q: { project_id?: string | null; object_id?: string | null }): S['Page_ReviewOut_'] {
  const idx = index()
  let items = [...extraHistory, ...allBundles().flatMap((b) => b.history)]
  if (q.object_id) items = items.filter((h) => h.object_id === q.object_id)
  if (q.project_id) items = items.filter((h) => h.object_id === q.project_id || idx.get(h.object_id)?.projectId === q.project_id)
  items.sort((a, b) => b.at.localeCompare(a.at))
  return { items, total: items.length, offset: 0, limit: 100 }
}

export function mockRelink(projectId: string, body: S['RelinkIn']): S['LinkOut'] {
  const b = caseBundle(projectId)!
  const cand = b.candidates.find((c) => (body.procedure_id && c.procedure_id === body.procedure_id) || (body.ocid && c.ocid === body.ocid) || (body.notice_number && c.bzp_number === body.notice_number))
  const old = b.links[0]
  const link: S['LinkOut'] = {
    id: uid('link', projectId, cand?.procedure_id ?? body.notice_number ?? body.ocid ?? 'x'), project_id: projectId, project_code: b.detail.code,
    procedure_id: cand?.procedure_id ?? uid('procedure', body.ocid ?? body.notice_number ?? ''), ocid: cand?.ocid ?? body.ocid ?? null,
    bzp_number: cand?.bzp_number ?? body.notice_number ?? null, procedure_title: cand?.title ?? '(pobieranie ogłoszenia…)', part_no: body.part_no ?? null,
    components: cand?.components ?? [], alternatives: b.candidates.filter((c) => c !== cand), is_override: true, rank: 1,
    status: 'approved', method: 'expert', confidence: 1, evidence_ids: [], reviewed_by: currentUser(), reviewed_at: new Date().toISOString(),
  }
  b.links = [link]
  const p = mockProjectItems.find((x) => x.id === projectId)
  if (p) { p.link_status = 'linked'; p.method = 'expert'; p.confidence = 1 }
  extraHistory.unshift({ id: uid('review', link.id, Date.now()), object_type: 'project_procedure', object_id: link.id, action: 'relink',
    before: old ? { procedure_id: old.procedure_id, bzp_number: old.bzp_number, confidence: old.confidence } : null,
    after: { procedure_id: link.procedure_id, bzp_number: link.bzp_number }, comment: body.comment ?? null, reviewer: currentUser(), at: new Date().toISOString() })
  return link
}

export function mockPatchProject(projectId: string, body: S['ProjectPatch']): S['ProjectDetail'] {
  const b = caseBundle(projectId)!
  const before = pick(b.detail as unknown as Record<string, unknown>, Object.keys(body.changes))
  Object.assign(b.detail, body.changes, { status: 'edited', reviewed_by: currentUser(), reviewed_at: new Date().toISOString() })
  const p = mockProjectItems.find((x) => x.id === projectId)
  if (p) Object.assign(p, pick(body.changes, Object.keys(p)), { status: 'edited' })
  extraHistory.unshift({ id: uid('review', projectId, Date.now()), object_type: 'project', object_id: projectId, action: 'edit', before, after: body.changes,
    comment: body.comment ?? null, reviewer: currentUser(), at: new Date().toISOString() })
  return b.detail
}

export function mockEvidence(ids: string[]): S['EvidenceOut'][] {
  return ids.map((id) => EVIDENCE.get(id)).filter((x): x is S['EvidenceOut'] => !!x)
}

function syncProject(projectId?: string) {
  if (!projectId) return
  const b = caseBundle(projectId)
  const p = mockProjectItems.find((x) => x.id === projectId)
  if (!b || !p) return
  const pending = [...b.events, ...b.links, ...b.issues, ...b.contracts.flatMap((c) => [c, ...(c.changes ?? [])])].filter((x) => x.status === 'proposed').length
  p.n_pending_review = pending
  b.detail.n_pending_review = pending
  const l = b.links[0]
  if (l) p.link_status = l.status === 'rejected' ? 'rejected' : l.status === 'proposed' && (l.confidence ?? 0) < 0.8 ? 'uncertain' : 'linked'
  b.detail.link_status = p.link_status
}

function pick(o: Record<string, unknown>, keys: string[]) {
  return Object.fromEntries(keys.filter((k) => k in o).map((k) => [k, o[k]]))
}
function stripMeta(p: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(p).filter(([k]) => !k.startsWith('_')))
}
