import { Search, X } from 'lucide-react'

export default function SearchBar({ value, onChange }) {
  return (
    <div className="relative flex-1">
      <Search
        size={15}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search by company or role..."
        className={`
          w-full bg-gray-800 border border-gray-700 rounded-lg
          pl-9 pr-8 py-2 text-sm text-gray-100
          placeholder:text-gray-600
          focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30
          transition-colors
        `}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-gray-600 hover:text-gray-300 hover:bg-gray-700 transition-colors"
          aria-label="Clear search"
        >
          <X size={13} />
        </button>
      )}
    </div>
  )
}
