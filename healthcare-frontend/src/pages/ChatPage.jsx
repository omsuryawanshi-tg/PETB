import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bot,
  CalendarCheck2,
  Loader2,
  SendHorizontal,
  UserRound,
} from 'lucide-react'
import { saveLocalAppointment, sendChatMessage } from '../services/api'
import { useLanguage } from '../context/LanguageContext'
import clsx from 'clsx'

const STARTER_PROMPTS = [
  'I have a persistent headache and fever',
  'Severe stomach pain since morning',
  'मुझको 2 दिन से बुखार है',
]

const WELCOME_EN =
  "Hello — I'm your CareConnect triage assistant. Describe your symptoms and I'll help assess urgency and book a visit if needed."
const WELCOME_HI =
  'नमस्ते — मैं आपका CareConnect ट्राइएज सहायक हूँ। अपने लक्षण बताएँ, मैं जरूरी सलाह दूँगा और जरूरत हो तो अपॉइंटमेंट बुक करूँगा।'

export default function ChatPage() {
  const navigate = useNavigate()
  const { language } = useLanguage()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [error, setError] = useState(null)
  const [showBookingBadge, setShowBookingBadge] = useState(false)
  const [patientName] = useState('Patient')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const redirectTimerRef = useRef(null)

  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: language === 'hi' ? WELCOME_HI : WELCOME_EN,
      },
    ])
  }, [language])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking, showBookingBadge])

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current)
      }
    }
  }, [])

  async function handleSend(rawText) {
    const text = (rawText ?? input).trim()
    if (!text || isThinking) return

    setError(null)
    setInput('')

    const nextMessages = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setIsThinking(true)

    try {
      // Send only user/assistant turns (exclude any UI-only flags)
      const payload = nextMessages.map(({ role, content }) => ({ role, content }))
      const response = await sendChatMessage(payload, language, patientName)

      const botMessage = {
        role: 'assistant',
        content:
          response.response_message ||
          (language === 'hi'
            ? 'माफ़ कीजिए, जवाब नहीं मिल सका।'
            : 'Sorry, I could not generate a response.'),
      }

      setMessages((prev) => [...prev, botMessage])

      if (response.action === 'REDIRECT_TO_CONFIRMATION') {
        setShowBookingBadge(true)
        if (response.booking_details) {
          saveLocalAppointment({
            ...response.booking_details,
            patient_name: patientName,
            status: 'Confirmed',
          })
        }

        redirectTimerRef.current = setTimeout(() => {
          navigate('/confirmation', {
            state: { booking: response.booking_details },
          })
        }, 1500)
      }
    } catch (err) {
      setError(
        err?.message ||
          (language === 'hi'
            ? 'सर्वर से बात नहीं हो पाई। कृपया फिर कोशिश करें।'
            : 'Could not reach the triage service. Please try again.'),
      )
    } finally {
      setIsThinking(false)
      inputRef.current?.focus()
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    handleSend()
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="mb-5 text-center sm:text-left">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Triage Assistant
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Share symptoms in English or Hindi — we&apos;ll guide next steps.
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
        {/* Messages */}
        <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6">
          {messages.map((msg, idx) => (
            <div
              key={`${msg.role}-${idx}`}
              className={clsx(
                'flex gap-3',
                msg.role === 'user' ? 'justify-end' : 'justify-start',
              )}
            >
              {msg.role === 'assistant' && (
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-50 text-teal-700">
                  <Bot className="h-4 w-4" aria-hidden />
                </div>
              )}
              <div
                className={clsx(
                  'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[75%]',
                  msg.role === 'user'
                    ? 'rounded-br-md bg-teal-600 text-white'
                    : 'rounded-bl-md border border-slate-100 bg-slate-50 text-slate-800',
                )}
              >
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600">
                  <UserRound className="h-4 w-4" aria-hidden />
                </div>
              )}
            </div>
          ))}

          {isThinking && (
            <div className="flex items-center gap-3" aria-live="polite">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-50 text-teal-700">
                <Bot className="h-4 w-4" aria-hidden />
              </div>
              <div className="inline-flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-100 bg-slate-50 px-4 py-2.5 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin text-teal-600" />
                Thinking…
              </div>
            </div>
          )}

          {showBookingBadge && (
            <div className="flex justify-center" aria-live="polite">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 shadow-soft">
                <CalendarCheck2 className="h-4 w-4" aria-hidden />
                Booking confirmed — redirecting…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Starter chips */}
        {messages.length <= 1 && !isThinking && (
          <div className="flex flex-wrap gap-2 border-t border-slate-100 px-4 py-3 sm:px-6">
            {STARTER_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => handleSend(prompt)}
                className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-left text-xs font-medium text-slate-600 transition hover:border-teal-300 hover:bg-teal-50 hover:text-teal-800"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div
            className="border-t border-red-100 bg-red-50 px-4 py-2 text-sm text-red-700 sm:px-6"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Composer */}
        <form
          onSubmit={onSubmit}
          className="flex items-end gap-2 border-t border-slate-200 bg-slate-50/80 px-3 py-3 sm:px-4"
        >
          <label htmlFor="chat-input" className="sr-only">
            Message
          </label>
          <textarea
            id="chat-input"
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            disabled={isThinking || showBookingBadge}
            placeholder={
              language === 'hi'
                ? 'अपने लक्षण लिखें…'
                : 'Describe your symptoms…'
            }
            className="max-h-32 min-h-[44px] flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-teal-400 focus:ring-2 focus:ring-teal-100 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!input.trim() || isThinking || showBookingBadge}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white shadow-soft transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Send message"
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
