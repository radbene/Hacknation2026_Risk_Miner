/**
 * Typed API client generated from the backend OpenAPI contract (npm run gen:api).
 *   const { data } = await api.GET('/api/projects', { params: { query: { tier: 'deep' } } })
 * While a backend router still returns 501 (or the backend is unreachable), pages fall back to mocks – see useApi().
 */
import createClient from 'openapi-fetch'
import type { paths, components } from './schema'

export type Schemas = components['schemas']

export const api = createClient<paths>({ baseUrl: '' })

// The public demo runs behind an ngrok tunnel: this header stops ngrok from answering API calls with its
// "You are about to visit…" interstitial page.
const TUNNEL_HEADER = 'ngrok-skip-browser-warning'

// Same header for plain fetch() calls to our own API (login, uploads, evidence context …).
if (typeof window !== 'undefined' && !(window.fetch as { rmPatched?: boolean }).rmPatched) {
  const nativeFetch = window.fetch.bind(window)
  const patched = (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const sameOriginApi = url.startsWith('/api') || url.startsWith(`${window.location.origin}/api`)
    if (!sameOriginApi || input instanceof Request) return nativeFetch(input, init)
    const headers = new Headers(init?.headers)
    headers.set(TUNNEL_HEADER, '1')
    return nativeFetch(input, { ...init, headers })
  }
  ;(patched as { rmPatched?: boolean }).rmPatched = true
  window.fetch = patched as typeof window.fetch
}

api.use({
  onRequest({ request }) {
    const user = localStorage.getItem('rm_user')
    const token = localStorage.getItem('rm_token')
    if (user) request.headers.set('X-User', user)
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    request.headers.set(TUNNEL_HEADER, '1')
    return request
  },
})

/** Endpoint exists in the contract but its router is not implemented yet (HTTP 501). */
export class NotImplementedYet extends Error {}
/** Backend not reachable (network error, proxy 502/503/504). */
export class BackendUnavailable extends Error {}

/** An HTML page instead of JSON means the request never reached our API (offline tunnel, proxy error page). */
function isHtmlPage(detail: unknown): boolean {
  return typeof detail === 'string' && /^\s*<(!doctype|html)/i.test(detail)
}

function describe(status: number, detail: unknown): string {
  if (isHtmlPage(detail)) {
    return `Serwer aplikacji jest niedostępny pod tym adresem (HTTP ${status}). ` +
      'Odśwież stronę; jeśli błąd się powtarza, adres demo mógł się zmienić.'
  }
  const text = typeof detail === 'string' ? detail : JSON.stringify(detail)
  return `Błąd serwera (HTTP ${status}): ${text.length > 300 ? `${text.slice(0, 300)}…` : text}`
}

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, detail: unknown) {
    super(describe(status, detail))
    this.status = status
    this.detail = detail
  }
}

/** Unwrap an openapi-fetch result; 501 → NotImplementedYet, 502–504 → BackendUnavailable (callers may use a mock). */
export function unwrap<T>(res: { data?: T; error?: unknown; response: Response }): T {
  const s = res.response.status
  if (s === 501) throw new NotImplementedYet(String(res.response.url))
  if (s === 502 || s === 503 || s === 504) throw new BackendUnavailable(String(res.response.url))
  if (res.error !== undefined || res.data === undefined) {
    const err = res.error as { detail?: unknown } | undefined
    throw new ApiError(s, err?.detail ?? res.error)
  }
  return res.data
}

export function isFallback(e: unknown): boolean {
  return e instanceof NotImplementedYet || e instanceof BackendUnavailable || e instanceof TypeError
}

/** Raw fetch for non-JSON endpoints (exports, files) with the same auth headers. */
export async function rawFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const user = localStorage.getItem('rm_user')
  const token = localStorage.getItem('rm_token')
  if (user) headers.set('X-User', user)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  headers.set(TUNNEL_HEADER, '1')
  const r = await fetch(url, { ...init, headers })
  if (r.status === 501) throw new NotImplementedYet(url)
  if (r.status >= 502 && r.status <= 504) throw new BackendUnavailable(url)
  if (!r.ok) throw new ApiError(r.status, await r.text())
  return r
}
