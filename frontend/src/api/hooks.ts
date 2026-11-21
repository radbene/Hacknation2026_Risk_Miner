import { useQuery, type UseQueryOptions } from '@tanstack/react-query'
import { NotImplementedYet } from './client'

/** useQuery that falls back to `mock` when the endpoint is not implemented yet (HTTP 501). */
export function useApi<T>(key: unknown[], fn: () => Promise<T>, mock?: T, opts?: Partial<UseQueryOptions<T>>) {
  return useQuery<T>({
    queryKey: key,
    queryFn: async () => {
      try {
        return await fn()
      } catch (e) {
        if (e instanceof NotImplementedYet && mock !== undefined) return mock
        throw e
      }
    },
    ...opts,
  })
}
