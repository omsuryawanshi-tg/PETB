import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CalendarDays,
  Clock3,
  Loader2,
  MessageSquareText,
  Stethoscope,
} from 'lucide-react'
import { getAppointmentHistory } from '../services/api'
import clsx from 'clsx'

function normalizeStatus(raw) {
  const s = String(raw || '').toLowerCase()
  if (['completed', 'done', 'past'].includes(s)) return 'Completed'
  if (['confirmed', 'booked', 'scheduled'].includes(s)) return 'Confirmed'
  if (s) return s.charAt(0).toUpperCase() + s.slice(1)
  return 'Confirmed'
}

function parseDate(value) {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

function isPastAppointment(appt) {
  const status = normalizeStatus(appt.status)
  if (status === 'Completed') return true
  const d = parseDate(appt.date)
  if (!d) return false
  const endOfDay = new Date(d)
  endOfDay.setHours(23, 59, 59, 999)
  return endOfDay < new Date()
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await getAppointmentHistory()
        if (!cancelled) {
          setAppointments(Array.isArray(data) ? data : [])
        }
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
    return () => {
      cancelled = true
    }
  }, [])

  const { upcoming, past } = useMemo(() => {
    const up = []
    const pa = []
    for (const appt of appointments) {
      if (isPastAppointment(appt)) pa.push(appt)
      else up.push(appt)
    }
    const byDate = (a, b) =>
      String(a.date || '').localeCompare(String(b.date || ''))
    up.sort(byDate)
    pa.sort((a, b) => byDate(b, a))
    return { upcoming: up, past: pa }
  }, [appointments])

  return (
    <div className="flex flex-1 flex-col">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            My Appointments
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Upcoming visits and past triage bookings.
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800"
        >
          <MessageSquareText className="h-4 w-4" aria-hidden />
          New Triage
        </Link>
      </div>

      {loading && (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin text-teal-600" />
          Loading appointments…
        </div>
      )}

      {!loading && error && (
        <div
          className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && appointments.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center">
          <CalendarDays className="mb-3 h-10 w-10 text-slate-300" aria-hidden />
          <p className="text-base font-medium text-slate-800">
            No appointments yet
          </p>
          <p className="mt-1 max-w-sm text-sm text-slate-500">
            Start a triage chat to get guided care and book a visit when
            needed.
          </p>
          <Link
            to="/"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
          >
            Open Triage Assistant
          </Link>
        </div>
      )}

      {!loading && !error && appointments.length > 0 && (
        <div className="space-y-8">
          <AppointmentSection
            title="Upcoming"
            items={upcoming}
            emptyLabel="No upcoming appointments."
          />
          <AppointmentSection
            title="Past"
            items={past}
            emptyLabel="No past appointments."
            forceStatus="Completed"
          />
        </div>
      )}
    </div>
  )
}

function AppointmentSection({ title, items, emptyLabel, forceStatus }) {
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        {title}
        <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 normal-case tracking-normal">
          {items.length}
        </span>
      </h2>
      {items.length === 0 ? (
        <p className="rounded-xl border border-slate-100 bg-white px-4 py-6 text-sm text-slate-400">
          {emptyLabel}
        </p>
      ) : (
        <ul className="space-y-3">
          {items.map((appt, idx) => (
            <AppointmentCard
              key={appt.id ?? appt.booking_id ?? `${appt.date}-${idx}`}
              appt={appt}
              statusOverride={forceStatus}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

function AppointmentCard({ appt, statusOverride }) {
  const status = normalizeStatus(statusOverride || appt.status)
  const doctor = appt.doctor_name || appt.doctor_id || 'Clinician'
  const bookingId = appt.booking_id || appt.appointment_id || appt.id

  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft transition hover:border-teal-100 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <div className="flex items-center gap-2 text-base font-semibold text-slate-900">
            <Stethoscope className="h-4 w-4 shrink-0 text-teal-600" aria-hidden />
            <span className="truncate">{doctor}</span>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              {appt.date || '—'}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock3 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              {appt.time_slot || appt.time || '—'}
            </span>
          </div>
          {bookingId != null && (
            <p className="text-xs text-slate-400">
              Booking ID · {String(bookingId)}
            </p>
          )}
        </div>
        <StatusBadge status={status} />
      </div>
    </li>
  )
}

function StatusBadge({ status }) {
  const confirmed = status === 'Confirmed'
  const completed = status === 'Completed'

  return (
    <span
      className={clsx(
        'inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold',
        confirmed && 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100',
        completed && 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
        !confirmed &&
          !completed &&
          'bg-teal-50 text-teal-700 ring-1 ring-teal-100',
      )}
    >
      {status}
    </span>
  )
}
