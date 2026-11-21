/** Who is using the app: the end user (prepares / assesses investments) or the expert (separate expert panel).
 * Anonymous visitor = user. The expert logs in (POST /api/auth/login); the signed token is sent by api/client. */
import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

export interface AuthUser { username: string; role: string; display_name: string }
interface Ctx {
  user: AuthUser
  isExpert: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const USER: AuthUser = { username: 'analityk', role: 'analyst', display_name: 'Użytkownik' }
const AuthCtx = createContext<Ctx>({ user: USER, isExpert: false, login: async () => {}, logout: () => {} })

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [user, setUser] = useState<AuthUser>(() => {
    try { return JSON.parse(localStorage.getItem('rm_auth_user') ?? '') as AuthUser } catch { return USER }
  })
  useEffect(() => { localStorage.removeItem('rm_user') }, []) // old developer shortcut header – not used any more
  useEffect(() => {
    const token = localStorage.getItem('rm_token')
    if (!token) return
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } }).then(async (r) => {
      if (!r.ok) { localStorage.removeItem('rm_token'); localStorage.removeItem('rm_auth_user'); setUser(USER); return }
      const u = (await r.json()) as AuthUser
      setUser(u); localStorage.setItem('rm_auth_user', JSON.stringify(u))
    }).catch(() => {})
  }, [])
  const login = useCallback(async (username: string, password: string) => {
    const r = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) })
    if (!r.ok) throw new Error((await r.json().catch(() => ({})))?.detail ?? 'Nieprawidłowy login lub hasło')
    const d = (await r.json()) as { token: string; user: AuthUser }
    localStorage.setItem('rm_token', d.token); localStorage.setItem('rm_auth_user', JSON.stringify(d.user))
    setUser(d.user); await qc.invalidateQueries()
  }, [qc])
  const logout = useCallback(() => {
    localStorage.removeItem('rm_token'); localStorage.removeItem('rm_auth_user'); setUser(USER); qc.invalidateQueries()
  }, [qc])
  return <AuthCtx.Provider value={{ user, isExpert: user.role === 'expert' || user.role === 'admin', login, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
