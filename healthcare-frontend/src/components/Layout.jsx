import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import { LanguageProvider } from '../context/LanguageContext'

export default function Layout() {
  return (
    <LanguageProvider>
      <div className="flex min-h-svh flex-col bg-slate-50">
        <Navbar />
        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-6 sm:px-6 sm:py-8">
          <Outlet />
        </main>
        <footer className="border-t border-slate-200/80 bg-white py-4 text-center text-xs text-slate-500">
          CareConnect Triage · For guidance only — seek emergency care when
          needed
        </footer>
      </div>
    </LanguageProvider>
  )
}
