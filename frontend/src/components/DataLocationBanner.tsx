import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'

const WHERE: Record<string, string> = {
  local: 'działa na naszym serwerze, dokumenty nie opuszczają systemu',
  eu: 'działa w chmurze w UE',
  non_eu: 'działa w usłudze poza UE',
  none: 'wyłączony, system używa samych reguł',
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
    <div className={`border-b-2 border-ink px-4 py-1 font-mono text-[11px] sm:px-6 lg:px-10 ${warn ? 'bg-amber-100 text-amber-900' : 'bg-surface text-slate-600'}`}>
      <span aria-hidden className="mr-1.5 inline-block h-2 w-2 bg-emerald-500 align-middle" />Model językowy <b>{(p?.display_name ?? p?.name ?? 'brak').replace(/\s*\(.*\)$/, '')}</b> {WHERE[loc] ?? loc}.
    </div>
  )
}
