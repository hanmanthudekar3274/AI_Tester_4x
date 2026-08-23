import { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronDown, X } from 'lucide-react'
import { JOB_STATUSES } from '../types/index'
import { STATUS_CONFIG } from '../utils/statusConfig'

function StatusDropdown({ selected, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (!ref.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const toggle = useCallback((status) => {
    onChange(
      selected.includes(status)
        ? selected.filter((s) => s !== status)
        : [...selected, status],
    )
  }, [selected, onChange])

  const label =
    selected.length === 0
      ? 'All Statuses'
      : selected.length === 1
      ? STATUS_CONFIG[selected[0]]?.label ?? selected[0]
      : `${selected.length} statuses`

  const isActive = selected.length > 0

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors whitespace-nowrap
          ${isActive
            ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
            : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
          }`}
      >
        {label}
        <ChevronDown size={13} className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1.5 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl shadow-black/50 z-30 py-1.5 min-w-[176px]">
          {JOB_STATUSES.map((status) => {
            const cfg     = STATUS_CONFIG[status]
            const checked = selected.includes(status)
            return (
              <label
                key={status}
                className="flex items-center gap-2.5 px-3 py-2 hover:bg-gray-700/60 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(status)}
                  className="w-3.5 h-3.5 rounded accent-indigo-500 cursor-pointer"
                />
                <span className={`w-2 h-2 rounded-full shrink-0 ${cfg.dot}`} />
                <span className={`text-sm ${checked ? 'text-gray-100' : 'text-gray-400'}`}>
                  {cfg.label}
                </span>
              </label>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function FilterBar({ filters, onFilterChange, availableResumes, hasActiveFilters, onClearAll }) {
  const handleStatusChange = useCallback(
    (status) => onFilterChange({ ...filters, status }),
    [filters, onFilterChange],
  )

  const handleResumeChange = useCallback(
    (e) => onFilterChange({ ...filters, resume: e.target.value }),
    [filters, onFilterChange],
  )

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Status multi-select */}
      <StatusDropdown selected={filters.status} onChange={handleStatusChange} />

      {/* Resume single-select */}
      <div className="relative">
        <select
          value={filters.resume}
          onChange={handleResumeChange}
          className={`appearance-none pl-3 pr-7 py-2 text-sm rounded-lg border transition-colors cursor-pointer
            focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30
            ${filters.resume
              ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
            }`}
        >
          <option value="">All Resumes</option>
          {availableResumes.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <ChevronDown
          size={13}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
        />
      </div>

      {/* Clear All — only when any filter active */}
      {hasActiveFilters && (
        <button
          onClick={onClearAll}
          className="flex items-center gap-1 px-2.5 py-2 text-xs text-gray-500 hover:text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <X size={12} />
          Clear all
        </button>
      )}
    </div>
  )
}
