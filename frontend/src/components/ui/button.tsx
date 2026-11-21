import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md text-sm font-medium transition-colors ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-1 ' +
    'disabled:pointer-events-none disabled:opacity-50 cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-brand text-white hover:bg-brand/90',
        secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200',
        outline: 'border border-slate-300 bg-white hover:bg-slate-50',
        ghost: 'hover:bg-slate-100',
        success: 'bg-emerald-600 text-white hover:bg-emerald-700',
        danger: 'bg-rose-600 text-white hover:bg-rose-700',
        link: 'text-brand underline-offset-2 hover:underline px-0',
      },
      size: { sm: 'h-7 px-2.5 text-xs', md: 'h-9 px-3.5', lg: 'h-10 px-5', icon: 'h-8 w-8' },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  },
)

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, type = 'button', ...props }, ref) => (
    <button ref={ref} type={type} className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading} aria-busy={loading || undefined} {...props}>
      {loading && <Loader2 className="animate-spin" size={14} aria-hidden />}
      {children}
    </button>
  ),
)
Button.displayName = 'Button'
