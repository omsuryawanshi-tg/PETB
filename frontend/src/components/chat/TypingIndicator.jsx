import { Bot } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 animate-fade-in-up" aria-live="polite">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-700 shadow-sm">
        <Bot className="h-4 w-4" aria-hidden />
      </div>
      <div className="inline-flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-slate-100 bg-white px-4 py-3 shadow-soft">
        <div className="typing-dot h-2 w-2 rounded-full bg-brand-400" />
        <div className="typing-dot h-2 w-2 rounded-full bg-brand-400" />
        <div className="typing-dot h-2 w-2 rounded-full bg-brand-400" />
      </div>
    </div>
  )
}
