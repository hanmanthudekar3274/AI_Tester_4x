import { useEffect } from 'react'
import { X, BarChart3 } from 'lucide-react'
import Analytics from './Analytics'

export default function AnalyticsModal({ isOpen, onClose, jobs }) {
  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Job Search Analytics"
      className={`fixed inset-0 z-50 flex items-center justify-center p-4
        transition-opacity duration-200 ease-out
        ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className={`relative w-full max-w-5xl max-h-[92vh] bg-gray-900 rounded-2xl border border-gray-700/80
          shadow-2xl shadow-black/60 flex flex-col
          transition-transform duration-200 ease-out
          ${isOpen ? 'scale-100' : 'scale-95'}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-indigo-600/20 rounded-lg">
              <BarChart3 size={16} className="text-indigo-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Job Search Analytics</h2>
              <p className="text-xs text-gray-500">{jobs.length} total job{jobs.length !== 1 ? 's' : ''} tracked</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
            aria-label="Close analytics"
          >
            <X size={16} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-5">
          {jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-600">
              <BarChart3 size={32} className="opacity-30" />
              <p className="text-sm">Add some jobs to see analytics</p>
            </div>
          ) : (
            <Analytics jobs={jobs} />
          )}
        </div>
      </div>
    </div>
  )
}
