import { useDraggable } from '@dnd-kit/core'
import { MapPin, DollarSign, ExternalLink, FileText, Clock, Award, MessageSquare, XCircle } from 'lucide-react'
import { STATUS_CONFIG } from '../utils/statusConfig'
import { daysAgo } from '../utils/helpers'

export default function JobCard({ job, overlay = false, onClick }) {
  const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
    id:       job.id,
    disabled: overlay,
    data:     { job },
  })

  const config   = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.wishlist
  const days     = daysAgo(job.createdAt)
  const dayLabel = days === 0 ? 'Today' : days === 1 ? '1 day ago' : `${days} days ago`
  const isLinkedIn = job.url?.includes('linkedin.com')

  const hasOffer      = job.status === 'offer' && job.offerDetails?.baseSalary
  const hasFeedback   = ['interview', 'offer', 'phone_screen'].includes(job.status) && job.interviewFeedback?.interviewNotes
  const hasRejection  = job.status === 'rejected' && job.interviewFeedback?.rejectionReason

  const showBadges = hasOffer || hasFeedback || hasRejection || job.resumeTag

  return (
    <div
      ref={overlay ? undefined : setNodeRef}
      {...(overlay ? {} : { ...listeners, ...attributes })}
      style={{ touchAction: overlay ? undefined : 'none' }}
      onClick={!overlay && onClick ? () => onClick(job) : undefined}
      onKeyDown={!overlay && onClick
        ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(job) } }
        : undefined}
      aria-label={!overlay ? `${job.companyName} – ${job.jobTitle}, ${config.label}` : undefined}
      className={[
        'bg-gray-800 rounded-lg border border-l-4 p-3.5 space-y-2.5 select-none',
        config.border,
        'transition-[opacity,transform,box-shadow] duration-150 ease-out',
        !overlay && isDragging
          ? 'opacity-40 scale-[0.97] border-gray-700/40 shadow-none'
          : 'opacity-100 scale-100 border-gray-700/60',
        overlay
          ? 'cursor-grabbing shadow-2xl shadow-black/60 rotate-[0.7deg] border-gray-600'
          : 'cursor-pointer active:cursor-grabbing hover:border-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900',
      ].join(' ')}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white leading-snug truncate">{job.companyName}</p>
          <p className="text-xs text-gray-400 mt-0.5 leading-snug line-clamp-2">{job.jobTitle}</p>
        </div>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="shrink-0 p-1 rounded text-gray-600 hover:text-indigo-400 hover:bg-gray-700 transition-colors"
            aria-label={isLinkedIn ? 'Open LinkedIn posting' : 'Open job posting'}
          >
            <ExternalLink size={13} />
          </a>
        )}
      </div>

      {/* Location / Salary */}
      {(job.location || job.salary) && (
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {job.location && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <MapPin size={11} className="shrink-0" />
              {job.location}
            </span>
          )}
          {job.salary && (
            <span className="flex items-center gap-1 text-xs font-medium text-emerald-400">
              <DollarSign size={11} className="shrink-0" />
              {job.salary}
            </span>
          )}
        </div>
      )}

      {/* Badges */}
      {showBadges && (
        <div className="flex flex-wrap gap-1.5">
          {job.resumeTag && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/20">
              <FileText size={10} />
              {job.resumeTag}
            </span>
          )}
          {hasOffer && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
              <Award size={10} />
              Offer logged
            </span>
          )}
          {hasFeedback && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-300 border border-orange-500/20">
              <MessageSquare size={10} />
              Notes
            </span>
          )}
          {hasRejection && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-300 border border-red-500/20">
              <XCircle size={10} />
              Reason logged
            </span>
          )}
        </div>
      )}

      {/* Notes */}
      {job.notes && (
        <p className="text-xs text-gray-500 italic line-clamp-2 leading-relaxed">{job.notes}</p>
      )}

      {/* Footer */}
      <div className="flex items-center gap-1 text-xs text-gray-600 pt-0.5 border-t border-gray-700/50">
        <Clock size={10} className="shrink-0" />
        {dayLabel}
      </div>
    </div>
  )
}
