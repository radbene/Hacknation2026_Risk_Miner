/** Shared by the user's and the expert's "add a model" forms: kinds, field hints per kind and the rule for
 *  where data is processed. The location is decided by the system (same rule as backend
 *  `routing.infer_data_location`) – nobody types it in. */

export const PROVIDERS = [
  { value: 'openai_compatible', label: 'Własny serwer zgodny z API OpenAI (Ollama, vLLM, LM Studio, Mistral, OpenRouter…)' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'openai', label: 'OpenAI (GPT)' },
  { value: 'gemini', label: 'Google Gemini' },
]

export interface KindHints { name: string; model: string; modelHelp?: string; key: string; keyEnv: string; keyHelp: string }

export const HINTS: Record<string, KindHints> = {
  openai_compatible: {
    name: 'np. PLLuM 12B', model: 'np. CYFRAGOVPL/PLLuM-12B-instruct albo SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M',
    key: 'zostaw puste, jeśli serwer nie wymaga klucza (np. Ollama)', keyEnv: 'zostaw puste, jeśli serwer nie wymaga klucza (np. Ollama)',
    modelHelp: 'Nazwa modelu dokładnie taka, jak na serwerze (dla Ollamy: wynik polecenia „ollama list”).',
    keyHelp: 'Potrzebny tylko, jeśli serwer wymaga klucza.',
  },
  anthropic: { name: 'np. Claude Sonnet', model: 'np. claude-sonnet-5-5', key: 'sk-ant-…', keyEnv: 'np. ANTHROPIC_API_KEY',
    keyHelp: 'Klucz z console.anthropic.com → API Keys.' },
  openai: { name: 'np. GPT-4.1', model: 'np. gpt-4.1', key: 'sk-…', keyEnv: 'np. OPENAI_API_KEY', keyHelp: 'Klucz z platform.openai.com → API keys.' },
  gemini: { name: 'np. Gemini 3.8 Flash', model: 'np. gemini-3.8-flash', key: 'AIza…', keyEnv: 'np. GEMINI_API_KEY',
    keyHelp: 'Klucz z aistudio.google.com → Get API key.' },
}

export const SERVER_URL_HINT = 'np. http://192.168.1.20:11434/v1 albo https://llm.moja-gmina.pl/v1'

const EU_TLDS = new Set(['eu', 'pl', 'de', 'fr', 'nl', 'be', 'lu', 'at', 'ie', 'it', 'es', 'pt', 'dk', 'se', 'fi', 'ee', 'lv', 'lt', 'cz', 'sk', 'hu', 'si', 'hr', 'ro', 'bg', 'gr', 'cy', 'mt'])

export const LOC_LABEL: Record<string, string> = { local: 'w sieci instytucji', eu: 'w Unii Europejskiej', non_eu: 'poza Unią Europejską' }

/** Where a model processes data, from its kind and server address. */
export function inferLocation(provider: string, url: string): { loc: string; why: string } {
  if (provider !== 'openai_compatible') return { loc: 'non_eu', why: 'API dostawcy działa poza Unią Europejską.' }
  let host = ''
  try { host = new URL(url.trim()).hostname.toLowerCase() } catch { return { loc: '', why: 'Podaj adres serwera, a ustalimy, gdzie trafią dane.' } }
  const ipv4 = /^(\d+)\.(\d+)\.\d+\.\d+$/.exec(host)
  const priv = ipv4 && (ipv4[1] === '10' || ipv4[1] === '127' || (ipv4[1] === '192' && ipv4[2] === '168')
    || (ipv4[1] === '172' && +ipv4[2] >= 16 && +ipv4[2] <= 31) || (ipv4[1] === '169' && ipv4[2] === '254'))
  if (host === 'localhost' || !host.includes('.') || /\.(local|internal|lan|localhost)$/.test(host) || priv)
    return { loc: 'local', why: 'Serwer w sieci wewnętrznej – dane nie wychodzą do internetu.' }
  if (ipv4) return { loc: 'non_eu', why: 'Nie znamy położenia serwera, więc przyjmujemy ostrożnie: poza UE.' }
  if (host === 'api.mistral.ai' || EU_TLDS.has(host.split('.').pop() ?? '')) return { loc: 'eu', why: 'Adres w domenie kraju Unii Europejskiej.' }
  return { loc: 'non_eu', why: 'Nie wiemy, że serwer jest w UE, więc przyjmujemy ostrożnie: poza UE.' }
}

export function LocationNote({ provider, url }: { provider: string; url: string }) {
  const w = inferLocation(provider, url)
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs" aria-live="polite">
      <div className="font-medium text-slate-700">Gdzie trafią dane: {w.loc ? LOC_LABEL[w.loc] : '—'}</div>
      <div className="text-slate-500">{w.why} Ustalamy to automatycznie na podstawie rodzaju modelu i adresu.</div>
    </div>
  )
}
