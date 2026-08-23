import { nanoid } from 'nanoid'

export function generateId() {
  return nanoid()
}

export function formatDate(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short',
    day:   'numeric',
    year:  'numeric',
  })
}

export function daysAgo(timestamp) {
  if (!timestamp) return 0
  const ms = Date.now() - new Date(timestamp).getTime()
  return Math.floor(ms / (1000 * 60 * 60 * 24))
}

/**
 * @param {Partial<import('../types').Job>} data
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateJobData(data) {
  const errors = []
  if (!data.companyName?.trim()) errors.push('companyName is required')
  if (!data.jobTitle?.trim())    errors.push('jobTitle is required')
  return errors.length ? { valid: false, errors } : { valid: true, errors: [] }
}
