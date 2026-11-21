import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'

const LABEL: Record<string, string> = { local: 'lokalnie', eu: 'w UE', non_eu: 'poza UE', none: 'bez LLM (reguły)' }

export function DataLocationBanner() {
  const { data } = useApi(['settings', 'llm'], async () => unwrap(await api.GET('/api/settings/llm')))
  if (!data) return null
  const locs = data.active_data_locations
  const warn = locs.includes('non_eu')
  return (
    <div className={`px-6 py-1.5 text-xs ${warn ? 'bg-amber-50 text-amber-900' : 'bg-emerald-50 text-emerald-900'}`}>
      Przetwarzanie LLM: <b>{locs.map((l) => LABEL[l] ?? l).join(', ') || 'brak'}</b> · tryb {data.mode}
    </div>
  )
}
