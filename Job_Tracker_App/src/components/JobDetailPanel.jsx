import { useState, useEffect, useRef, useCallback } from 'react'
import {
  X, Briefcase, FileText, MessageSquare, Gift,
  AlertCircle, CheckCircle, Loader2, ExternalLink,
} from 'lucide-react'
import { COLUMN_ORDER, STATUS_CONFIG } from '../utils/statusConfig'
import QuickActionButtons from './QuickActionButtons'
import InterviewPrepChecklist from './InterviewPrepChecklist'

const DEBOUNCE_MS = 500
const CURRENCIES  = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'INR', 'JPY', 'SGD']

const inputCls    = 'w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors'
const textareaCls = `${inputCls} resize-none leading-relaxed`
const selectCls   = `${inputCls} cursor-pointer`

function SectionTitle({ icon: Icon, title, color = 'text-gray-500', bg = '', border = 'border-gray-800' }) {
  return (
    <div className={[
      'flex items-center gap-2.5 -mx-6 px-6 py-2.5 mb-4',
      'border-b',
      border,
      bg,
    ].join(' ')}>
      <Icon size={13} className={color} />
      <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{title}</span>
    </div>
  )
}

function Field({ label, children, className = '' }) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      <label className="block text-xs font-medium text-gray-500">{label}</label>
      {children}
    </div>
  )
}

function normalizeJob(job) {
  return {
    ...job,
    interviewFeedback: {
      skills: '', weaknesses: '', rejectionReason: '', interviewNotes: '', followUpDate: '',
      ...(job.interviewFeedback || {}),
    },
    offerDetails: {
      baseSalary: '', currency: 'USD', bonus: '', stockOptions: '',
      startDate: '', benefits: '', deadline: '', notes: '',
      ...(job.offerDetails || {}),
    },
  }
}

