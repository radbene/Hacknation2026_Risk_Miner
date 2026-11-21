import { Link, Outlet } from '@tanstack/react-router'
import { Activity, BookOpen, ClipboardCheck, Database, Home, Sparkles } from 'lucide-react'
import { DataLocationBanner } from './DataLocationBanner'

const NAV = [
  { to: '/', label: 'Start', icon: Home },
  { to: '/projekty', label: 'Baza przypadków', icon: Database },
  { to: '/kolejka', label: 'Kolejka eksperta', icon: ClipboardCheck },
  { to: '/wiedza', label: 'Wiedza ekspercka', icon: BookOpen },
  { to: '/nowa-inwestycja', label: 'Nowa inwestycja', icon: Sparkles },
  { to: '/zrodla', label: 'Źródła i operacje', icon: Activity },
] as const

export function Layout() {
  return (
    <div className="flex h-full">
      <aside className="w-60 shrink-0 border-r border-slate-200 bg-white">
        <div className="px-4 py-4 text-lg font-bold text-brand">RISK MINER</div>
        <nav className="flex flex-col gap-0.5 px-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to} className="flex items-center gap-2 rounded px-3 py-2 text-sm hover:bg-brand-soft"
              activeProps={{ className: 'bg-brand-soft font-semibold text-brand' }} activeOptions={{ exact: to === '/' }}>
              <Icon size={16} /> {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <DataLocationBanner />
        <div className="min-h-0 flex-1 overflow-auto p-6"><Outlet /></div>
      </main>
    </div>
  )
}
