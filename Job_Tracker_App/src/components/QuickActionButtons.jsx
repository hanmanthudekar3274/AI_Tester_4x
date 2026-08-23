import { useState } from 'react'
import { ChevronRight, XCircle, Trash2, RotateCcw } from 'lucide-react'
import { STATUS_LABELS } from '../types/index'

const STATUS_FLOW = {
  wishlist:     'applied',
  applied:      'phone_screen',
  phone_screen: 'interview',
  interview:    'offer',
  offer:        null,
  rejected:     null,
}

export default function QuickActionButtons({ job, onUpdate, onDelete }) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const nextStatus = STATUS_FLOW[job.status]

  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2 flex-wrap">
        {nextStatus && (
          <button
            onClick={() => onUpdate({ status: nextStatus })}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
              bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            <ChevronRight size={13} />
            Move to {STATUS_LABELS[nextStatus]}
          </button>
        )}
        {job.status !== 'rejected' && job.status !== 'wishlist' && (
          <button
            onClick={() => onUpdate({ status: 'rejected' })}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
              border border-gray-700 bg-gray-800 text-gray-400
              hover:text-red-400 hover:border-red-500/50 transition-colors"
          >
            <XCircle size={13} />
            Reject
          </button>
        )}
        {job.status === 'rejected' && (
          <button
            onClick={() => onUpdate({ status: 'applied' })}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg
              border border-gray-700 bg-gray-800 text-gray-400
              hover:text-amber-400 hover:border-amber-500/50 transition-colors"
          >
            <RotateCcw size={13} />
            Reopen
          </button>
        )}
      </div>

      {!confirmDelete ? (
        <button
          onClick={() => setConfirmDelete(true)}
          className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Delete this job"
        >
          <Trash2 size={14} />
        </button>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Delete?</span>
          <button
            onClick={onDelete}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors"
          >
            Yes
          </button>
          <button
            onClick={() => setConfirmDelete(false)}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
          >
            No
          </button>
        </div>
      )}
    </div>
  )
}
