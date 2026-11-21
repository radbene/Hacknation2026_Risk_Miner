import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes, type LabelHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

const field = 'w-full rounded-md border border-slate-200 bg-white px-3 text-sm shadow-xs transition-[color,box-shadow] placeholder:text-slate-400 ' +
  'outline-none focus-visible:border-brand focus-visible:ring-[3px] focus-visible:ring-brand/20 disabled:bg-slate-50 disabled:text-slate-500'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(({ className, ...p }, ref) => (
  <input ref={ref} className={cn(field, 'h-9', className)} {...p} />
))
Input.displayName = 'Input'

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...p }, ref) => (
  <textarea ref={ref} className={cn(field, 'min-h-20 py-2', className)} {...p} />
))
Textarea.displayName = 'Textarea'

export interface SelectOption { value: string; label: string }
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement> & { options: SelectOption[]; placeholder?: string }>(
  ({ className, options, placeholder, ...p }, ref) => (
    <select ref={ref} className={cn(field, 'h-9 pr-7', className)} {...p}>
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  ),
)
Select.displayName = 'Select'

export function Label({ className, ...p }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn('mb-1.5 block text-sm font-medium text-slate-900', className)} {...p} />
}
