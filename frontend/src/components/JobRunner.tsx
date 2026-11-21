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
      <Dialog open={open} onClose={() => setOpen(false)} title={<>{label} – przebieg</>} description={job ? `Zadanie ${job.kind} · ${job.id.slice(0, 8)} · start ${fmtDateTime(job.started_at ?? job.created_at)}` : undefined}
        footer={<Button variant="outline" onClick={() => setOpen(false)}>Zamknij</Button>}>
        {job && <JobReport job={job} />}
      </Dialog>
    </>
  )
}

export function JobReport({ job }: { job: Schemas['JobOut'] }) {
  const pct = Math.round((job.progress ?? 0) * 100)
  const r = job.result as Record<string, unknown> | null | undefined
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div className="flex items-center gap-2">
        {job.state === 'done' ? <CheckCircle2 className="text-emerald-600" size={18} /> : job.state === 'failed' ? <XCircle className="text-rose-600" size={18} /> : <Loader2 className="animate-spin text-brand" size={18} />}
        <span>{job.state === 'done' ? 'Zakończono' : job.state === 'failed' ? 'Błąd' : job.message ?? 'W kolejce…'}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full bg-brand transition-all" style={{ width: `${pct}%` }} />
      </div>
      {job.error && <pre className="whitespace-pre-wrap rounded bg-rose-50 p-2 text-xs text-rose-800">{job.error}</pre>}
      {r && (
        <div>
          <h3 className="mb-2 text-sm font-semibold">Raport z przebiegu</h3>
          <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(r).filter(([, v]) => typeof v === 'number').map(([k, v]) => (
              <div key={k} className="rounded border border-slate-200 p-2"><dt className="text-xs text-slate-500">{REPORT_LABEL[k] ?? k}</dt>
                <dd className="text-lg font-semibold tabular-nums">{(v as number).toLocaleString('pl-PL')}</dd></div>
            ))}
          </dl>
          {typeof r.by_source === 'object' && r.by_source && (
            <table className="mt-3 w-full text-xs"><thead className="text-left text-slate-500"><tr><th>Źródło</th><th>Zapytania</th><th>OK</th><th>Błędy</th><th>Uwagi</th></tr></thead>
              <tbody>{Object.entries(r.by_source as Record<string, Record<string, unknown>>).map(([k, v]) => (
                <tr key={k} className="border-t border-slate-100"><td className="py-1 font-medium">{k}</td><td>{String(v.queries ?? '')}</td><td>{String(v.ok ?? '')}</td><td>{String(v.errors ?? '')}</td><td>{String(v.note ?? '')}</td></tr>
              ))}</tbody></table>
          )}
          {typeof r.idempotent === 'string' && <p className="mt-2 text-xs text-emerald-700">{r.idempotent}</p>}
        </div>
      )}
    </div>
  )
}
