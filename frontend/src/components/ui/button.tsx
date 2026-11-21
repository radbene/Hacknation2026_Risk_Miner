import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors duration-150 ' +
    'outline-none focus-visible:ring-[3px] focus-visible:ring-brand/30 [&_svg]:shrink-0 ' +
    'disabled:pointer-events-none disabled:opacity-50 cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-brand text-white shadow-xs hover:bg-brand/90',
        secondary: 'bg-slate-100 text-slate-900 shadow-xs hover:bg-slate-200/80',
        outline: 'border border-slate-200 bg-white text-slate-900 shadow-xs hover:bg-slate-100',
        ghost: 'text-slate-700 hover:bg-slate-100 hover:text-slate-900',
        success: 'bg-emerald-600 text-white shadow-xs hover:bg-emerald-600/90',
        danger: 'bg-rose-600 text-white shadow-xs hover:bg-rose-600/90',
        link: 'text-brand underline-offset-2 hover:underline px-0',
      },
      size: { sm: 'h-8 gap-1.5 px-3 text-xs', md: 'h-9 px-4', lg: 'h-10 px-6', icon: 'h-9 w-9' },
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
