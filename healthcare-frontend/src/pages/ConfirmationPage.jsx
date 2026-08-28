import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Hash,
  Stethoscope,
  MessageSquareText,
} from 'lucide-react'
import { saveLocalAppointment } from '../services/api'

export default function ConfirmationPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const booking = location.state?.booking

  useEffect(() => {
    if (!booking) {
      navigate('/', { replace: true })
      return
    }
    saveLocalAppointment({ ...booking, status: 'Confirmed' })
  }, [booking, navigate])

  if (!booking) {
    return null
  }

  const doctor =
    booking.doctor_name || booking.doctor_id || 'Assigned clinician'
  const date = booking.date || '—'
  const time = booking.time_slot || booking.time || '—'
  const bookingId =
    booking.booking_id ||
    booking.appointment_id ||
    booking.id ||
    '—'

  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-card">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-8 ring-emerald-50/60">
          <CheckCircle2 className="h-9 w-9" strokeWidth={2} aria-hidden />
        </div>

        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Appointment Confirmed
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Your visit is booked. A summary is saved under My Appointments.
        </p>

        <dl className="mt-8 space-y-3 text-left">
          <DetailRow
            icon={Stethoscope}
            label="Doctor"
            value={doctor}
          />
          <DetailRow icon={CalendarDays} label="Date" value={date} />
          <DetailRow icon={Clock3} label="Time Slot" value={time} />
          <DetailRow
            icon={Hash}
            label="Booking ID"
            value={String(bookingId)}
          />
        </dl>

        <div className="mt-8 flex flex-col gap-2.5 sm:flex-row sm:justify-center">
          <Link
            to="/appointments"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:bg-teal-700"
          >
            <CalendarDays className="h-4 w-4" aria-hidden />
            View All Appointments
          </Link>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800"
          >
            <MessageSquareText className="h-4 w-4" aria-hidden />
            Start New Triage
          </Link>
        </div>
      </div>
    </div>
  )
}

function DetailRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-teal-700 shadow-sm">
        <Icon className="h-4 w-4" aria-hidden />
      </div>
      <div className="min-w-0">
        <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </dt>
        <dd className="truncate text-sm font-semibold text-slate-900">
          {value}
        </dd>
      </div>
    </div>
  )
}
