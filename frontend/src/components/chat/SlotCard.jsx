import { Clock3, MapPin, Star, Stethoscope, IndianRupee } from 'lucide-react'

export default function SlotCard({ slot, onBook, disabled = false }) {
  if (!slot) return null

  const ratingStars = Math.round(slot.rating || 0)

  return (
    <div className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-soft transition-all duration-200 hover:border-brand-200 hover:shadow-card animate-fade-in-up">
      {/* Doctor Info */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
              <Stethoscope className="h-4 w-4" aria-hidden />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">
                {slot.doctor_name}
              </p>
              <p className="text-xs text-brand-600 font-medium">
                {slot.specialty}
              </p>
            </div>
          </div>
        </div>
        {/* Rating */}
        <div className="flex items-center gap-0.5 shrink-0" title={`${slot.rating} rating`}>
          {[...Array(5)].map((_, i) => (
            <Star
              key={i}
              className={`h-3 w-3 ${i < ratingStars ? 'fill-amber-400 text-amber-400' : 'text-slate-200'}`}
              aria-hidden
            />
          ))}
          <span className="ml-1 text-[11px] font-medium text-slate-500">{slot.rating}</span>
        </div>
      </div>

      {/* Details */}
      <div className="mb-3 space-y-1.5">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <Clock3 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
          <span className="font-medium">{slot.date}</span>
          <span className="text-slate-300">·</span>
          <span>{slot.time_slot}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <MapPin className="h-3.5 w-3.5 text-slate-400" aria-hidden />
          <span className="truncate">{slot.clinic_name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <IndianRupee className="h-3.5 w-3.5 text-slate-400" aria-hidden />
          <span className="font-semibold text-slate-800">₹{slot.fee}</span>
          <span className="text-slate-400">consultation fee</span>
        </div>
      </div>

      {/* Book Button */}
      <button
        type="button"
        onClick={() => onBook(slot)}
        disabled={disabled}
        className="w-full rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all duration-200 hover:from-brand-700 hover:to-brand-800 hover:shadow-soft disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98]"
      >
        Book This Slot
      </button>
    </div>
  )
}
