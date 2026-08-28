export default function QuickChips({ prompts, onSelect, disabled = false }) {
  if (!prompts?.length) return null

  return (
    <div className="flex flex-wrap gap-2 border-t border-slate-100 px-4 py-3 sm:px-6">
      {prompts.map((prompt) => (
        <button
          key={prompt}
          type="button"
          onClick={() => onSelect(prompt)}
          disabled={disabled}
          className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-left text-xs font-medium text-slate-600 shadow-sm transition-all duration-200 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-800 hover:shadow-soft disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}
