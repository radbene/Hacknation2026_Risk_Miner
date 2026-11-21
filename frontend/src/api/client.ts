/**
 * Typed API client generated from the backend OpenAPI contract (npm run gen:api).
 *   const { data } = await api.GET('/api/projects', { params: { query: { tier: 'deep' } } })
 * While a backend router still returns 501 (or the backend is unreachable), pages fall back to mocks – see useApi().
 */
import createClient from 'openapi-fetch'
import type { paths, components } from './schema'

export type Schemas = components['schemas']

export const api = createClient<paths>({ baseUrl: '' })

api.use({
  onRequest({ request }) {
    const user = localStorage.getItem('rm_user')
    const token = localStorage.getItem('rm_token')
    if (user) request.headers.set('X-User', user)
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
})

/** Endpoint exists in the contract but its router is not implemented yet (HTTP 501). */
export class NotImplementedYet extends Error {}
/** Backend not reachable (network error, proxy 502/503/504). */
export class BackendUnavailable extends Error {}

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, detail: unknown) {
    super(`API ${status}: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`)
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
  const r = await fetch(url, { ...init, headers })
  if (r.status === 501) throw new NotImplementedYet(url)
  if (r.status >= 502 && r.status <= 504) throw new BackendUnavailable(url)
  if (!r.ok) throw new ApiError(r.status, await r.text())
  return r
}
