import clsx from 'clsx'

const STATUS_STYLES = {
  confirmed: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  completed: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
  cancelled: 'bg-red-50 text-red-600 ring-1 ring-red-200',
}

export default function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase()
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1)

  return (
    <span
      className={clsx(
        'inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold',
        STATUS_STYLES[normalized] || 'bg-brand-50 text-brand-700 ring-1 ring-brand-100',
      )}
    >
      {label}
    </span>
  )
}
