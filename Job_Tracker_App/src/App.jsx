import { useEffect, useState, useCallback, useRef } from 'react'
import { Sun, Compass, Plus, CheckCircle, XCircle } from 'lucide-react'
import { initDB, addJob, getAllJobs, exportJobsAsJSON, importJobsFromJSON } from './db/database'
import { downloadJSON, readFileAsJSON } from './utils/fileHelpers'
import { useJobs } from './hooks/useJobs'
import KanbanBoard from './components/KanbanBoard'
import AddJobModal from './components/AddJobModal'
import ExportImportMenu from './components/ExportImportMenu'
import ImportConfirmation from './components/ImportConfirmation'
import AnalyticsModal from './components/AnalyticsModal'
import Footer from './components/Footer'
import { BRAND } from './config/brandColors'
import { TOASTS } from './config/messages'

const SEED_JOBS = [
  {
    companyName: 'Acme Corp',
    jobTitle:    'Senior Frontend Engineer',
    status:      'applied',
    location:    'Remote',
    salary:      '$130k–$160k',
    url:         'https://example.com/job/1',
    resumeTag:   'Resume_v2',
  },
  {
    companyName: 'Globex Inc',
    jobTitle:    'Full Stack Developer',
    status:      'interview',
    location:    'New York, NY',
    salary:      '$140k–$170k',
    resumeTag:   'Resume_v3',
    notes:       'Second round scheduled for next week',
  },
  {
    companyName: 'Initech Ltd',
    jobTitle:    'React Developer',
    status:      'wishlist',
    notes:       'Referral from Sarah — reach out before applying',
  },
  {
    companyName: 'Umbrella Corp',
    jobTitle:    'Backend Engineer',
    status:      'phone_screen',
    location:    'San Francisco, CA',
    salary:      '$150k–$180k',
    url:         'https://linkedin.com/jobs/view/123456',
  },
  {
    companyName: 'TechStart',
    jobTitle:    'React Native Developer',
    status:      'offer',
    location:    'Remote',
    salary:      '$125k + equity',
    resumeTag:   'Resume_v1',
  },
]

async function seedIfEmpty() {
  await initDB()
  const existing = await getAllJobs()
  if (existing.length === 0) {
    await Promise.all(SEED_JOBS.map((j) => addJob(j)))
    console.log(`✅ Database test passed: ${SEED_JOBS.length} jobs created`)
  }
}

// ─── Minimal toast hook ────────────────────────────────────────────────────
function useToast() {
  const [toast, setToast]   = useState(null)
  const timerRef            = useRef(null)

  const show = useCallback((message, type = 'success') => {
    clearTimeout(timerRef.current)
    setToast({ message, type, key: Date.now() })
    timerRef.current = setTimeout(() => setToast(null), 3500)
  }, [])

  return { toast, show }
}

