import { Check, CircleDashed, PencilLine, X } from 'lucide-react'
import { Badge } from '@/components/ui'
import { STATUS_LABEL } from '@/lib/labels'

const V = { proposed: 'warning', approved: 'success', edited: 'info', rejected: 'danger' } as const
const I = { proposed: CircleDashed, approved: Check, edited: PencilLine, rejected: X }

export function StatusBadge({ status }: { status?: string | null }) {
  const s = (status ?? 'proposed') as keyof typeof V
  const Icon = I[s] ?? CircleDashed
  return <Badge variant={V[s] ?? 'default'} title={`Status: ${STATUS_LABEL[s] ?? s}`}><Icon size={11} aria-hidden />{STATUS_LABEL[s] ?? s}</Badge>
}
