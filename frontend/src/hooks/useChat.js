import { useCallback, useRef, useState } from 'react'
import { sendChatMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'

const WELCOME_EN =
  "Hello — I'm your CareConnect triage assistant. Describe your symptoms and I'll help assess urgency and book a visit if needed."
const WELCOME_HI =
  'नमस्ते — मैं आपका CareConnect ट्राइएज सहायक हूँ। अपने लक्षण बताएँ, मैं जरूरी सलाह दूँगा और जरूरत हो तो अपॉइंटमेंट बुक करूँगा।'

export function useChat(language = 'en') {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: language === 'hi' ? WELCOME_HI : WELCOME_EN,
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [severity, setSeverity] = useState(null)
  const [bookingDetails, setBookingDetails] = useState(null)
  const [showBookingBadge, setShowBookingBadge] = useState(false)
  const [availableSlots, setAvailableSlots] = useState([])
  const redirectTimerRef = useRef(null)

  const resetChat = useCallback(() => {
    setMessages([
      {
        role: 'assistant',
        content: language === 'hi' ? WELCOME_HI : WELCOME_EN,
      },
    ])
    setError(null)
    setSeverity(null)
    setBookingDetails(null)
    setShowBookingBadge(false)
    setAvailableSlots([])
    if (redirectTimerRef.current) {
      clearTimeout(redirectTimerRef.current)
      redirectTimerRef.current = null
    }
  }, [language])

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isLoading) return null

      setError(null)
      // Clear previous slots when user sends a new message
      setAvailableSlots([])

      const userMsg = { role: 'user', content: text.trim() }
      const nextMessages = [...messages, userMsg]
      setMessages(nextMessages)
      setIsLoading(true)

      try {
        const payload = nextMessages.map(({ role, content }) => ({
          role,
          content,
        }))
        const response = await sendChatMessage(payload, language)

        const botMsg = {
          role: 'assistant',
          content:
            response.response_message ||
            (language === 'hi'
              ? 'माफ़ कीजिए, जवाब नहीं मिल सका।'
              : 'Sorry, I could not generate a response.'),
        }
        setMessages((prev) => [...prev, botMsg])

        if (response.severity) {
          setSeverity(response.severity)
        }

        // Handle SHOW_SLOTS — structured slot data for card rendering
        if (
          response.action === 'SHOW_SLOTS' &&
          response.available_slots?.length > 0
        ) {
          setAvailableSlots(response.available_slots)
        }

        // Handle REDIRECT_TO_CONFIRMATION — booking succeeded
        if (
          response.action === 'REDIRECT_TO_CONFIRMATION' &&
          response.booking_details
        ) {
          setBookingDetails(response.booking_details)
          setShowBookingBadge(true)
          setAvailableSlots([]) // clear slots after booking
        }

        return response
      } catch (err) {
        setError(
          err?.message ||
            (language === 'hi'
              ? 'सर्वर से बात नहीं हो पाई। कृपया फिर कोशिश करें।'
              : 'Could not reach the triage service. Please try again.'),
        )
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [messages, isLoading, language],
  )

  return {
    messages,
    isLoading,
    error,
    severity,
    bookingDetails,
    showBookingBadge,
    availableSlots,
    sendMessage,
    resetChat,
    redirectTimerRef,
  }
}
