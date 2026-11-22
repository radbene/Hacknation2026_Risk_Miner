import { Link, Outlet, useNavigate, useRouterState } from '@tanstack/react-router'
import { LogIn, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { api, unwrap } from '@/api/client'
import { useApi } from '@/api/hooks'
import { useAuth } from '@/lib/auth'
import { Button, Dialog, Input, Label } from './ui'
import { Gem } from './PixelMine'
import { MineBackdrop } from './MineBackdrop'
import { DataLocationBanner } from './DataLocationBanner'

const USER_NAV = [
  { to: '/', label: 'Jak zacząć' },
  { to: '/nowa-inwestycja', label: 'Nowa analiza' },
  { to: '/analizy', label: 'Moje analizy' },
  { to: '/projekty', label: 'Baza przypadków' },
  { to: '/jak-testowac', label: 'Scenariusze testowe' },
] as const
const EXPERT_NAV = [
  { to: '/', label: 'Jak pracować w panelu' },
  { to: '/kolejka', label: 'Do zatwierdzenia' },
  { to: '/projekty', label: 'Baza przypadków' },
  { to: '/wiedza', label: 'Wiedza ekspercka' },
  { to: '/zrodla', label: 'Źródła danych' },
  { to: '/modele', label: 'Modele językowe' },
  { to: '/analizy', label: 'Analizy użytkowników' },
] as const

export function Layout() {
  const { user, isExpert, logout } = useAuth()
  const [login, setLogin] = useState(false)
  const [menu, setMenu] = useState(false)
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const counts = useApi(['review', 'counts'], async () => unwrap(await api.GET('/api/review/counts')), undefined, { enabled: isExpert })
  const pending = isExpert ? Object.values(counts.data ?? {}).reduce((a, b) => a + b, 0) : 0
  const nav = isExpert ? EXPERT_NAV : USER_NAV
  // the expert menu is longer: show it inline only on very wide screens, otherwise behind the menu button
  const wide = isExpert ? { show: '2xl:flex', hide: '2xl:hidden' } : { show: 'xl:flex', hide: 'xl:hidden' }
  const links = (mobile: boolean) => nav.map(({ to, label }) => (
    <Link key={to} to={to} onClick={() => setMenu(false)}
      className={mobile
        ? 'flex items-center gap-2 border-b-2 border-ink px-4 py-3 font-mono text-sm uppercase tracking-wide last:border-b-0 hover:bg-brand-soft'
        : 'flex items-center gap-1.5 whitespace-nowrap border-2 border-transparent px-2.5 py-1 font-mono text-[12px] uppercase tracking-wide text-ink hover:border-ink'}
      activeProps={{ className: mobile ? 'bg-ink text-paper hover:bg-ink' : 'border-ink bg-ink text-paper hover:border-ink' }} activeOptions={{ exact: to === '/' }}>
      <span className="flex-1">{label}</span>
      {to === '/kolejka' && pending > 0 && <span className="bg-amber-300 px-1 text-[11px] text-ink tabular-nums">{pending}</span>}
    </Link>))
  const roleButton = isExpert
    ? <Button size="sm" variant="outline" onClick={() => { setMenu(false); logout(); navigate({ to: '/' }) }}><LogOut size={13} />Wyjdź z panelu</Button>
    : <Button size="sm" variant="outline" onClick={() => { setMenu(false); setLogin(true) }}><LogIn size={13} />Panel eksperta</Button>
  return (
    <>
    <MineBackdrop />
    <div className="relative z-10 flex h-full flex-col">
      <header className="relative z-30 shrink-0 border-b-2 border-ink bg-paper/90 backdrop-blur-sm">
        <div className="flex items-center gap-3 px-4 py-2.5 lg:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2" onClick={() => setMenu(false)} aria-label="RISK MINER, strona główna">
            <span className="logo-gem grid h-9 w-9 place-items-center border-2 border-ink bg-surface shadow-sm"><Gem size={22} /></span>
            <span className="font-pixel text-[15px] leading-none text-ink">Risk<br />Miner</span>
          </Link>
          <nav className={`ml-3 hidden items-center gap-1 ${wide.show}`} aria-label={isExpert ? 'Panel eksperta' : 'Menu'}>{links(false)}</nav>
          <span className="stripes mx-2 hidden h-4 min-w-6 flex-1 sm:block" aria-hidden />
          <span className="flex-1 sm:hidden" />
          <div className="hidden shrink-0 items-center gap-2 md:flex">
            <span className="whitespace-nowrap font-mono text-xs text-slate-600">{isExpert ? user.display_name : 'Użytkownik'}</span>
            <span className={isExpert ? 'tag border-violet-700 bg-violet-50 text-violet-800' : 'tag'}>{isExpert ? 'ekspert' : 'analityk'}</span>
            {roleButton}
          </div>
          <button className={`press grid h-9 w-9 shrink-0 place-items-center border-2 border-ink bg-surface shadow-sm cursor-pointer ${wide.hide}`}
            aria-label={menu ? 'Zamknij menu' : 'Otwórz menu'} aria-expanded={menu} onClick={() => setMenu((m) => !m)}>
            {menu ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
        {menu && (
          <div className={`absolute inset-x-0 top-full border-b-2 border-ink bg-surface shadow-md sm:left-auto sm:right-4 sm:top-[calc(100%+6px)] sm:w-80 sm:border-2 lg:right-6 ${wide.hide}`}>
            <nav className="flex flex-col" aria-label="Menu">{links(true)}</nav>
            <div className="flex items-center gap-2 border-t-2 border-ink px-4 py-3 md:hidden">
              <span className={isExpert ? 'tag border-violet-700 bg-violet-50 text-violet-800' : 'tag'}>{isExpert ? 'ekspert' : 'analityk'}</span>
              <span className="flex-1 font-mono text-xs">{isExpert ? user.display_name : 'Użytkownik'}</span>
              {roleButton}
            </div>
          </div>)}
      </header>
      <main className="flex min-h-0 min-w-0 flex-1 flex-col">
        <DataLocationBanner />
        <div className="min-h-0 flex-1 overflow-auto px-4 py-5 sm:px-6 lg:px-10 lg:py-8"><div key={pathname} className="page-in mx-auto max-w-[1400px]"><Outlet /></div></div>
      </main>
      <LoginDialog open={login} onClose={() => setLogin(false)} />
    </div>
    </>
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
  async function submit(u = username, pw = password) {
    setBusy(true); setErr('')
    try { await login(u, pw); onClose(); navigate({ to: '/kolejka' }) } catch (e) { setErr(e instanceof Error ? e.message : String(e)) } finally { setBusy(false) }
  }
  return (
    <Dialog open={open} onClose={onClose} title="Logowanie do panelu eksperta"
      description="Ekspert zatwierdza zdarzenia, przyczyny i powiązania, poprawia dane i prowadzi wiedzę ekspercką."
      footer={<><Button variant="outline" onClick={onClose}>Anuluj</Button>
        {/* demo: one click, like the EKSPERT tile on the start page ("panel eksperta otwiera się bez hasła") */}
        {hint && <Button variant="outline" loading={busy} onClick={() => submit('ekspert', hint)}>Wejdź jako ekspert (demo)</Button>}
        <Button loading={busy} onClick={() => submit()}>Zaloguj</Button></>}>
      <form className="space-y-3 text-sm" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div><Label htmlFor="lg-u">Login</Label><Input id="lg-u" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></div>
        <div><Label htmlFor="lg-p">Hasło</Label><Input id="lg-p" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></div>
        {hint && <p className="border-2 border-amber-700 bg-amber-50 p-2 text-xs text-amber-900">Wersja demonstracyjna: konto <b>ekspert</b>, hasło <b>{hint}</b>.</p>}
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
    <div className="mx-auto mt-16 max-w-lg border-2 border-ink bg-surface p-6 text-center shadow-md">
      <h1 className="text-lg font-semibold">{what}</h1>
      <p className="mt-1 text-sm text-slate-600">Tę część obsługuje ekspert: zatwierdza i poprawia dane, które trafiają do bazy przypadków.</p>
      <Button className="mt-4" onClick={() => setLogin(true)}><LogIn size={14} />Zaloguj jako ekspert</Button>
      <LoginDialog open={login} onClose={() => setLogin(false)} />
    </div>
  )
}
