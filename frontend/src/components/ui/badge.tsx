import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const badgeVariants = cva('inline-flex items-center gap-1 border px-1.5 py-px font-mono text-[11px] font-medium uppercase tracking-wide whitespace-nowrap', {
  variants: {
    variant: {
      default: 'border-ink bg-surface text-ink',
      brand: 'border-brand bg-brand-soft text-brand',
      success: 'border-emerald-700 bg-emerald-50 text-emerald-800',
      warning: 'border-amber-700 bg-amber-50 text-amber-900',
      danger: 'border-rose-700 bg-rose-50 text-rose-800',
      info: 'border-sky-700 bg-sky-50 text-sky-800',
      violet: 'border-violet-700 bg-violet-50 text-violet-800',
      outline: 'border-ink text-ink',
    },
  },
  defaultVariants: { variant: 'default' },
})

export function Badge({ className, variant, ...props }: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
