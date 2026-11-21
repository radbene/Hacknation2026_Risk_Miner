import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const badgeVariants = cva('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap', {
  variants: {
    variant: {
      default: 'border-transparent bg-slate-100 text-slate-700',
      brand: 'border-transparent bg-brand-soft text-brand',
      success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
      warning: 'border-amber-200 bg-amber-50 text-amber-800',
      danger: 'border-rose-200 bg-rose-50 text-rose-800',
      info: 'border-sky-200 bg-sky-50 text-sky-800',
      violet: 'border-violet-200 bg-violet-50 text-violet-800',
      outline: 'border-slate-300 text-slate-700',
    },
  },
  defaultVariants: { variant: 'default' },
})

export function Badge({ className, variant, ...props }: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
