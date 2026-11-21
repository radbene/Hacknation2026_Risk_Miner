/**
 * Typed API client generated from the backend OpenAPI contract (npm run gen:api).
 *   const { data } = await api.GET('/api/projects', { params: { query: { tier: 'deep' } } })
 * While a backend router still returns 501, pages fall back to mocks (src/mocks) – see useApi().
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

export class NotImplementedYet extends Error {}

/** Unwrap an openapi-fetch result; 501 → NotImplementedYet (caller may use a mock). */
export function unwrap<T>(res: { data?: T; error?: unknown; response: Response }): T {
  if (res.response.status === 501) throw new NotImplementedYet(String(res.response.url))
  if (res.error !== undefined || res.data === undefined) throw new Error(`API ${res.response.status}: ${JSON.stringify(res.error)}`)
  return res.data
}
