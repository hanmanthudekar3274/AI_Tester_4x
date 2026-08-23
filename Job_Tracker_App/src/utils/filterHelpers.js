/** @param {import('../types').Job} job @param {string} query */
export function matchesSearch(job, query) {
  if (!query) return true
  const q = query.toLowerCase()
  return (
    job.companyName.toLowerCase().includes(q) ||
    job.jobTitle.toLowerCase().includes(q)
  )
}

/** @param {import('../types').Job} job @param {string[]} statusArray */
export function matchesStatus(job, statusArray) {
  if (!statusArray || statusArray.length === 0) return true
  return statusArray.includes(job.status)
}

/** @param {import('../types').Job} job @param {string} resumeVersion */
export function matchesResume(job, resumeVersion) {
  if (!resumeVersion) return true
  return job.resumeTag === resumeVersion
}

/**
 * @param {import('../types').Job[]} jobs
 * @param {string} searchQuery
 * @param {{ status: string[], resume: string }} filters
 */
export function applyFilters(jobs, searchQuery, filters) {
  return jobs.filter(
    (job) =>
      matchesSearch(job, searchQuery) &&
      matchesStatus(job, filters.status) &&
      matchesResume(job, filters.resume),
  )
}
