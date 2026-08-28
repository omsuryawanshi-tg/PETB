import { NavLink, useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  UserCircle,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useLanguage } from '../../context/LanguageContext'
import clsx from 'clsx'

const navLinkClass = ({ isActive }) =>
  clsx(
    'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
    isActive
      ? 'bg-brand-50 text-brand-700 shadow-sm'
      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
  )

export default function Navbar() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth()
  const { language, toggleLanguage } = useLanguage()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 glass">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        {/* Logo */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-accent-600 text-white shadow-soft">
            <HeartPulse className="h-5 w-5" strokeWidth={2.25} aria-hidden />
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-bold tracking-tight text-slate-900">
              CareConnect
            </p>
            <p className="hidden text-[11px] text-slate-500 sm:block">
              Patient Engagement & Triage
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main">
          {isAuthenticated && (
            <>
              <NavLink to="/" end className={navLinkClass}>
                <MessageSquareText className="h-4 w-4" aria-hidden />
                <span className="hidden sm:inline">Triage</span>
              </NavLink>
              <NavLink to="/appointments" className={navLinkClass}>
                <CalendarDays className="h-4 w-4" aria-hidden />
                <span className="hidden sm:inline">Appointments</span>
              </NavLink>
              {isAdmin && (
                <NavLink to="/admin" className={navLinkClass}>
                  <LayoutDashboard className="h-4 w-4" aria-hidden />
                  <span className="hidden sm:inline">Admin</span>
                </NavLink>
              )}
            </>
          )}

          {/* Language toggle */}
          <button
            type="button"
            onClick={toggleLanguage}
            className="ml-1 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-800"
            aria-label={`Switch language. Current: ${language === 'en' ? 'English' : 'Hindi'}`}
          >
            <span
              className={clsx(
                'rounded px-1.5 py-0.5 transition-colors',
                language === 'en'
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-500',
              )}
            >
              EN
            </span>
            <span className="text-slate-300">/</span>
            <span
              className={clsx(
                'rounded px-1.5 py-0.5 transition-colors',
                language === 'hi'
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-500',
              )}
            >
              हिं
            </span>
          </button>

          {/* User section */}
          {isAuthenticated ? (
            <div className="ml-2 flex items-center gap-2">
              <div className="hidden items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-600 sm:flex">
                <UserCircle className="h-3.5 w-3.5" aria-hidden />
                {user?.full_name?.split(' ')[0]}
              </div>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700"
                aria-label="Logout"
              >
                <LogOut className="h-3.5 w-3.5" aria-hidden />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="ml-2 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white shadow-soft transition hover:bg-brand-700"
            >
              Sign In
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  )
}
