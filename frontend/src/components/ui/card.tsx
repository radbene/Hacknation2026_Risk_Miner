import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('border-2 border-ink bg-surface text-ink shadow-md', className)} {...p} />
}
export function CardHeader({ title, description, actions, className, children }:
  { title?: ReactNode; description?: ReactNode; actions?: ReactNode; className?: string; children?: ReactNode }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-2 border-b-2 border-ink px-5 py-3', className)}>
      <div className="min-w-0">
        {title && <h2 className="text-[17px] font-bold leading-snug tracking-tight text-ink">{title}</h2>}
        {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
        {children}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}
export function CardContent({ className, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-5 py-4', className)} {...p} />
}
