import { Compass, Plus, Lock, WifiOff, Download } from 'lucide-react'
import { EMPTY_BOARD } from '../config/messages'

const FEATURES = [
  { icon: Lock,     label: '100% private' },
  { icon: WifiOff,  label: 'Works offline' },
  { icon: Download, label: 'Export anytime' },
]

export default function EmptyStateHero({ onAddJob }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 py-16 px-6 text-center">
      {/* Logo mark */}
      <div className="relative">
        <div className="absolute inset-0 bg-primary-600/20 rounded-3xl blur-xl" />
        <div className="relative p-5 bg-gray-900 border border-primary-500/30 rounded-2xl shadow-xl">
          <Compass size={52} className="text-primary-400" strokeWidth={1.5} />
        </div>
      </div>

      {/* Heading */}
      <div className="space-y-3 max-w-sm">
        <h2 className="text-2xl font-bold text-white tracking-tight">{EMPTY_BOARD.heading}</h2>
        <p className="text-sm text-gray-400 leading-relaxed">{EMPTY_BOARD.sub}</p>
      </div>

      {/* CTA */}
      <button
        onClick={() => onAddJob('wishlist')}
        className="flex items-center gap-2 px-6 py-3 text-sm font-semibold rounded-xl
          bg-primary-600 hover:bg-primary-500 text-white
          shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40
          transition-all duration-200 active:scale-[0.97]
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
        aria-label="Add your first job application"
      >
        <Plus size={16} />
        {EMPTY_BOARD.cta}
      </button>

      {/* Feature pills */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {FEATURES.map(({ icon: Icon, label }) => (
          <span
            key={label}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs text-gray-600 bg-gray-900 border border-gray-800"
          >
            <Icon size={11} className="text-gray-700" />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
