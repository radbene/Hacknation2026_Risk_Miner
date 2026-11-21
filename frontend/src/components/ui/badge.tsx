import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const badgeVariants = cva('inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap', {
  variants: {
    variant: {
      default: 'border-transparent bg-slate-100 text-slate-700',
      brand: 'border-transparent bg-brand-soft text-brand',
      success: 'border-transparent bg-emerald-50 text-emerald-700',
      warning: 'border-transparent bg-amber-50 text-amber-800',
      danger: 'border-transparent bg-rose-50 text-rose-700',
      info: 'border-transparent bg-sky-50 text-sky-700',
      violet: 'border-transparent bg-violet-50 text-violet-700',
      outline: 'border-slate-200 text-slate-700',
    },
  },
  defaultVariants: { variant: 'default' },
})

export function Badge({ className, variant, ...props }: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
