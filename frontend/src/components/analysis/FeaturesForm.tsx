import type { Schemas } from '@/api/client'
import { Badge, Input, Label, Select } from '@/components/ui'
import { SUBSECTORS } from '@/lib/labels'

export type Features = Schemas['Features']
type FV = Schemas['FeatureValue']

const FIELDS: { key: keyof Features; label: string; type: 'text' | 'number' | 'enum'; unit?: string; options?: string[] }[] = [
  { key: 'subsector_main', label: 'Podsektor główny', type: 'enum', options: SUBSECTORS },
  { key: 'work_type', label: 'Rodzaj robót', type: 'enum', options: ['budowa', 'rozbudowa', 'przebudowa', 'modernizacja', 'remont', 'renowacja'] },
  { key: 'formula', label: 'Formuła realizacji', type: 'enum', options: ['tradycyjna', 'zaprojektuj i wybuduj'] },
  { key: 'value', label: 'Wartość', type: 'number', unit: 'zł' },
  { key: 'vat_basis', label: 'Kwota netto czy brutto?', type: 'enum', options: ['net', 'gross', 'unknown'] },
  { key: 'duration_months', label: 'Czas realizacji', type: 'number', unit: 'mies.' },
  { key: 'start_date', label: 'Planowany start', type: 'text' },
  { key: 'length_km', label: 'Długość sieci', type: 'number', unit: 'km' },
  { key: 'connections', label: 'Przyłącza', type: 'number', unit: 'szt.' },
  { key: 'pump_stations', label: 'Przepompownie', type: 'number', unit: 'szt.' },
  { key: 'rlm', label: 'RLM', type: 'number' },
  { key: 'capacity_m3d', label: 'Przepustowość', type: 'number', unit: 'm³/d' },
  { key: 'voivodeship', label: 'Województwo', type: 'text' },
  { key: 'location', label: 'Lokalizacja', type: 'text' },
  { key: 'funding', label: 'Finansowanie', type: 'text' },
]
const VAT_PL: Record<string, string> = { net: 'netto', gross: 'brutto', unknown: 'nie wiadomo' }
const SRC_PL: Record<string, string> = { user: 'ekspert', regex: 'reguła', llm: 'model', document: 'dokument', default: 'domyślne' }

/** Editable feature form; every value shows its source and quote. Editing sets source = user. */
export function FeaturesForm({ value, onChange, readOnly }: { value: Features; onChange?: (f: Features) => void; readOnly?: boolean }) {
  const set = (k: keyof Features, v: unknown) => {
    const prev = (value[k] ?? {}) as FV
    const empty = v === '' || v == null
    onChange?.({ ...value, [k]: empty ? null : { ...prev, value: v, source: 'user', quote: prev.source === 'user' ? prev.quote : null } })
  }
  return (
    <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
      {FIELDS.map((f) => {
        const fv = value[f.key] as FV | null | undefined
        const raw = fv?.value
        const id = `f-${String(f.key)}`
        const warn = f.key === 'vat_basis' && (!raw || raw === 'unknown') && value.value?.value != null
        return (
          <div key={String(f.key)} className={warn ? 'rounded-md bg-amber-50 p-1 ring-1 ring-amber-300' : undefined}>
            <Label htmlFor={id} className="flex items-center justify-between gap-1">
              <span>{f.label}{f.unit && <span className="text-slate-400"> [{f.unit}]</span>}</span>
              {fv?.source && <Badge variant={fv.source === 'llm' ? 'violet' : fv.source === 'user' ? 'success' : 'default'} className="text-[10px]">{SRC_PL[fv.source] ?? fv.source}</Badge>}
            </Label>
            {f.type === 'enum' ? (
              <Select id={id} disabled={readOnly} value={raw == null ? '' : String(raw)} onChange={(e) => set(f.key, e.target.value || null)} placeholder="—"
                options={(f.options ?? []).map((o) => ({ value: o, label: f.key === 'vat_basis' ? VAT_PL[o] : o }))} />
            ) : (
              <Input id={id} disabled={readOnly} type={f.type === 'number' ? 'number' : 'text'} step="any" value={raw == null ? '' : String(raw)}
                onChange={(e) => set(f.key, f.type === 'number' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)} />
            )}
            {fv?.quote && <p className="mt-0.5 line-clamp-2 text-[11px] text-slate-500" title={fv.quote}>„{fv.quote}”</p>}
            {warn && <p className="mt-0.5 text-[11px] text-amber-800">Bez tej informacji nie porównujemy budżetu z umowami sąsiadów (kwoty tylko tego samego rodzaju).</p>}
          </div>
        )
      })}
      {!!Object.keys(value.cues ?? {}).length && (
        <div className="sm:col-span-2 lg:col-span-3">
          <Label>Sygnały w opisie (reguły)</Label>
          <ul className="mt-1 flex flex-wrap gap-1">{Object.entries(value.cues ?? {}).map(([k, c]) => (
            <li key={k}><Badge variant={k.startsWith('gap_') ? 'warning' : 'info'} title={c?.quote ?? ''}>{String(c?.value ?? k)}</Badge></li>))}</ul>
        </div>)}
    </div>
  )
}
