import { X, Award } from 'lucide-react'

function parseAmount(str) {
  if (!str) return 0
  const n = parseFloat(String(str).replace(/[^0-9.]/g, ''))
  return isNaN(n) ? 0 : n
}

function fmt(amount, currency = 'USD') {
  if (!amount) return null
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

function deadlineLabel(isoDate) {
  if (!isoDate) return null
  const days = Math.ceil((new Date(isoDate) - Date.now()) / 86_400_000)
  const label = days >= 0 ? `(${days}d left)` : '(expired)'
  return `${isoDate} ${label}`
}

function Row({ label, values, highlight = false, maxIdx = -1, color = null }) {
  return (
    <tr className={`border-b border-gray-800 ${highlight ? 'bg-gray-800/30' : ''}`}>
      <td className="py-3 px-4 text-xs font-medium text-gray-500 whitespace-nowrap">{label}</td>
      {values.map((val, i) => (
        <td
          key={i}
          className={[
            'py-3 px-4 text-sm text-center',
            maxIdx === i ? 'text-emerald-400 font-bold' : 'text-white',
          ].join(' ')}
        >
          {val ?? <span className="text-gray-700">—</span>}
        </td>
      ))}
    </tr>
  )
}

export default function OfferComparison({ isOpen, onClose, offerJobs }) {
  if (!offerJobs?.length) return null

  const bases   = offerJobs.map((j) => parseAmount(j.offerDetails?.baseSalary))
  const maxBase = Math.max(...bases)
  const maxIdx  = bases.indexOf(maxBase)

  const rows = [
    {
      label:  'Base Salary',
      values: offerJobs.map((j, i) => fmt(bases[i], j.offerDetails?.currency)),
      highlight: true,
      maxIdx: maxBase > 0 ? maxIdx : -1,
    },
    {
      label:  'Currency',
      values: offerJobs.map((j) => j.offerDetails?.currency || 'USD'),
    },
    {
      label:  'Bonus',
      values: offerJobs.map((j) => j.offerDetails?.bonus || null),
    },
    {
      label:  'Stock / Equity',
      values: offerJobs.map((j) => j.offerDetails?.stockOptions || null),
    },
    {
      label:  'Benefits',
      values: offerJobs.map((j) => j.offerDetails?.benefits || null),
    },
    {
      label:  'Start Date',
      values: offerJobs.map((j) => j.offerDetails?.startDate || null),
    },
    {
      label:  'Deadline',
      values: offerJobs.map((j) => deadlineLabel(j.offerDetails?.deadline)),
    },
    {
      label:  'Location',
      values: offerJobs.map((j) => j.location || null),
    },
    {
      label:  'Notes',
      values: offerJobs.map((j) => j.offerDetails?.notes || null),
    },
  ]

  return (
    <div
      className={[
        'fixed inset-0 z-50 flex items-center justify-center p-4 transition-opacity duration-200',
        isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
      ].join(' ')}
    >
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div
        className={[
          'relative w-full max-w-4xl max-h-[90vh] bg-gray-900 rounded-2xl border border-gray-700/80',
          'shadow-2xl flex flex-col transition-transform duration-200',
          isOpen ? 'scale-100' : 'scale-95',
        ].join(' ')}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-emerald-600/20 rounded-lg">
              <Award size={16} className="text-emerald-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Offer Comparison</h2>
              <p className="text-xs text-gray-500">{offerJobs.length} offers · base salary highlighted in green</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Table */}
        <div className="overflow-auto flex-1">
          <table className="w-full">
            <thead className="sticky top-0 bg-gray-900 z-10">
              <tr className="border-b border-gray-700">
                <th className="py-3 px-4 text-left text-xs text-gray-600 font-medium w-36">Field</th>
                {offerJobs.map((job) => (
                  <th key={job.id} className="py-3 px-4 text-center">
                    <p className="text-sm font-bold text-white">{job.companyName}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{job.jobTitle}</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <Row key={row.label} {...row} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
