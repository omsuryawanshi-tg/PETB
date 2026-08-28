import { HeartPulse } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-slate-200/80 bg-white/80 py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-center gap-2 px-4 text-xs text-slate-500">
        <HeartPulse className="h-3.5 w-3.5 text-brand-500" aria-hidden />
        <span>CareConnect Triage · For guidance only — seek emergency care when needed</span>
      </div>
    </footer>
  )
}
