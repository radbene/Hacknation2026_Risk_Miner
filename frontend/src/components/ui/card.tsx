import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('rounded-lg border border-slate-200 bg-white shadow-sm', className)} {...p} />
}
export function CardHeader({ title, description, actions, className, children }:
  { title?: ReactNode; description?: ReactNode; actions?: ReactNode; className?: string; children?: ReactNode }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 px-4 py-3', className)}>
      <div className="min-w-0">
        {title && <h2 className="text-sm font-semibold text-slate-900">{title}</h2>}
        {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}
export function CardContent({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-4 py-3', className)} {...p} />
}
