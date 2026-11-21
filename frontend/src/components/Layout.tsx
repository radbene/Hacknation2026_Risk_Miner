import { Link, Outlet, useNavigate } from '@tanstack/react-router'
import { BookOpen, ClipboardCheck, Cpu, Database, FlaskConical, FolderOpen, Home, LogIn, LogOut, Plug, ShieldCheck, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'
import { useAuth } from '@/lib/auth'
import { Badge, Button, Dialog, Input, Label } from './ui'
import { DataLocationBanner } from './DataLocationBanner'

const USER_NAV = [
  { to: '/', label: 'Jak zacząć', icon: Home },
  { to: '/nowa-inwestycja', label: 'Nowa analiza', icon: Sparkles },
  { to: '/analizy', label: 'Moje analizy', icon: FolderOpen },
  { to: '/projekty', label: 'Baza przypadków', icon: Database },
  { to: '/jak-testowac', label: 'Scenariusze testowe', icon: FlaskConical },
] as const
const EXPERT_NAV = [
  { to: '/', label: 'Jak pracować w panelu', icon: Home },
  { to: '/kolejka', label: 'Do zatwierdzenia', icon: ClipboardCheck },
  { to: '/projekty', label: 'Baza przypadków', icon: Database },
  { to: '/wiedza', label: 'Wiedza ekspercka', icon: BookOpen },
  { to: '/zrodla', label: 'Źródła danych', icon: Plug },
  { to: '/modele', label: 'Modele językowe', icon: Cpu },
  { to: '/analizy', label: 'Analizy użytkowników', icon: FolderOpen },
] as const

export function Layout() {
  const { user, isExpert, logout } = useAuth()
  const [login, setLogin] = useState(false)
  const navigate = useNavigate()
  const counts = useApi(['review', 'counts'], async () => unwrap(await api.GET('/api/review/counts')), undefined, { enabled: isExpert })
  const pending = isExpert ? Object.values(counts.data ?? {}).reduce((a, b) => a + b, 0) : 0
  const nav = isExpert ? EXPERT_NAV : USER_NAV
  return (
    <div className="flex h-full">
      <aside className={`flex w-64 shrink-0 flex-col border-r ${isExpert ? 'border-violet-200 bg-violet-50/40' : 'border-slate-200 bg-white'}`}>
        <div className="px-4 pt-4 text-lg font-bold text-brand">RISK MINER</div>
        <div className="px-4 pb-3 text-xs text-slate-500">{isExpert ? <span className="inline-flex items-center gap-1 font-semibold text-violet-800"><ShieldCheck size={12} />Panel eksperta</span> : 'Analiza ryzyka nowych inwestycji'}</div>
        <nav className="flex flex-col gap-0.5 px-2" aria-label={isExpert ? 'Panel eksperta' : 'Menu'}>
          {nav.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className="flex items-center gap-2 rounded px-3 py-2 text-sm hover:bg-brand-soft"
              activeProps={{ className: 'bg-brand-soft font-semibold text-brand' }} activeOptions={{ exact: to === '/' }}>
              <Icon size={16} /> <span className="flex-1">{label}</span>
              {to === '/kolejka' && pending > 0 && <Badge variant="warning">{pending}</Badge>}
            </Link>
          ))}
        </nav>
        <div className="mt-auto border-t border-slate-200 p-3 text-xs">
          <div className="mb-2 text-slate-500">Zalogowano jako: <b className="text-slate-800">{isExpert ? user.display_name : 'Użytkownik'}</b></div>
          {isExpert
            ? <Button size="sm" variant="outline" className="w-full" onClick={() => { logout(); navigate({ to: '/' }) }}><LogOut size={13} />Wyjdź z panelu eksperta</Button>
            : <Button size="sm" variant="outline" className="w-full" onClick={() => setLogin(true)}><LogIn size={13} />Zaloguj jako ekspert</Button>}
        </div>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <DataLocationBanner />
        <div className="min-h-0 flex-1 overflow-auto p-6"><Outlet /></div>
      </main>
      <LoginDialog open={login} onClose={() => setLogin(false)} />
    </div>
  )
}

export function LoginDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { login } = useAuth()
  const navigate = useNavigate()
  const demo = useApi(['demo-users'], async () => unwrap(await api.GET('/api/auth/demo-users')), undefined, { enabled: open })
  const hint = (demo.data ?? []).find((u) => u.username === 'ekspert')?.password_hint
  const [username, setUsername] = useState('ekspert')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit() {
    setBusy(true); setErr('')
    try { await login(username, password); onClose(); navigate({ to: '/kolejka' }) } catch (e) { setErr(e instanceof Error ? e.message : String(e)) } finally { setBusy(false) }
  }
  return (
    <Dialog open={open} onClose={onClose} title="Logowanie do panelu eksperta"
      description="Ekspert zatwierdza zdarzenia, przyczyny i powiązania, poprawia dane i prowadzi wiedzę ekspercką. Użytkownik (bez logowania) analizuje nowe inwestycje i przegląda bazę."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button><Button loading={busy} onClick={submit}>Zaloguj</Button></>}>
      <form className="space-y-3 text-sm" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div><Label htmlFor="lg-u">Login</Label><Input id="lg-u" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></div>
        <div><Label htmlFor="lg-p">Hasło</Label><Input id="lg-p" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></div>
        {hint && <p className="rounded bg-amber-50 p-2 text-xs text-amber-900">Wersja demonstracyjna: konto <b>ekspert</b>, hasło <b>{hint}</b>.</p>}
        {err && <p role="alert" className="text-xs text-rose-700">{err}</p>}
        <button type="submit" className="hidden" />
      </form>
    </Dialog>
  )
}

/** Route guard: expert-panel pages show a short explanation + login for users. */
export function ExpertOnly({ children, what }: { children: React.ReactNode; what: string }) {
  const { isExpert } = useAuth()
  const [login, setLogin] = useState(false)
  if (isExpert) return <>{children}</>
  return (
    <div className="mx-auto mt-16 max-w-lg rounded-lg border border-violet-200 bg-violet-50/50 p-6 text-center">
      <ShieldCheck className="mx-auto mb-2 text-violet-700" />
      <h1 className="text-lg font-semibold">{what} – panel eksperta</h1>
      <p className="mt-1 text-sm text-slate-600">Tę część obsługuje ekspert: zatwierdza i poprawia dane, które trafiają do bazy przypadków. Zaloguj się jako ekspert, aby kontynuować.</p>
      <Button className="mt-4" onClick={() => setLogin(true)}><LogIn size={14} />Zaloguj jako ekspert</Button>
      <LoginDialog open={login} onClose={() => setLogin(false)} />
    </div>
  )
}
