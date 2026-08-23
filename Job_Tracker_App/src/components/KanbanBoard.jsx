import { useState, useCallback, useMemo, useEffect } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from '@dnd-kit/core'
import { COLUMN_ORDER } from '../utils/statusConfig'
import { applyFilters } from '../utils/filterHelpers'
import { getAllResumeNames } from '../db/database'
import KanbanColumn from './KanbanColumn'
import JobCard from './JobCard'
import SearchBar from './SearchBar'
import FilterBar from './FilterBar'
import JobDetailPanel from './JobDetailPanel'
import OfferComparison from './OfferComparison'
import InterviewTimeline from './InterviewTimeline'
import Analytics from './Analytics'
import { Loader2, BarChart3, LayoutDashboard, List, Award } from 'lucide-react'
import EmptyStateHero from './EmptyStateHero'

const EMPTY_FILTERS = { status: [], resume: '' }

const VIEW_TABS = [
  { key: 'kanban',    label: 'Kanban',    icon: LayoutDashboard },
  { key: 'timeline',  label: 'Timeline',  icon: List },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function KanbanBoard({ jobs, loading, error, onAddJob, onUpdateJob, onDeleteJob }) {
  const [activeJob,        setActiveJob]        = useState(null)
  const [searchQuery,      setSearchQuery]      = useState('')
  const [filters,          setFilters]          = useState(EMPTY_FILTERS)
  const [availableResumes, setAvailableResumes] = useState(['Resume_v1', 'Resume_v2', 'Resume_v3'])
  const [selectedJob,      setSelectedJob]      = useState(null)
  const [panelOpen,        setPanelOpen]        = useState(false)
  const [viewMode,         setViewMode]         = useState('kanban')
  const [showOfferCompare, setShowOfferCompare] = useState(false)

  useEffect(() => {
    getAllResumeNames().then(setAvailableResumes).catch(() => {})
  }, [])

  const hasActiveFilters = searchQuery.length > 0 || filters.status.length > 0 || filters.resume !== ''

  const clearAll = useCallback(() => {
    setSearchQuery('')
    setFilters(EMPTY_FILTERS)
  }, [])

  const filteredJobs = useMemo(
    () => applyFilters(jobs, searchQuery, filters),
    [jobs, searchQuery, filters],
  )

  const jobsByStatus = useCallback(
    (status) => filteredJobs.filter((j) => j.status === status),
    [filteredJobs],
  )

  const offerJobs = useMemo(() => jobs.filter((j) => j.status === 'offer'), [jobs])

  // Keep selectedJob in sync with the live jobs array (e.g. after auto-save)
  useEffect(() => {
    if (!selectedJob) return
    const updated = jobs.find((j) => j.id === selectedJob.id)
    if (updated && updated !== selectedJob) setSelectedJob(updated)
  }, [jobs]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectJob = useCallback((job) => {
    setSelectedJob(job)
    setPanelOpen(true)
  }, [])

  const handleClosePanel = useCallback(() => setPanelOpen(false), [])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  )

  const handleDragStart = useCallback(
    ({ active }) => setActiveJob(jobs.find((j) => j.id === active.id) ?? null),
    [jobs],
  )

  const handleDragEnd = useCallback(
    ({ active, over }) => {
      setActiveJob(null)
      if (!over) return
      const newStatus = over.id
      const job = jobs.find((j) => j.id === active.id)
      if (!job || job.status === newStatus) return
      onUpdateJob(active.id, { status: newStatus })
    },
    [jobs, onUpdateJob],
  )

  const handleDragCancel = useCallback(() => setActiveJob(null), [])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-600">
        <Loader2 size={20} className="animate-spin mr-2" />
        <span className="text-sm">Loading jobs…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
        Failed to load jobs: {error}
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* ── Toolbar ── */}
      <div className="shrink-0 bg-gray-950 border-b border-gray-800 px-6 py-3 flex flex-col gap-2.5">
        <div className="flex items-center gap-3">
          <SearchBar value={searchQuery} onChange={setSearchQuery} />
          {hasActiveFilters && (
            <span className="text-xs text-gray-600 whitespace-nowrap tabular-nums">
              {filteredJobs.length} of {jobs.length} jobs
            </span>
          )}

          {/* View toggle */}
          <div className="flex items-center rounded-lg border border-gray-700 bg-gray-800 p-0.5 shrink-0">
            {VIEW_TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setViewMode(key)}
                className={[
                  'flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md transition-all',
                  viewMode === key
                    ? 'bg-gray-700 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300',
                ].join(' ')}
                title={label}
              >
                <Icon size={12} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>

          {/* Compare Offers button — appears when 2+ offers exist */}
          {offerJobs.length >= 2 && (
            <button
              onClick={() => setShowOfferCompare(true)}
              className="flex items-center gap-1.5 px-2.5 py-2 text-xs font-medium rounded-lg border shrink-0
                bg-emerald-500/10 border-emerald-500/30 text-emerald-400
                hover:bg-emerald-500/20 hover:border-emerald-500/50 transition-colors"
              title="Compare offers side by side"
            >
              <Award size={13} />
              <span className="hidden sm:inline">Compare Offers</span>
            </button>
          )}
        </div>

        <FilterBar
          filters={filters}
          onFilterChange={setFilters}
          availableResumes={availableResumes}
          hasActiveFilters={hasActiveFilters}
          onClearAll={clearAll}
        />
      </div>

      {/* ── Empty state (first visit) ── */}
      {viewMode === 'kanban' && jobs.length === 0 && !loading && (
        <EmptyStateHero onAddJob={onAddJob} />
      )}

      {/* ── Kanban view ── */}
      {viewMode === 'kanban' && jobs.length > 0 && (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <div className="flex-1 min-h-0 overflow-x-auto px-6 py-5">
            <div className="flex gap-4 h-full min-w-max">
              {COLUMN_ORDER.map((status) => (
                <KanbanColumn
                  key={status}
                  status={status}
                  jobs={jobsByStatus(status)}
                  onAddJob={onAddJob}
                  onSelectJob={handleSelectJob}
                />
              ))}
            </div>
          </div>

          <DragOverlay dropAnimation={{ duration: 150, easing: 'cubic-bezier(0.18,0.67,0.6,1.22)' }}>
            {activeJob && <JobCard job={activeJob} overlay />}
          </DragOverlay>
        </DndContext>
      )}

      {/* ── Timeline view ── */}
      {viewMode === 'timeline' && (
        <InterviewTimeline jobs={filteredJobs} onSelectJob={handleSelectJob} />
      )}

      {/* ── Analytics view ── */}
      {viewMode === 'analytics' && (
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-600">
              <BarChart3 size={32} className="opacity-30" />
              <p className="text-sm">Add some jobs to see analytics</p>
            </div>
          ) : (
            <Analytics jobs={jobs} />
          )}
        </div>
      )}

      {/* ── Detail panel (slide-in from right) ── */}
      <JobDetailPanel
        isOpen={panelOpen}
        job={selectedJob}
        onClose={handleClosePanel}
        onUpdate={onUpdateJob}
        onDelete={onDeleteJob}
        availableResumes={availableResumes}
      />

      {/* ── Offer comparison modal ── */}
      <OfferComparison
        isOpen={showOfferCompare}
        onClose={() => setShowOfferCompare(false)}
        offerJobs={offerJobs}
      />
    </div>
  )
}
