import { Bot, UserRound } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import clsx from 'clsx'

export default function MessageBubble({ role, content, severity }) {
  const isUser = role === 'user'

  return (
    <div
      className={clsx(
        'flex gap-3 animate-fade-in-up',
        isUser ? 'justify-end' : 'justify-start',
      )}
    >
      {!isUser && (
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 shadow-sm">
          <Bot className="h-4 w-4" aria-hidden />
        </div>
      )}
      <div
        className={clsx(
          'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[75%]',
          isUser
            ? 'rounded-br-md bg-gradient-to-br from-brand-600 to-brand-700 text-white shadow-soft'
            : 'rounded-bl-md border border-slate-100 bg-white text-slate-800 shadow-soft',
        )}
      >
        {isUser ? (
          content
        ) : (
          <div className="prose-chat">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {isUser && (
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600">
          <UserRound className="h-4 w-4" aria-hidden />
        </div>
      )}
    </div>
  )
}
