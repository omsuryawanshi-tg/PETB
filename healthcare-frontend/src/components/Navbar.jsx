import { NavLink } from 'react-router-dom'
import { CalendarDays, HeartPulse, MessageSquareText } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import clsx from 'clsx'

const navLinkClass = ({ isActive }) =>
  clsx(
    'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-teal-50 text-teal-700'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
  )

export default function Navbar() {
  const { language, toggleLanguage } = useLanguage()

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-600 to-emerald-600 text-white shadow-soft">
            <HeartPulse className="h-5 w-5" strokeWidth={2.25} aria-hidden />
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-semibold tracking-tight text-slate-900">
              CareConnect Triage
            </p>
            <p className="hidden text-xs text-slate-500 sm:block">
              Patient Engagement &amp; Triage
            </p>
          </div>
        </div>

        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main">
          <NavLink to="/" end className={navLinkClass}>
            <MessageSquareText className="h-4 w-4" aria-hidden />
            <span className="hidden sm:inline">Triage Assistant</span>
            <span className="sm:hidden">Chat</span>
          </NavLink>
          <NavLink to="/appointments" className={navLinkClass}>
            <CalendarDays className="h-4 w-4" aria-hidden />
            <span className="hidden sm:inline">My Appointments</span>
            <span className="sm:hidden">Appts</span>
          </NavLink>

          <button
            type="button"
            onClick={toggleLanguage}
            className="ml-1 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800"
            aria-label={`Switch language. Current: ${language === 'en' ? 'English' : 'Hindi'}`}
          >
            <span
              className={clsx(
                'rounded px-1.5 py-0.5',
                language === 'en'
                  ? 'bg-teal-600 text-white'
                  : 'text-slate-500',
              )}
            >
              EN
            </span>
            <span className="text-slate-300">/</span>
            <span
              className={clsx(
                'rounded px-1.5 py-0.5',
                language === 'hi'
                  ? 'bg-teal-600 text-white'
                  : 'text-slate-500',
              )}
            >
              हिं
            </span>
          </button>
        </nav>
      </div>
    </header>
  )
}
