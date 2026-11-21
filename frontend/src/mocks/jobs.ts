/** Simulated jobs for mock mode (enrich / extract / harvest): progress advances with wall-clock time. */
import type { Schemas } from '@/api/client'
import { uid } from './ids'
import { mockProjectItems } from './projects'

const JOBS = new Map<string, { job: Schemas['JobOut']; start: number; duration: number; result: Record<string, unknown> }>()

export function mockStartJob(kind: string, params: Record<string, unknown>): Schemas['JobOut'] {
  const id = uid('job', kind, Date.now())
  const now = new Date().toISOString()
  const job: Schemas['JobOut'] = { id, kind, params, state: 'queued', progress: 0, created_at: now, created_by: localStorage.getItem('rm_user') || 'ekspert' }
  JOBS.set(id, { job, start: Date.now(), duration: 4500, result: enrichReport(params) })
  return job
}

export function isMockJob(id: string) { return JOBS.has(id) }

export function mockJob(id: string): Schemas['JobOut'] | undefined {
  const j = JOBS.get(id)
  if (!j) return undefined
  const p = Math.min(1, (Date.now() - j.start) / j.duration)
  const steps = ['Zapytania do BZP (lustro, własny User-Agent)…', 'Parsowanie sekcji ogłoszeń…', 'Łączenie: klucze → łańcuch ogłoszeń → kandydaci…',
    'Biała lista VAT…', 'Zdarzenia z reguł i przyczyny…', 'Raport z przebiegu']
  return {
    ...j.job, state: p >= 1 ? 'done' : 'running', progress: p, message: steps[Math.min(steps.length - 1, Math.floor(p * steps.length))],
    started_at: new Date(j.start).toISOString(), finished_at: p >= 1 ? new Date(j.start + j.duration).toISOString() : null, result: p >= 1 ? j.result : null,
  }
}

function enrichReport(params: Record<string, unknown>) {
  const ids = (params.project_ids as string[] | null) ?? null
  const n = ids ? ids.length : mockProjectItems.length
  return {
    projects: n, queries: n * 9, notices_found: ids ? 5 * n : 988, notices_new: 0, notices_unchanged: ids ? 5 * n : 988,
    linked: ids ? n : 20, uncertain: ids ? 0 : 2, unlinked: 0, events_proposed: ids ? 3 * n : 61, errors: 0,
    by_source: { bzp: { queries: n * 7, ok: n * 7, errors: 0 }, vat_whitelist: { queries: n, ok: n, errors: 0 }, ted: { queries: n, ok: n, errors: 0, note: 'sprawdzono: brak (postępowania krajowe)' } },
    idempotent: 'Ponowne uruchomienie: 0 duplikatów, decyzje eksperta zachowane',
  }
}
