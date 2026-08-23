/**
 * @param {{ companyName?: string, jobTitle?: string, url?: string, notes?: string }} data
 * @returns {{ isValid: boolean, errors: Record<string, string> }}
 */
export function validateJobForm(data) {
  const errors = {}

  if (!data.companyName?.trim()) {
    errors.companyName = 'Company name is required'
  }

  if (!data.jobTitle?.trim()) {
    errors.jobTitle = 'Job title is required'
  }

  if (data.url?.trim()) {
    try {
      new URL(data.url.trim())
    } catch {
      errors.url = 'Please enter a valid URL (e.g. https://linkedin.com/jobs/…)'
    }
  }

  if (data.notes && data.notes.length > 500) {
    errors.notes = `Notes must be 500 characters or less (currently ${data.notes.length})`
  }

  const isValid = Object.keys(errors).length === 0
  return { isValid, errors }
}
