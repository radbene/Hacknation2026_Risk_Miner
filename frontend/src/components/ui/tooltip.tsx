import { useId, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** CSS tooltip shown on hover and keyboard focus; content is linked via aria-describedby. */
export function Tooltip({ content, children, className, side = 'top' }:
  { content: ReactNode; children: ReactNode; className?: string; side?: 'top' | 'bottom' }) {
  const id = useId()
  return (
    <span className={cn('group relative inline-flex', className)} aria-describedby={id}>
      {children}
      <span role="tooltip" id={id}
        className={cn('pointer-events-none absolute left-1/2 z-50 w-max max-w-xs -translate-x-1/2 rounded bg-slate-900 px-2 py-1',
          'text-xs font-normal text-white opacity-0 shadow transition-opacity group-hover:opacity-100 group-focus-within:opacity-100',
          side === 'top' ? 'bottom-full mb-1' : 'top-full mt-1')}>
        {content}
      </span>
    </span>
  )
}
