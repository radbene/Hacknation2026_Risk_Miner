import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from './button'

export function Loading({ label = 'Wczytywanie…' }: { label?: string }) {
  return <div role="status" className="flex items-center gap-2 py-8 text-sm text-slate-500"><Loader2 className="animate-spin" size={16} />{label}</div>
}
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
      <div className="flex-1">Nie udało się wczytać danych. <span className="text-xs text-rose-700">{error instanceof Error ? error.message : String(error)}</span></div>
      {onRetry && <Button size="sm" variant="outline" onClick={onRetry}>Ponów</Button>}
    </div>
  )
}
export function Empty({ children = 'Brak danych.', icon }: { children?: ReactNode; icon?: ReactNode }) {
  return <div className="flex flex-col items-center gap-2 py-8 text-sm text-slate-500">{icon ?? <Inbox size={20} />}{children}</div>
}

/** Renders loading / error / content for a TanStack Query result. */
export function QueryState<T>({ q, children, empty }: { q: { data?: T; isLoading: boolean; error: unknown; refetch: () => unknown }; children: (d: T) => ReactNode; empty?: (d: T) => boolean }) {
  if (q.isLoading) return <Loading />
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />
  if (q.data === undefined) return <Empty />
  if (empty?.(q.data)) return <Empty />
  return <>{children(q.data)}</>
}
