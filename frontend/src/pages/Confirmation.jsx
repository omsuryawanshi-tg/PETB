import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Download,
  MapPin,
  MessageSquareText,
  Stethoscope,
  Tag,
} from 'lucide-react'

export default function Confirmation() {
  const location = useLocation()
  const navigate = useNavigate()
  const booking = location.state?.booking

  useEffect(() => {
    if (!booking) {
      navigate('/', { replace: true })
    }
  }, [booking, navigate])

  if (!booking) return null

  const doctor = booking.doctor_name || 'Assigned Clinician'
  const specialty = booking.specialty || ''
  const dateStr = booking.date || '—'
  const time = booking.time || booking.time_slot || '—'
  const clinic = booking.clinic || ''
  const bookingId = booking.appointment_id || booking.id || '—'

  function generateICS() {
    const dtStart = dateStr.replace(/-/g, '') + 'T' + (time.replace(/[: ]/g, '').replace(/AM|PM/i, '') || '0900') + '00'
    const icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'BEGIN:VEVENT',
      `DTSTART:${dtStart}`,
      `SUMMARY:Appointment with ${doctor}`,
      `DESCRIPTION:${specialty} consultation at ${clinic}`,
      `LOCATION:${clinic}`,
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n')

    const blob = new Blob([icsContent], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `appointment_${bookingId}.ics`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center animate-fade-in-up">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-card">
        {/* Success icon */}
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-8 ring-emerald-50/60 shadow-glow-teal">
          <CheckCircle2 className="h-9 w-9" strokeWidth={2} aria-hidden />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Appointment Confirmed
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Your visit has been booked. Here's your digital appointment slip.
        </p>

        {/* Details */}
        <dl className="mt-8 space-y-3 text-left">
          <DetailRow icon={Stethoscope} label="Doctor" value={doctor} />
          {specialty && <DetailRow icon={Tag} label="Specialty" value={specialty} />}
          <DetailRow icon={CalendarDays} label="Date" value={dateStr} />
          <DetailRow icon={Clock3} label="Time" value={time} />
          {clinic && <DetailRow icon={MapPin} label="Clinic" value={clinic} />}
          <DetailRow icon={Tag} label="Booking Ref" value={`#${bookingId}`} />
        </dl>

        {/* Actions */}
        <div className="mt-8 flex flex-col gap-2.5 sm:flex-row sm:justify-center">
          <Link
            to="/appointments"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 px-5 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:from-brand-700 hover:to-brand-800"
          >
            <CalendarDays className="h-4 w-4" aria-hidden />
            View Appointments
          </Link>
          <button
            onClick={generateICS}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-800"
          >
            <Download className="h-4 w-4" aria-hidden />
            Add to Calendar
          </button>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-800"
          >
            <MessageSquareText className="h-4 w-4" aria-hidden />
            New Triage
          </Link>
        </div>
      </div>
    </div>
  )
}

function DetailRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-brand-700 shadow-sm">
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
