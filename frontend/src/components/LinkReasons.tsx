/** Why a project was linked to a BZP procedure – in plain words, no raw scores. */
import { Check, CircleHelp, X } from 'lucide-react'
import type { Schemas } from '@/api/client'
import { EvidenceChip } from '@/components/evidence/EvidenceChip'
import { confidenceWords } from '@/components/Visual'
import { cn } from '@/lib/utils'

const QUESTION: Record<string, string> = {
  kpo_ref: 'Numer projektu KPO z listy występuje w ogłoszeniu',
  notice_no: 'Numer ogłoszenia z listy istnieje w BZP',
  nip: 'NIP zamawiającego zgadza się z NIP-em beneficjenta',
  ocid: 'To samo postępowanie (wspólny identyfikator ogłoszeń)',
  xref: 'Inne ogłoszenia tego postępowania odwołują się do numeru z listy',
  title: 'Nazwa zamówienia podobna do nazwy projektu',
  cpv: 'Kod CPV dotyczy robót wodno-kanalizacyjnych',
  date: 'Data ogłoszenia pasuje do okresu projektu',
  value: 'Wartość umowy zbliżona do wartości projektu',
  location: 'Wspólne nazwy miejscowości w opisie',
  lot: 'Właściwa część zamówienia (dla projektów obejmujących część)',
  scope: 'Zakres (km, przyłącza) porównywalny',
  consistency: 'Stan realizacji zgodny (np. „zakończone” i jest ogłoszenie o wykonaniu)',
  expert: 'Powiązanie wskazane przez eksperta',
}
export const METHOD_SENTENCE: Record<string, string> = {
  kpo_ref: 'po numerze projektu KPO podanym w ogłoszeniu',
  notice_no: 'po numerze ogłoszenia z listy organizatora',
  xref: 'przez odwołania między ogłoszeniami (numer z listy pojawia się w innych ogłoszeniach tego postępowania)',
  fuzzy: 'po podobieństwie nazwy, miejsca, daty i wartości (bez wspólnego numeru)',
  ocid: 'jako to samo postępowanie',
  expert: 'decyzją eksperta',
  harvest: 'automatycznie z BZP (jedno postępowanie = jedna inwestycja)',
}

export function LinkReasons({ comps, compact }: { comps?: Schemas['LinkComponent'][] | null; compact?: boolean }) {
  if (!comps?.length) return null
  return (
    <ul className={cn('space-y-1.5 text-sm', compact && 'text-xs')}>
      {comps.map((c, i) => {
        const ok = c.score >= 0.8, partly = c.score >= 0.5 && !ok
        const Icon = ok ? Check : partly ? CircleHelp : X
        return (
          <li key={i} className="flex items-start gap-2">
            <Icon size={15} className={cn('mt-0.5 shrink-0', ok ? 'text-emerald-600' : partly ? 'text-amber-600' : 'text-rose-500')} aria-hidden />
            <div className="min-w-0">
              <span className="font-medium">{QUESTION[c.name] ?? c.name}</span>
              <span className="text-slate-500"> – {ok ? 'tak' : partly ? 'częściowo' : 'nie'}</span>
              {c.detail && <div className="text-xs text-slate-500">{c.detail}</div>}
            </div>
            {c.evidence_id && <EvidenceChip ids={[c.evidence_id]} className="ml-auto shrink-0" />}
          </li>)
      })}
    </ul>
  )
}

export function LinkVerdict({ method, confidence }: { method?: string | null; confidence?: number | null }) {
  return (
    <span className="text-sm text-slate-700">Dopasowano {METHOD_SENTENCE[method ?? ''] ?? 'automatycznie'}; pewność <b>{confidenceWords(confidence)}</b>.</span>
  )
}
