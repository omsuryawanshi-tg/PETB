import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, Loader2, MessageSquareText } from 'lucide-react'
import { getMyAppointments, cancelAppointment } from '../services/api'
import BookingCard from '../components/appointments/BookingCard'
import toast from 'react-hot-toast'

export default function MyAppointments() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all | upcoming | past

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await getMyAppointments()
        if (!cancelled) setAppointments(Array.isArray(data) ? data : [])
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || 'Failed to load appointments.')
          setAppointments([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const { upcoming, past } = useMemo(() => {
    const today = new Date(new Date().toDateString())
    const up = []
    const pa = []
    for (const appt of appointments) {
      const apptDate = new Date(appt.date)
      const isCancelled = appt.booking_status === 'cancelled'
      const isPast = apptDate < today || appt.booking_status === 'completed'
      if (isPast || isCancelled) pa.push(appt)
      else up.push(appt)
    }
    up.sort((a, b) => a.date.localeCompare(b.date))
    pa.sort((a, b) => b.date.localeCompare(a.date))
    return { upcoming: up, past: pa }
  }, [appointments])

  async function handleCancel(appointmentId) {
    if (!confirm('Cancel this appointment?')) return
    try {
      await cancelAppointment(appointmentId)
      toast.success('Appointment cancelled.')
      // Refresh
      setAppointments((prev) =>
        prev.map((a) =>
          a.id === appointmentId ? { ...a, booking_status: 'cancelled' } : a,
        ),
      )
    } catch (err) {
      toast.error(err?.message || 'Failed to cancel.')
    }
  }

  const displayList = filter === 'upcoming' ? upcoming : filter === 'past' ? past : [...upcoming, ...past]

  return (
    <div className="flex flex-1 flex-col">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            My Appointments
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Upcoming visits and past triage bookings.
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-800"
        >
          <MessageSquareText className="h-4 w-4" aria-hidden />
          New Triage
        </Link>
      </div>

      {/* Filter tabs */}
      <div className="mb-5 flex gap-1 rounded-xl bg-slate-100 p-1 self-start">
        {['all', 'upcoming', 'past'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`rounded-lg px-4 py-1.5 text-xs font-semibold transition ${
              filter === tab
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="ml-1.5 text-[10px] font-medium text-slate-400">
              {tab === 'all'
                ? appointments.length
                : tab === 'upcoming'
                  ? upcoming.length
                  : past.length}
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      {loading && (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
          Loading appointments…
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && displayList.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center">
          <CalendarDays className="mb-3 h-10 w-10 text-slate-300" aria-hidden />
          <p className="text-base font-medium text-slate-800">
            No appointments {filter !== 'all' ? `(${filter})` : 'yet'}
          </p>
          <p className="mt-1 max-w-sm text-sm text-slate-500">
            Start a triage chat to get guided care and book a visit.
          </p>
          <Link
            to="/"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 px-4 py-2.5 text-sm font-semibold text-white hover:from-brand-700 hover:to-brand-800"
          >
            Open Triage Assistant
          </Link>
        </div>
      )}

      {!loading && !error && displayList.length > 0 && (
        <ul className="space-y-3">
          {displayList.map((appt) => (
            <BookingCard
              key={appt.id}
              appointment={appt}
              onCancel={handleCancel}
            />
          ))}
        </ul>
      )}
    </div>
  )
}