// ─── App ──────────────────────────────────────────────────────────────────
export default function App() {
  const { jobs, loading, error, create, update, remove, refresh } = useJobs()
  const { toast, show: showToast } = useToast()

  // Add job modal
  const [modalOpen,          setModalOpen]          = useState(false)
  const [modalDefaultStatus, setModalDefaultStatus] = useState('wishlist')

  // Analytics modal (kept for backward compat, analytics also lives inline in KanbanBoard)
  const [showAnalytics, setShowAnalytics] = useState(false)
  const handleCloseAnalytics = useCallback(() => setShowAnalytics(false), [])

  // Import flow
  const [importData,        setImportData]        = useState(null)
  const [showImportConfirm, setShowImportConfirm] = useState(false)
  const [isImporting,       setIsImporting]       = useState(false)
  const [isExporting,       setIsExporting]       = useState(false)

  useEffect(() => {
    seedIfEmpty().then(refresh).catch(console.error)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Add job ──
  const handleAddJob = useCallback((status) => {
    setModalDefaultStatus(status || 'wishlist')
    setModalOpen(true)
  }, [])

  const handleCloseModal = useCallback(() => setModalOpen(false), [])

  const handleUpdateJob = useCallback(async (id, changes) => {
    try {
      await update(id, changes)
    } catch (err) {
      console.error('Failed to update job:', err)
    }
  }, [update])

  const handleDeleteJob = useCallback(async (id) => {
    try {
      await remove(id)
    } catch (err) {
      console.error('Failed to delete job:', err)
      showToast(TOASTS.deleteFailed(), 'error')
    }
  }, [remove, showToast])

  // ── Export ──
  const handleExport = useCallback(async () => {
    setIsExporting(true)
    try {
      const jsonStr  = await exportJobsAsJSON()
      const data     = JSON.parse(jsonStr)
      const date     = new Date().toISOString().split('T')[0]
      downloadJSON(data, `jobflow-backup-${date}.json`)
      showToast(TOASTS.exported(data.totalJobs))
    } catch (err) {
      console.error('Export failed:', err)
      showToast(TOASTS.exportFailed(err.message), 'error')
    } finally {
      setIsExporting(false)
    }
  }, [showToast])

  // ── Import — step 1: read file, show confirmation ──
  const handleImport = useCallback(async (file) => {
    try {
      const data = await readFileAsJSON(file)
      setImportData({ ...data, _fileName: file.name })
      setShowImportConfirm(true)
    } catch (err) {
      console.error('Import read failed:', err)
      showToast(TOASTS.importFailed(err.message), 'error')
    }
  }, [showToast])

  // ── Import — step 2: confirmed, write to DB ──
  const handleImportConfirm = useCallback(async () => {
    if (!importData) return
    setIsImporting(true)
    try {
      const { _fileName, ...exportPayload } = importData
      const result = await importJobsFromJSON(JSON.stringify(exportPayload))
      await refresh()
      setShowImportConfirm(false)
      setImportData(null)
      showToast(TOASTS.imported(result.jobsImported, result.skipped))
    } catch (err) {
      console.error('Import failed:', err)
      showToast(TOASTS.importFailed(err.message), 'error')
    } finally {
      setIsImporting(false)
    }
  }, [importData, refresh, showToast])

  const handleImportCancel = useCallback(() => {
    setShowImportConfirm(false)
    setImportData(null)
  }, [])

  return (
    <div className="h-screen bg-gray-950 text-gray-100 flex flex-col overflow-hidden">
      <header className="border-b border-gray-800 bg-gray-900 shrink-0">
        <div className="px-6 py-3.5 flex items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="relative">
              <div className="absolute inset-0 bg-primary-600/30 rounded-lg blur-sm" />
              <div className="relative p-1.5 bg-primary-600 rounded-lg">
                <Compass size={18} className="text-white" strokeWidth={2} />
              </div>
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">{BRAND.name}</h1>
              <p className="text-xs text-gray-500">{BRAND.tagline}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Export / Import */}
            <ExportImportMenu
              onExport={handleExport}
              onImport={handleImport}
              isExporting={isExporting}
            />

            <div className="w-px h-5 bg-gray-800" />

            {/* Add Job */}
            <button
              onClick={() => handleAddJob('wishlist')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-all
                shadow-lg shadow-primary-500/20
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              aria-label="Add a new job application"
            >
              <Plus size={15} />
              Add Job
            </button>

            <button
              className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              aria-label="Toggle light/dark mode"
            >
              <Sun size={16} />
            </button>
          </div>
        </div>
      </header>

      <KanbanBoard
        jobs={jobs}
        onUpdateJob={handleUpdateJob}
        onDeleteJob={handleDeleteJob}
        loading={loading}
        error={error}
        onAddJob={handleAddJob}
      />

      <Footer />

      {/* ── Modals ── */}
      <AddJobModal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        defaultStatus={modalDefaultStatus}
        onCreate={create}
        onJobAdded={handleCloseModal}
      />

      <AnalyticsModal
        isOpen={showAnalytics}
        onClose={handleCloseAnalytics}
        jobs={jobs}
      />

      <ImportConfirmation
        isOpen={showImportConfirm}
        onClose={handleImportCancel}
        fileName={importData?._fileName ?? ''}
        jobCount={Array.isArray(importData?.jobs) ? importData.jobs.length : undefined}
        skipped={0}
        onConfirm={handleImportConfirm}
        isImporting={isImporting}
      />

      {/* ── Toast ── */}
      {toast && (
        <div
          key={toast.key}
          className={`fixed bottom-6 right-6 z-[100] flex items-center gap-2.5
            px-4 py-3 rounded-xl text-sm font-medium shadow-2xl border
            animate-in fade-in slide-in-from-bottom-4 duration-200
            ${toast.type === 'error'
              ? 'bg-gray-900 border-red-500/30 text-red-300'
              : 'bg-gray-900 border-emerald-500/30 text-gray-100'
            }`}
        >
          {toast.type === 'error'
            ? <XCircle size={15} className="text-red-400 shrink-0" />
            : <CheckCircle size={15} className="text-emerald-400 shrink-0" />
          }
          {toast.message}
        </div>
      )}

      <footer className="border-t border-gray-800 py-3 text-center text-xs text-gray-700 shrink-0">
        Job Tracker AI — local-first, no data leaves your machine
      </footer>
    </div>
  )
}