export default function JobDetailPanel({ isOpen, job, onClose, onUpdate, onDelete, availableResumes = [] }) {
  const [draft,      setDraft]      = useState(null)
  const [saveState,  setSaveState]  = useState('idle') // 'idle' | 'saving' | 'saved'
  const debounceRef  = useRef(null)
  const saveTimerRef = useRef(null)
  // Keep a ref to the last seen job so slide-out animation still shows content
  const lastJobRef   = useRef(null)
  if (job) lastJobRef.current = job
  const displayJob = lastJobRef.current

  // Sync draft when panel opens with a new job
  useEffect(() => {
    if (isOpen && job) {
      setDraft(normalizeJob(job))
      setSaveState('idle')
    }
  }, [isOpen, job?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Escape key
  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  // Body scroll lock on mobile
  useEffect(() => {
    if (isOpen && window.innerWidth < 768) document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  // Cleanup timers
  useEffect(() => () => {
    clearTimeout(debounceRef.current)
    clearTimeout(saveTimerRef.current)
  }, [])

  const flushSave = useCallback((newDraft) => {
    setSaveState('saving')
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        await onUpdate(newDraft.id, newDraft)
        setSaveState('saved')
        clearTimeout(saveTimerRef.current)
        saveTimerRef.current = setTimeout(() => setSaveState('idle'), 2000)
      } catch (err) {
        console.error('Auto-save failed:', err)
        setSaveState('idle')
      }
    }, DEBOUNCE_MS)
  }, [onUpdate])

  const updateField = useCallback((field, value) => {
    setDraft((prev) => {
      const next = { ...prev, [field]: value }
      flushSave(next)
      return next
    })
  }, [flushSave])

  const updateNested = useCallback((section, field, value) => {
    setDraft((prev) => {
      const next = { ...prev, [section]: { ...(prev[section] || {}), [field]: value } }
      flushSave(next)
      return next
    })
  }, [flushSave])

  const handleQuickUpdate = useCallback((changes) => {
    setDraft((prev) => {
      const next = { ...prev, ...changes }
      flushSave(next)
      return next
    })
  }, [flushSave])

  const currentStatus = draft?.status ?? displayJob?.status ?? 'wishlist'
  const isInterview   = ['interview', 'offer'].includes(currentStatus)
  const isPhoneScreen = currentStatus === 'phone_screen'
  const isRejected    = currentStatus === 'rejected'
  const isOffer       = currentStatus === 'offer'
  const showFeedback  = isInterview || isRejected || isPhoneScreen
  const showPrep      = isInterview || isPhoneScreen

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={[
          'fixed inset-0 z-40 bg-black/60 transition-opacity duration-300 md:hidden',
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        ].join(' ')}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        aria-label={displayJob ? `Job details: ${displayJob.companyName}` : 'Job details'}
        className={[
          'fixed right-0 top-0 bottom-0 z-50',
          'w-full md:w-[65%] lg:w-[55%] max-w-2xl',
          'bg-gray-900 border-l border-gray-800',
          'flex flex-col shadow-2xl shadow-black/80',
          'transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
      >
        {displayJob && (
          <>
            {/* ── Header ── */}
            <div className="shrink-0 flex items-start justify-between gap-3 px-6 py-4 border-b border-gray-800">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-base font-bold text-white truncate">
                    {draft?.companyName || displayJob.companyName}
                  </p>
                  {(draft?.url || displayJob.url) && (
                    <a
                      href={draft?.url || displayJob.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 text-gray-600 hover:text-indigo-400 transition-colors"
                      title="Open job posting"
                    >
                      <ExternalLink size={13} />
                    </a>
                  )}
                </div>
                <p className="text-sm text-gray-400 truncate mt-0.5">
                  {draft?.jobTitle || displayJob.jobTitle}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {saveState === 'saving' && (
                  <span className="flex items-center gap-1 text-xs text-gray-600">
                    <Loader2 size={11} className="animate-spin" />
                    Saving
                  </span>
                )}
                {saveState === 'saved' && (
                  <span className="flex items-center gap-1 text-xs text-emerald-600">
                    <CheckCircle size={11} />
                    Saved
                  </span>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors
                    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1 focus-visible:ring-offset-gray-900"
                  aria-label="Close panel"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* ── Scrollable body ── */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-7">
              {draft ? (
                <>
                  {/* Status */}
                  <div>
                    <SectionTitle icon={Briefcase} title="Status" color="text-primary-400" bg="bg-primary-500/5" border="border-primary-500/20" />
                    <div className="flex flex-wrap gap-2">
                      {COLUMN_ORDER.map((s) => {
                        const cfg    = STATUS_CONFIG[s]
                        const active = draft.status === s
                        return (
                          <button
                            key={s}
                            onClick={() => updateField('status', s)}
                            className={[
                              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                              active
                                ? `${cfg.badge} border-current`
                                : 'bg-gray-800 border-gray-700 text-gray-500 hover:border-gray-600 hover:text-gray-300',
                            ].join(' ')}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                            {cfg.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  {/* Basic Info */}
                  <div>
                    <SectionTitle icon={FileText} title="Basic Info" color="text-gray-400" />
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Field label="Company Name">
                        <input className={inputCls} value={draft.companyName}
                          onChange={(e) => updateField('companyName', e.target.value)}
                          placeholder="Company name" />
                      </Field>
                      <Field label="Job Title">
                        <input className={inputCls} value={draft.jobTitle}
                          onChange={(e) => updateField('jobTitle', e.target.value)}
                          placeholder="Job title" />
                      </Field>
                      <Field label="Location">
                        <input className={inputCls} value={draft.location || ''}
                          onChange={(e) => updateField('location', e.target.value)}
                          placeholder="e.g. Remote, New York, NY" />
                      </Field>
                      <Field label="Salary Range">
                        <input className={inputCls} value={draft.salary || ''}
                          onChange={(e) => updateField('salary', e.target.value)}
                          placeholder="e.g. $120k–$150k" />
                      </Field>
                      <Field label="Applied Date">
                        <input type="date" className={inputCls} value={draft.appliedDate || ''}
                          onChange={(e) => updateField('appliedDate', e.target.value)} />
                      </Field>
                      <Field label="Resume Used">
                        <select className={selectCls} value={draft.resumeTag || ''}
                          onChange={(e) => updateField('resumeTag', e.target.value)}>
                          <option value="">No resume selected</option>
                          {availableResumes.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </Field>
                      <Field label="Job URL" className="sm:col-span-2">
                        <input className={inputCls} value={draft.url || ''}
                          onChange={(e) => updateField('url', e.target.value)}
                          placeholder="https://..." />
                      </Field>
                      <Field label="Notes" className="sm:col-span-2">
                        <textarea className={textareaCls} rows={3} value={draft.notes || ''}
                          onChange={(e) => updateField('notes', e.target.value)}
                          placeholder="Any notes about this application..." />
                      </Field>
                    </div>
                  </div>

                  {/* Interview Feedback */}
                  {showFeedback && (
                    <div>
                      <SectionTitle icon={MessageSquare} title="Interview Feedback" color="text-orange-400" bg="bg-orange-500/5" border="border-orange-500/20" />
                      <div className="space-y-4">
                        <Field label="Strengths Noted">
                          <textarea className={textareaCls} rows={2}
                            value={draft.interviewFeedback?.skills || ''}
                            onChange={(e) => updateNested('interviewFeedback', 'skills', e.target.value)}
                            placeholder="What went well, strengths mentioned by interviewers..." />
                        </Field>
                        <Field label="Areas to Improve">
                          <textarea className={textareaCls} rows={2}
                            value={draft.interviewFeedback?.weaknesses || ''}
                            onChange={(e) => updateNested('interviewFeedback', 'weaknesses', e.target.value)}
                            placeholder="Areas where you could improve..." />
                        </Field>
                        <Field label="Interview Notes">
                          <textarea className={textareaCls} rows={3}
                            value={draft.interviewFeedback?.interviewNotes || ''}
                            onChange={(e) => updateNested('interviewFeedback', 'interviewNotes', e.target.value)}
                            placeholder="Notes from your interviews..." />
                        </Field>
                        <Field label="Follow-up Date">
                          <input type="date" className={inputCls}
                            value={draft.interviewFeedback?.followUpDate || ''}
                            onChange={(e) => updateNested('interviewFeedback', 'followUpDate', e.target.value)} />
                        </Field>
                      </div>
                    </div>
                  )}

                  {/* Rejection Details */}
                  {isRejected && (
                    <div>
                      <SectionTitle icon={AlertCircle} title="Rejection Details" color="text-red-400" bg="bg-red-500/5" border="border-red-500/20" />
                      <Field label="Rejection Reason">
                        <textarea className={textareaCls} rows={3}
                          value={draft.interviewFeedback?.rejectionReason || ''}
                          onChange={(e) => updateNested('interviewFeedback', 'rejectionReason', e.target.value)}
                          placeholder="Why was the application rejected? What feedback was given?" />
                      </Field>
                    </div>
                  )}

                  {/* Offer Details */}
                  {isOffer && (
                    <div>
                      <SectionTitle icon={Gift} title="Offer Details" color="text-emerald-400" bg="bg-emerald-500/5" border="border-emerald-500/20" />
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Field label="Base Salary">
                          <input className={inputCls} value={draft.offerDetails?.baseSalary || ''}
                            onChange={(e) => updateNested('offerDetails', 'baseSalary', e.target.value)}
                            placeholder="e.g. 130000" />
                        </Field>
                        <Field label="Currency">
                          <select className={selectCls} value={draft.offerDetails?.currency || 'USD'}
                            onChange={(e) => updateNested('offerDetails', 'currency', e.target.value)}>
                            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
                          </select>
                        </Field>
                        <Field label="Bonus">
                          <input className={inputCls} value={draft.offerDetails?.bonus || ''}
                            onChange={(e) => updateNested('offerDetails', 'bonus', e.target.value)}
                            placeholder="e.g. 15% or $20,000" />
                        </Field>
                        <Field label="Stock / Equity">
                          <input className={inputCls} value={draft.offerDetails?.stockOptions || ''}
                            onChange={(e) => updateNested('offerDetails', 'stockOptions', e.target.value)}
                            placeholder="e.g. $50k RSUs over 4 years" />
                        </Field>
                        <Field label="Start Date">
                          <input type="date" className={inputCls}
                            value={draft.offerDetails?.startDate || ''}
                            onChange={(e) => updateNested('offerDetails', 'startDate', e.target.value)} />
                        </Field>
                        <Field label="Offer Deadline">
                          <input type="date" className={inputCls}
                            value={draft.offerDetails?.deadline || ''}
                            onChange={(e) => updateNested('offerDetails', 'deadline', e.target.value)} />
                        </Field>
                        <Field label="Benefits" className="sm:col-span-2">
                          <textarea className={textareaCls} rows={2}
                            value={draft.offerDetails?.benefits || ''}
                            onChange={(e) => updateNested('offerDetails', 'benefits', e.target.value)}
                            placeholder="Health, dental, 401k, PTO, remote work..." />
                        </Field>
                        <Field label="Offer Notes" className="sm:col-span-2">
                          <textarea className={textareaCls} rows={2}
                            value={draft.offerDetails?.notes || ''}
                            onChange={(e) => updateNested('offerDetails', 'notes', e.target.value)}
                            placeholder="Additional notes about this offer..." />
                        </Field>
                      </div>
                    </div>
                  )}

                  {/* Interview Prep Checklist */}
                  {showPrep && (
                    <div className="pt-2 border-t border-gray-800">
                      <div className="pt-4">
                        <InterviewPrepChecklist jobId={displayJob.id} />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center py-20 text-gray-600 text-sm">
                  Loading…
                </div>
              )}
            </div>

            {/* ── Footer: Quick Actions ── */}
            <div className="shrink-0 border-t border-gray-800 px-6 py-4">
              <QuickActionButtons
                job={draft || displayJob}
                onUpdate={handleQuickUpdate}
                onDelete={() => {
                  onDelete(displayJob.id)
                  onClose()
                }}
              />
            </div>
          </>
        )}
      </aside>
    </>
  )
}
