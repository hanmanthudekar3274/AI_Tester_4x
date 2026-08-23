import { useRef } from 'react'
import { Download, Upload, Loader2 } from 'lucide-react'

export default function ExportImportMenu({ onExport, onImport, isExporting }) {
  const fileInputRef = useRef(null)

  function handleImportClick() {
    fileInputRef.current?.click()
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      onImport(file)
      e.target.value = '' // reset so same file can be re-selected
    }
  }

  return (
    <div className="flex items-center gap-1.5">
      {/* Export */}
      <button
        onClick={onExport}
        disabled={isExporting}
        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border
          bg-gray-800 border-gray-700 text-gray-400
          hover:text-blue-400 hover:border-blue-500/50 hover:bg-blue-500/10
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors"
        title="Export all jobs as JSON"
      >
        {isExporting
          ? <Loader2 size={13} className="animate-spin" />
          : <Download size={13} />
        }
        Export
      </button>

      {/* Import */}
      <button
        onClick={handleImportClick}
        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border
          bg-gray-800 border-gray-700 text-gray-400
          hover:text-gray-200 hover:border-gray-600
          transition-colors"
        title="Import jobs from a JSON backup file"
      >
        <Upload size={13} />
        Import
      </button>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        onChange={handleFileChange}
        className="hidden"
        aria-hidden="true"
      />
    </div>
  )
}
