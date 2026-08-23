import { useState, useEffect } from 'react'
import { Link2, Loader2 } from 'lucide-react'
import Modal from './Modal'
import FormField from './FormField'
import { JOB_STATUSES } from '../types/index'
import { STATUS_CONFIG } from '../utils/statusConfig'
import { validateJobForm } from '../utils/validation'
import { getAllResumeNames } from '../db/database'

const INITIAL_FORM = {
  companyName: '',
  jobTitle:    '',
  url:         '',
  resumeTag:   '',
  status:      'wishlist',
  salary:      '',
  notes:       '',
}

const inputClass = `
  w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100
  placeholder:text-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40
  transition-colors
`
const selectClass = `
  w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100
  focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/40
  transition-colors appearance-none cursor-pointer
`

export default function AddJobModal({ isOpen, onClose, defaultStatus = 'wishlist', onCreate, onJobAdded }) {
  const [form,        setForm]        = useState({ ...INITIAL_FORM, status: defaultStatus })
  const [errors,      setErrors]      = useState({})
  const [submitting,  setSubmitting]  = useState(false)
  const [resumeNames, setResumeNames] = useState(['Resume_v1', 'Resume_v2', 'Resume_v3'])

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setForm({ ...INITIAL_FORM, status: defaultStatus })
      setErrors({})
      setSubmitting(false)
    }
  }, [isOpen, defaultStatus])

  // Load resume names on first open
  useEffect(() => {
    if (isOpen) {
      getAllResumeNames().then(setResumeNames).catch(() => {})
    }
  }, [isOpen])

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
    // Clear field error on change
    if (errors[key]) setErrors((prev) => { const e = { ...prev }; delete e[key]; return e })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const { isValid, errors: validationErrors } = validateJobForm(form)
    if (!isValid) { setErrors(validationErrors); return }

    setSubmitting(true)
    try {
      await onCreate({
        companyName: form.companyName.trim(),
        jobTitle:    form.jobTitle.trim(),
        url:         form.url.trim(),
        resumeTag:   form.resumeTag,
        status:      form.status,
        salary:      form.salary.trim(),
        notes:       form.notes.trim(),
      })
      onJobAdded?.()
      onClose()
    } catch (err) {
      setErrors({ _submit: err.message })
      setSubmitting(false)
    }
  }

  const canSubmit = form.companyName.trim() && form.jobTitle.trim() && !submitting

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Job">
      <form onSubmit={handleSubmit} noValidate>
        <div className="px-6 py-5 space-y-5">

          {/* Company Name */}
          <FormField label="Company Name" required error={errors.companyName}>
            <input
              type="text"
              className={inputClass}
              placeholder="e.g., Google, Microsoft"
              value={form.companyName}
              onChange={(e) => setField('companyName', e.target.value)}
              autoFocus
            />
          </FormField>

          {/* Job Title */}
          <FormField label="Job Title" required error={errors.jobTitle}>
            <input
              type="text"
              className={inputClass}
              placeholder="e.g., Senior QA Engineer"
              value={form.jobTitle}
              onChange={(e) => setField('jobTitle', e.target.value)}
            />
          </FormField>

          {/* LinkedIn / Job URL */}
          <FormField label="Job URL" error={errors.url}>
            <div className="relative">
              <Link2 size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none" />
              <input
                type="url"
                className={`${inputClass} pl-8`}
                placeholder="https://linkedin.com/jobs/..."
                value={form.url}
                onChange={(e) => setField('url', e.target.value)}
              />
            </div>
          </FormField>

          {/* Two-column row: Resume + Salary */}
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Resume Used">
              <select
                className={selectClass}
                value={form.resumeTag}
                onChange={(e) => setField('resumeTag', e.target.value)}
              >
                <option value="">Select a resume…</option>
                {resumeNames.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </FormField>

            <FormField label="Salary Range">
              <input
                type="text"
                className={inputClass}
                placeholder="e.g., $120–150K"
                value={form.salary}
                onChange={(e) => setField('salary', e.target.value)}
              />
            </FormField>
          </div>

          {/* Job Status — pill selector */}
          <FormField label="Status" required>
            <div className="flex flex-wrap gap-2 pt-0.5">
              {JOB_STATUSES.map((s) => {
                const cfg     = STATUS_CONFIG[s]
                const selected = form.status === s
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setField('status', s)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all
                      ${selected
                        ? `${cfg.badge} border-transparent ring-1 ring-offset-1 ring-offset-gray-900 ring-current`
                        : 'bg-gray-800 text-gray-500 border-gray-700 hover:border-gray-600 hover:text-gray-400'
                      }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    {cfg.label}
                  </button>
                )
              })}
            </div>
          </FormField>

          {/* Notes */}
          <FormField label="Notes" error={errors.notes}>
            <div className="relative">
              <textarea
                className={`${inputClass} resize-none`}
                placeholder="Recruiter name, referral info, next steps…"
                rows={4}
                maxLength={520}
                value={form.notes}
                onChange={(e) => setField('notes', e.target.value)}
              />
              <span className={`absolute bottom-2 right-3 text-xs tabular-nums pointer-events-none
                ${form.notes.length > 480 ? 'text-amber-500' : 'text-gray-600'}
                ${form.notes.length > 500 ? 'text-red-400' : ''}`}
              >
                {form.notes.length}/500
              </span>
            </div>
          </FormField>

          {/* Submit error */}
          {errors._submit && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {errors._submit}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800 bg-gray-900/50 rounded-b-xl">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!canSubmit}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all
              ${canSubmit
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                : 'bg-gray-800 text-gray-600 cursor-not-allowed'
              }`}
          >
            {submitting && <Loader2 size={13} className="animate-spin" />}
            {submitting ? 'Saving…' : 'Add Job'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
