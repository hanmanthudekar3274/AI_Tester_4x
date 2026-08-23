import { STATUS_CONFIG } from '../utils/statusConfig'

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.wishlist
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${config.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  )
}
