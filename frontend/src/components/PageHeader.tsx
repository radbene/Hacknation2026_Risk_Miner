import { useRouter } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'

export function PageHeader({ title, description, actions, back, children }: { title: ReactNode; description?: ReactNode; actions?: ReactNode; back?: boolean; children?: ReactNode }) {
  const router = useRouter()
  return (
    <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        {back && <button onClick={() => router.history.back()} className="mb-1 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-brand cursor-pointer"><ArrowLeft size={12} />Wstecz</button>}
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-sm text-slate-600">{description}</p>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  )
}
