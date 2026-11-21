import { CheckCircle2, Loader2, Play, XCircle } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, isFallback, unwrap, type Schemas } from '@/api/client'
import { Button, Dialog, useToast } from '@/components/ui'
import { fmtDateTime } from '@/lib/utils'
import { isMockJob, mockJob, mockStartJob } from '@/mocks'

const REPORT_LABEL: Record<string, string> = {
  projects: 'Projekty', queries: 'Zapytania', notices_found: 'Ogłoszenia znalezione', notices_new: 'Nowe ogłoszenia', notices_unchanged: 'Bez zmian',
  linked: 'Powiązane', uncertain: 'Niepewne', unlinked: 'Niepowiązane', events_proposed: 'Zaproponowane zdarzenia', errors: 'Błędy',
}

/** Starts a background job and shows progress + the run report (polls /api/jobs/{id}). */
export function JobRunner({ label, start, mockKind = 'enrich', mockParams = {}, icon, variant = 'default', invalidate = [] }: {
  label: ReactNode; start: () => Promise<Schemas['JobOut']>; mockKind?: string; mockParams?: Record<string, unknown>; icon?: ReactNode; variant?: 'default' | 'outline'; invalidate?: unknown[][]
}) {
  const [job, setJob] = useState<Schemas['JobOut'] | null>(null)
  const [open, setOpen] = useState(false)
  const [starting, setStarting] = useState(false)
  const { toast } = useToast()
  const qc = useQueryClient()

  useEffect(() => {
    if (!job || job.state === 'done' || job.state === 'failed') return
    const t = setInterval(async () => {
      let j: Schemas['JobOut'] | undefined
      if (isMockJob(job.id)) j = mockJob(job.id)
      else {
        try { j = unwrap(await api.GET('/api/jobs/{job_id}', { params: { path: { job_id: job.id } } })) } catch { /* keep polling */ }
      }
      if (j) {
        setJob(j)
        if (j.state === 'done') { invalidate.forEach((k) => qc.invalidateQueries({ queryKey: k })); toast({ kind: 'success', title: 'Zadanie zakończone', description: String(label) }) }
        if (j.state === 'failed') toast({ kind: 'error', title: 'Zadanie nie powiodło się', description: j.error ?? undefined })
      }
    }, 700)
    return () => clearInterval(t)
  }, [job, invalidate, qc, toast, label])

  async function run() {
    setStarting(true)
    try {
      let j: Schemas['JobOut']
      try { j = await start() } catch (e) { if (!isFallback(e)) throw e; j = mockStartJob(mockKind, mockParams) }
      setJob(j); setOpen(true)
    } catch (e) {
      toast({ kind: 'error', title: 'Nie udało się uruchomić', description: String(e) })
    } finally { setStarting(false) }
  }

  const running = job && (job.state === 'queued' || job.state === 'running')
  return (
    <>
      <Button variant={variant} onClick={running ? () => setOpen(true) : run} loading={starting}>
        {running ? <Loader2 size={14} className="animate-spin" /> : icon ?? <Play size={14} />}{running ? `${Math.round((job.progress ?? 0) * 100)}%` : label}
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)} title={label} description={job ? `Rozpoczęto ${fmtDateTime(job.started_at ?? job.created_at)}. Zadanie działa w tle.` : undefined}
        footer={<Button variant="outline" onClick={() => setOpen(false)}>Zamknij</Button>}>
        {job && <JobReport job={job} />}
      </Dialog>
    </>
  )
}

/** Run report in plain sentences (per job kind), no ids. */
export function JobReport({ job }: { job: Schemas['JobOut'] }) {
  const pct = Math.round((job.progress ?? 0) * 100)
  const r = (job.result ?? null) as Record<string, any> | null // eslint-disable-line @typescript-eslint/no-explicit-any
  const lines: string[] = []
  if (r && job.kind === 'enrich') {
    lines.push(`Sprawdzono ogłoszenia ${r.buyers ?? '?'} zamawiających (${r.requests ?? 0} zapytań do BZP${r.offline_nips?.length ? `; dla ${r.offline_nips.length} użyto zapasowej kopii BZP` : ''}).`)
    lines.push(`Ogłoszenia: ${r.notices ?? 0}, w tym nowe ${r.inserted ?? 0}, zmienione ${r.updated ?? 0}, bez zmian ${r.unchanged ?? 0}. Postępowania: ${r.procedures ?? 0}.`)
    const ls = r.link_summary ?? {}
    lines.push(`Dopasowanie projektów: ${ls.linked ?? 0} powiązanych, ${ls.uncertain ?? 0} niepewnych, ${ls.unlinked ?? 0} bez powiązania${ls.override ? `, ${ls.override} wg decyzji eksperta` : ''}. `)
  } else if (r && job.kind === 'harvest') {
    lines.push(`Wczytano ${(r.stored ?? 0).toLocaleString('pl-PL')} ogłoszeń (nowe ${(r.inserted ?? 0).toLocaleString('pl-PL')}), zbudowano ${(r.procedures ?? 0).toLocaleString('pl-PL')} postępowań i ${(r.auto_projects ?? 0).toLocaleString('pl-PL')} inwestycji do porównań.`)
  } else if (r && job.kind === 'llm_test') {
    lines.push(r.ok ? `Model odpowiada (czas odpowiedzi ${Math.round((r.latency_ms ?? 0) / 100) / 10} s): „${r.sample ?? ''}”` : `Model nie odpowiada: ${r.error ?? 'nieznany błąd'}`)
  } else if (r && job.kind === 'extract') {
    lines.push(`Wyliczono ${r.events ?? 0} zdarzeń dla ${r.projects?.length ?? 0} projektów.`)
  } else if (r) {
    for (const [k, v] of Object.entries(r)) if (typeof v === 'number') lines.push(`${REPORT_LABEL[k] ?? k}: ${v.toLocaleString('pl-PL')}`)
  }
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div className="flex items-center gap-2">
        {job.state === 'done' ? <CheckCircle2 className="text-emerald-600" size={18} /> : job.state === 'failed' ? <XCircle className="text-rose-600" size={18} /> : <Loader2 className="animate-spin text-brand" size={18} />}
        <span>{job.state === 'done' ? 'Zakończono' : job.state === 'failed' ? 'Nie udało się' : job.message ?? 'Czeka na rozpoczęcie…'}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full bg-brand transition-all" style={{ width: `${pct}%` }} />
      </div>
      {job.error && <p className="rounded bg-rose-50 p-2 text-xs text-rose-800">{job.error.split('\n').slice(-2).join(' ')}</p>}
      {lines.length > 0 && <ul className="list-disc space-y-1 pl-5">{lines.map((l, i) => <li key={i}>{l}</li>)}</ul>}
    </div>
  )
}
