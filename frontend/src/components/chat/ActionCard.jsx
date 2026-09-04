import { CalendarCheck2, IndianRupee, MapPin, Stethoscope } from 'lucide-react'

export default function ActionCard({ booking }) {
  if (!booking) return null

  return (
    <div className="mx-auto max-w-sm animate-fade-in-up">
      <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-brand-50 p-4 shadow-soft">
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <CalendarCheck2 className="h-4 w-4" aria-hidden />
          </div>
          <p className="text-sm font-semibold text-emerald-800">
            Appointment Confirmed — Redirecting…
          </p>
        </div>
        <div className="space-y-1.5 text-sm text-slate-700">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-3.5 w-3.5 text-slate-400" aria-hidden />
            <span className="font-medium">{booking.doctor_name}</span>
            {booking.specialty && (
              <span className="text-xs text-slate-500">· {booking.specialty}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <CalendarCheck2 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
            <span>{booking.date} at {booking.time_slot}</span>
          </div>
          {booking.clinic_name && (
            <div className="flex items-center gap-2">
              <MapPin className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              <span className="text-xs">{booking.clinic_name}</span>
            </div>
          )}
          {booking.fee > 0 && (
            <div className="flex items-center gap-2">
              <IndianRupee className="h-3.5 w-3.5 text-slate-400" aria-hidden />
              <span className="text-xs font-semibold">₹{booking.fee}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
