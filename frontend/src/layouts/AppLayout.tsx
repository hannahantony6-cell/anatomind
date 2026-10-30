import { BarChart3, BookOpen, History, LayoutDashboard, LogOut, Menu, User as UserIcon, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { Logo } from '../components/Logo'
import { useAuth } from '../hooks/useAuth'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/topics', label: 'Textbook Topics', Icon: BookOpen },
  { to: '/progress', label: 'My Progress', Icon: BarChart3 },
  { to: '/history', label: 'Quiz History', Icon: History },
  { to: '/profile', label: 'Profile', Icon: UserIcon },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const doLogout = async () => { await logout(); nav('/login', { replace: true }) }

  const links = (
    <nav aria-label="Main" className="flex flex-1 flex-col gap-1">
      {NAV.map(({ to, label, Icon }) => (
        <NavLink key={to} to={to} onClick={() => setOpen(false)}
          className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-teal-600 text-white' : 'text-navy-100 hover:bg-navy-800'}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />{label}
        </NavLink>
      ))}
      <button onClick={doLogout} className="mt-auto flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-navy-100 hover:bg-navy-800">
        <LogOut className="h-4 w-4" aria-hidden="true" />Logout
      </button>
    </nav>
  )

  return (
    <div className="min-h-screen lg:flex">
      <header className="flex items-center justify-between bg-navy-900 px-4 py-3 lg:hidden">
        <Logo to="/dashboard" light />
        <button aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open} onClick={() => setOpen((o) => !o)} className="rounded-lg p-2 text-white hover:bg-navy-800">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>
      <aside className={`${open ? 'flex' : 'hidden'} flex-col gap-6 bg-navy-900 p-4 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0`}>
        <div className="hidden lg:block"><Logo to="/dashboard" light /></div>
        {links}
        <p className="truncate px-3 text-xs text-navy-200">Signed in as {user?.full_name}</p>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-8"><Outlet /></main>
        <footer className="border-t border-navy-100 bg-white px-4 py-4 sm:px-8"><Disclaimer compact /></footer>
      </div>
    </div>
  )
}
