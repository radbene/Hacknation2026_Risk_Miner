import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const buttonVariants = cva(
  'press inline-flex items-center justify-center gap-2 whitespace-nowrap border-2 border-ink text-sm font-semibold ' +
    'outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand [&_svg]:shrink-0 ' +
    'disabled:pointer-events-none disabled:opacity-50 cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-brand text-white shadow-sm hover:shadow-md',
        secondary: 'bg-slate-100 text-ink shadow-sm hover:shadow-md',
        outline: 'bg-surface text-ink shadow-sm hover:shadow-md',
        ghost: 'border-transparent text-ink hover:border-ink hover:bg-surface',
        success: 'bg-emerald-600 text-white shadow-sm hover:shadow-md',
        danger: 'bg-rose-600 text-white shadow-sm hover:shadow-md',
        link: 'text-brand underline-offset-2 hover:underline px-0',
      },
      size: { sm: 'h-8 gap-1.5 px-3 text-xs', md: 'h-10 px-4', lg: 'h-12 px-6 text-base', icon: 'h-9 w-9' },
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
