import { CalendarDays, Clock3, IndianRupee, MapPin, Stethoscope } from 'lucide-react'
import StatusBadge from './StatusBadge'

export default function BookingCard({ appointment, onCancel }) {
  const canCancel =
    appointment.booking_status === 'confirmed' &&
    new Date(appointment.date) >= new Date(new Date().toDateString())

  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft transition-all duration-200 hover:border-brand-100 hover:shadow-card sm:p-5 animate-fade-in-up">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-2 flex-1">
          <div className="flex items-center gap-2 text-base font-semibold text-slate-900">
            <Stethoscope className="h-4 w-4 shrink-0 text-brand-600" aria-hidden />
            <span className="truncate">{appointment.doctor_name || 'Doctor'}</span>
            {appointment.specialty && (
              <span className="hidden rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700 sm:inline">
                {appointment.specialty}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              {appointment.date || '—'}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock3 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              {appointment.time_slot || '—'}
            </span>
            {appointment.clinic_name && (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400" aria-hidden />
                {appointment.clinic_name}
              </span>
            )}
            {appointment.consultation_fee > 0 && (
              <span className="inline-flex items-center gap-1.5">
                <IndianRupee className="h-3.5 w-3.5 text-slate-400" aria-hidden />
                ₹{appointment.consultation_fee}
              </span>
            )}
          </div>
          {appointment.reason_for_visit && (
            <p className="text-xs text-slate-500 italic">
              {appointment.reason_for_visit}
            </p>
          )}
          <p className="text-xs text-slate-400">
            Booking #{appointment.id}
            {appointment.severity && (
              <span className="ml-2">· Severity: {appointment.severity}</span>
            )}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={appointment.booking_status} />
          {canCancel && onCancel && (
            <button
              onClick={() => onCancel(appointment.id)}
              className="rounded-lg border border-red-200 bg-white px-3 py-1 text-xs font-medium text-red-600 transition hover:bg-red-50 hover:text-red-700"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </li>
  )
}
