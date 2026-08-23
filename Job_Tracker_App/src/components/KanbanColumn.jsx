import { useDroppable } from '@dnd-kit/core'
import { Plus } from 'lucide-react'
import { STATUS_CONFIG } from '../utils/statusConfig'
import { COLUMN_MESSAGES } from '../config/messages'
import JobCard from './JobCard'

export default function KanbanColumn({ status, jobs, onAddJob, onSelectJob }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.wishlist
  const msg    = COLUMN_MESSAGES[status] ?? {}
  const { setNodeRef, isOver } = useDroppable({ id: status })

  return (
    <div
      ref={setNodeRef}
      className={[
        'flex flex-col w-72 shrink-0 rounded-xl border transition-all duration-150 h-full',
        isOver
          ? 'bg-blue-950/50 border-blue-500/50 shadow-lg shadow-blue-500/10'
          : 'bg-gray-900/60 border-gray-800',
      ].join(' ')}
    >
      {/* Column header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${config.dot}`} aria-hidden="true" />
          <h3 className={`text-sm font-semibold ${config.headerText}`}>{config.label}</h3>
          <span
            className="text-xs text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded-full tabular-nums"
            aria-label={`${jobs.length} job${jobs.length !== 1 ? 's' : ''}`}
          >
            {jobs.length}
          </span>
        </div>
        <button
          onClick={() => onAddJob?.(status)}
          className="p-1 rounded-md text-gray-600 hover:text-gray-300 hover:bg-gray-800 transition-colors
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1 focus-visible:ring-offset-gray-900"
          aria-label={`Add job to ${config.label}`}
        >
          <Plus size={14} />
        </button>
      </div>

      {/* Cards list */}
      <div
        className={[
          'flex-1 overflow-y-auto p-3 space-y-2 min-h-[120px]',
          'rounded-b-xl transition-colors duration-150',
          isOver ? 'bg-blue-500/5' : '',
        ].join(' ')}
        role="list"
        aria-label={`${config.label} jobs`}
      >
        {jobs.map((job) => (
          <div key={job.id} role="listitem">
            <JobCard job={job} onClick={onSelectJob} />
          </div>
        ))}

        {jobs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 gap-2 px-3 text-center">
            {isOver ? (
              <p className="text-xs text-blue-400 font-medium">{msg.dropHint ?? 'Drop here'}</p>
            ) : (
              <>
                <p className="text-xs text-gray-600 font-medium">{msg.empty ?? 'No jobs yet'}</p>
                <p className="text-xs text-gray-700 leading-relaxed">{msg.sub}</p>
                <button
                  onClick={() => onAddJob?.(status)}
                  className="mt-1 text-xs text-gray-700 hover:text-gray-400 flex items-center gap-1 transition-colors
                    focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-500 rounded"
                  aria-label={msg.cta ?? `Add job to ${config.label}`}
                >
                  <Plus size={12} />
                  {msg.cta ?? 'Add one'}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
