import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('rounded-xl border border-slate-200 bg-white text-slate-950 shadow-xs', className)} {...p} />
}
export function CardHeader({ title, description, actions, className, children }:
  { title?: ReactNode; description?: ReactNode; actions?: ReactNode; className?: string; children?: ReactNode }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-2 px-5 pt-4 pb-2', className)}>
      <div className="min-w-0">
        {title && <h2 className="font-semibold leading-snug tracking-tight text-slate-950">{title}</h2>}
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}
export function CardContent({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-5 pb-4 pt-2', className)} {...p} />
}
