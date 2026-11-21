import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const PLN = new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'PLN', maximumFractionDigits: 2 })
const NUM = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 2 })
const PCT = new Intl.NumberFormat('pl-PL', { style: 'percent', maximumFractionDigits: 0 })

export const fmtPln = (v?: number | null) => (v == null ? '—' : PLN.format(v))
export const fmtNum = (v?: number | null, digits = 2) =>
  v == null ? '—' : new Intl.NumberFormat('pl-PL', { maximumFractionDigits: digits }).format(v)
export const fmtPct = (v?: number | null) => (v == null ? '—' : PCT.format(v))
export { NUM }

export function fmtDate(v?: string | null) {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  return d.toLocaleDateString('pl-PL', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

export function fmtDateTime(v?: string | null) {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  return d.toLocaleString('pl-PL', { dateStyle: 'short', timeStyle: 'short' })
}

export function download(filename: string, content: string, mime = 'application/json') {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function toCsv(rows: Record<string, unknown>[]): string {
  if (!rows.length) return ''
  const cols = Array.from(new Set(rows.flatMap((r) => Object.keys(r))))
  const esc = (v: unknown) => {
    const s = v == null ? '' : typeof v === 'object' ? JSON.stringify(v) : String(v)
    return /[",;\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  return [cols.join(','), ...rows.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n')
}
