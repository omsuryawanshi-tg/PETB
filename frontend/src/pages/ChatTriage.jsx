import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { SendHorizontal } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { useChat } from '../hooks/useChat'
import MessageBubble from '../components/chat/MessageBubble'
import QuickChips from '../components/chat/QuickChips'
import TypingIndicator from '../components/chat/TypingIndicator'
import ActionCard from '../components/chat/ActionCard'
import SlotCard from '../components/chat/SlotCard'
import clsx from 'clsx'
import { useState } from 'react'

const STARTER_PROMPTS = [
  'I have a persistent headache and fever',
  'Severe stomach pain since morning',
  'मुझको 2 दिन से बुखार है',
  'I feel chest tightness when walking',
]

const SEVERITY_COLORS = {
  low: 'bg-green-50 text-green-700 ring-green-200',
  medium: 'bg-amber-50 text-amber-700 ring-amber-200',
  high: 'bg-red-50 text-red-700 ring-red-200',
  emergency: 'bg-red-100 text-red-800 ring-red-300 animate-pulse-emergency',
}

export default function ChatTriage() {
  const navigate = useNavigate()
  const { language } = useLanguage()
  const {
    messages,
    isLoading,
    error,
    severity,
    bookingDetails,
    showBookingBadge,
    availableSlots,
    sendMessage,
    redirectTimerRef,
  } = useChat(language)

  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, showBookingBadge, availableSlots])

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current)
      }
    }
  }, [redirectTimerRef])

  // Auto-redirect on booking
  useEffect(() => {
    if (showBookingBadge && bookingDetails) {
      redirectTimerRef.current = setTimeout(() => {
        navigate('/confirmation', {
          state: { booking: bookingDetails },
        })
      }, 2500)
    }
  }, [showBookingBadge, bookingDetails, navigate, redirectTimerRef])

  // Handle slot selection — sends a booking message to the agent
  function handleSlotBook(slot) {
    const bookingMsg = `Book appointment with ${slot.doctor_name} on ${slot.date} at ${slot.time_slot} (Doctor ID: ${slot.doctor_id})`
    handleSend(bookingMsg)
  }

  async function handleSend(rawText) {
    const text = (rawText ?? input).trim()
    if (!text) return

    setInput('')
    await sendMessage(text)
    inputRef.current?.focus()
  }

  function onSubmit(e) {
    e.preventDefault()
    handleSend()
  }

  return (
    <div className="flex flex-1 flex-col">
      {/* Header */}
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Triage Assistant
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Share symptoms in English or Hindi — we'll guide next steps.
          </p>
        </div>
        {severity && (
          <span
            className={clsx(
              'inline-flex items-center rounded-full px-3 py-1 text-xs font-bold ring-1 uppercase tracking-wide',
              SEVERITY_COLORS[severity] || SEVERITY_COLORS.low,
            )}
          >
            {severity}
          </span>
        )}
      </div>

      {/* Chat Container */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
        {/* Messages */}
        <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-6">
          {messages.map((msg, idx) => (
            <MessageBubble
              key={`${msg.role}-${idx}`}
              role={msg.role}
              content={msg.content}
              severity={severity}
            />
          ))}

          {isLoading && <TypingIndicator />}

          {/* Slot Cards Grid */}
          {availableSlots.length > 0 && !isLoading && (
            <div className="animate-fade-in-up">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Available Slots
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {availableSlots.map((slot, idx) => (
                  <SlotCard
                    key={`${slot.doctor_id}-${slot.date}-${slot.time_slot}-${idx}`}
                    slot={slot}
                    onBook={handleSlotBook}
                    disabled={isLoading || showBookingBadge}
                  />
                ))}
              </div>
            </div>
          )}

          {showBookingBadge && <ActionCard booking={bookingDetails} />}

          <div ref={bottomRef} />
        </div>

        {/* Starter chips */}
        {messages.length <= 1 && !isLoading && (
          <QuickChips
            prompts={STARTER_PROMPTS}
            onSelect={handleSend}
            disabled={isLoading || showBookingBadge}
          />
        )}

        {/* Error */}
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
            disabled={isLoading || showBookingBadge}
            placeholder={
              language === 'hi'
                ? 'अपने लक्षण लिखें…'
                : 'Describe your symptoms…'
            }
            className="max-h-32 min-h-[44px] flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || showBookingBadge}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 text-white shadow-soft transition hover:from-brand-700 hover:to-brand-800 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Send message"
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
