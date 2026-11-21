import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'

const WHERE: Record<string, string> = {
  local: 'działa na naszym serwerze – dokumenty nie opuszczają systemu',
  eu: 'działa w chmurze w UE',
  non_eu: 'działa w usłudze poza UE',
  none: 'wyłączony – system używa wyłącznie reguł',
}

/** One sentence: which language model answers first and where the data is processed. */
export function DataLocationBanner() {
  const { data } = useApi(['settings', 'llm'], async () => unwrap(await api.GET('/api/settings/llm')))
  if (!data) return null
  const firsts = Object.values(data.tasks).map((c) => c.find((n) => data.profiles.find((p) => p.name === n)?.available)).filter(Boolean) as string[]
  const top = firsts.sort((a, b) => firsts.filter((x) => x === b).length - firsts.filter((x) => x === a).length)[0]
  const p = data.profiles.find((x) => x.name === top)
  const loc = p?.data_location ?? 'none'
  const warn = loc === 'non_eu'
  return (
    <div className={`px-6 py-1.5 text-xs ${warn ? 'bg-amber-50 text-amber-900' : 'bg-emerald-50 text-emerald-900'}`}>
      Model językowy: <b>{(p?.display_name ?? p?.name ?? 'brak').replace(/\s*\(.*\)$/, '')}</b> – {WHERE[loc] ?? loc}. Każdy wniosek modelu jest oznaczony i czeka na decyzję eksperta.
    </div>
  )
}
