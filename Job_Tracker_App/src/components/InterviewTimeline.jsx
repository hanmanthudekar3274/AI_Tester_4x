import { useMemo } from 'react'
import { MapPin, DollarSign, FileText, ExternalLink, Clock } from 'lucide-react'
import { STATUS_CONFIG } from '../utils/statusConfig'
import { daysAgo } from '../utils/helpers'

export default function InterviewTimeline({ jobs, onSelectJob }) {
  const sorted = useMemo(
    () => [...jobs].sort((a, b) => {
      const da = new Date(a.appliedDate || a.createdAt)
      const db = new Date(b.appliedDate || b.createdAt)
      return db - da
    }),
    [jobs],
  )

  if (sorted.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-gray-600 text-sm">
        <Clock size={32} className="opacity-20" />
        No jobs yet. Add your first application to see the timeline.
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-5">
      <div className="max-w-2xl mx-auto relative">
        {/* Vertical line */}
        <div className="absolute left-4 top-2 bottom-2 w-px bg-gray-800" />

        <div className="space-y-3">
          {sorted.map((job) => {
            const cfg      = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.wishlist
            const days     = daysAgo(job.appliedDate || job.createdAt)
            const dayLabel = days === 0 ? 'Today' : days === 1 ? '1 day ago' : `${days} days ago`

            return (
              <div key={job.id} className="relative pl-12">
                {/* Status dot on the line */}
                <div className={`absolute left-2 top-4 w-4 h-4 rounded-full border-2 border-gray-950 ${cfg.dot}`} />

                {/* Card */}
                <button
                  className="w-full text-left bg-gray-900/80 border border-gray-800 rounded-xl p-4
                    hover:border-gray-700 hover:bg-gray-900 transition-colors"
                  onClick={() => onSelectJob(job)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-white">{job.companyName}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{job.jobTitle}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.badge}`}>
                        {cfg.label}
                      </span>
                      {job.url && (
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-gray-600 hover:text-indigo-400 transition-colors"
                        >
                          <ExternalLink size={13} />
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2.5">
                    {job.location && (
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <MapPin size={10} />
                        {job.location}
                      </span>
                    )}
                    {job.salary && (
                      <span className="flex items-center gap-1 text-xs text-emerald-600">
                        <DollarSign size={10} />
                        {job.salary}
                      </span>
                    )}
                    {job.resumeTag && (
                      <span className="flex items-center gap-1 text-xs text-indigo-500">
                        <FileText size={10} />
                        {job.resumeTag}
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-xs text-gray-700 ml-auto">
                      <Clock size={10} />
                      {dayLabel}
                    </span>
                  </div>
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
