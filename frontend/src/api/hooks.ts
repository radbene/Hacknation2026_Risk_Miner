import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query'
import { useSyncExternalStore } from 'react'
import { isFallback } from './client'

/* ---- which endpoints are currently served from mocks (shown in the layout) ---- */
const mocked = new Set<string>()
const listeners = new Set<() => void>()
let snapshot: string[] = []
function markMocked(key: string, on: boolean) {
  const had = mocked.has(key)
  if (on === had) return
  if (on) mocked.add(key)
  else mocked.delete(key)
  snapshot = Array.from(mocked).sort()
  listeners.forEach((l) => l())
}
export function useMockedEndpoints(): string[] {
  return useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l) }, () => snapshot)
}

type MockArg<T> = T | (() => T | undefined) | undefined
const resolveMock = <T,>(m: MockArg<T>): T | undefined => (typeof m === 'function' ? (m as () => T | undefined)() : m)

/** useQuery that falls back to `mock` when the endpoint is not implemented yet (501) or the backend is down. */
export function useApi<T>(key: unknown[], fn: () => Promise<T>, mock?: MockArg<T>, opts?: Partial<UseQueryOptions<T>>) {
  const tag = String(key[0]) + (key[1] !== undefined && typeof key[1] !== 'object' ? `/${String(key[1])}` : '')
  return useQuery<T>({
    queryKey: key,
    queryFn: async () => {
      try {
        const r = await fn()
        markMocked(tag, false)
        return r
      } catch (e) {
        const m = resolveMock(mock)
        if (isFallback(e) && m !== undefined) {
          markMocked(tag, true)
          return m
        }
        throw e
      }
    },
    ...opts,
  })
}

/** Mutation with the same fallback: if the backend returns 501, `mock(vars)` mutates the in-memory mock store. */
export function useApiMutation<V, R>(opts: {
  fn: (vars: V) => Promise<R>
  mock?: (vars: V) => R
  invalidate?: unknown[][]
  onSuccess?: (r: R, vars: V) => void
  onError?: (e: unknown) => void
}) {
  const qc = useQueryClient()
  return useMutation<R, unknown, V>({
    mutationFn: async (vars) => {
      try {
        return await opts.fn(vars)
      } catch (e) {
        if (isFallback(e) && opts.mock) return opts.mock(vars)
        throw e
      }
    },
    onSuccess: async (r, vars) => {
      await Promise.all((opts.invalidate ?? []).map((k) => qc.invalidateQueries({ queryKey: k })))
      opts.onSuccess?.(r, vars)
    },
    onError: opts.onError,
  })
}
