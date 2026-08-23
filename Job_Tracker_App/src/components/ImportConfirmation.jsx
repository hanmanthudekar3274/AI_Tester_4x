import { AlertTriangle, FileJson } from 'lucide-react'
import Modal from './Modal'

export default function ImportConfirmation({ isOpen, onClose, fileName, jobCount, skipped, onConfirm, isImporting }) {
  const isEmpty = typeof jobCount === 'number' && jobCount === 0

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import Jobs?">
      <div className="px-6 py-5 space-y-4">
        {/* File info */}
        <div className="flex items-start gap-3 p-3.5 bg-gray-800 rounded-lg border border-gray-700">
          <FileJson size={18} className="text-blue-400 shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{fileName}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {typeof jobCount === 'number'
                ? `${jobCount} valid job${jobCount !== 1 ? 's' : ''} found`
                : 'Reading file…'
              }
              {skipped > 0 && (
                <span className="text-amber-400"> · {skipped} skipped</span>
              )}
            </p>
          </div>
        </div>

        {/* Warning */}
        <div className="flex items-start gap-2.5 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <AlertTriangle size={15} className="text-amber-400 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-300 leading-relaxed">
            Existing jobs will remain in place. Any imported job that shares an ID with an
            existing job will overwrite it.
          </p>
        </div>

        {isEmpty && (
          <p className="text-xs text-gray-500 text-center">
            No valid jobs were found in this file. Nothing will be imported.
          </p>
        )}
      </div>

      {/* Footer buttons */}
      <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800 bg-gray-900/50 rounded-b-xl">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={isImporting || isEmpty}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all
            ${isImporting || isEmpty
              ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
            }`}
        >
          {isImporting ? 'Importing…' : `Import ${jobCount ?? ''} Jobs`}
        </button>
      </div>
    </Modal>
  )
}
