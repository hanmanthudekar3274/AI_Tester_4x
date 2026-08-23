import { JOB_STATUSES } from '../types/index'

// Stages that count as "having applied" (excludes wishlist)
const ACTIVE_STAGES    = ['applied', 'phone_screen', 'interview', 'offer', 'rejected']
// Stages that count as "reached interview or beyond"
const INTERVIEW_STAGES = ['interview', 'offer']
// Funnel stages in order (cumulative from each stage onwards)
const FUNNEL_STAGES    = ['applied', 'phone_screen', 'interview', 'offer']

const FUNNEL_INCLUDES = {
  applied:      ['applied', 'phone_screen', 'interview', 'offer', 'rejected'],
  phone_screen: ['phone_screen', 'interview', 'offer'],
  interview:    ['interview', 'offer'],
  offer:        ['offer'],
}

/** @param {number} value @param {number} [decimals] */
export function formatPercentage(value, decimals = 1) {
  if (!isFinite(value)) return '0%'
  return `${value.toFixed(decimals)}%`
}

/** @param {number} days */
export function formatDays(days) {
  if (days === 1) return '1 day'
  return `${days} days`
}

/**
 * Returns the effective date to use for a job (appliedDate ?? createdAt).
 * @param {import('../types').Job} job
 */
function jobDate(job) {
  return job.appliedDate || job.createdAt
}

/**
 * Main stats calculation.
 * @param {import('../types').Job[]} jobs
 */
export function calculateStats(jobs) {
  const total       = jobs.length
  const activeJobs  = jobs.filter((j) => ACTIVE_STAGES.includes(j.status))
  const activeCount = activeJobs.length

  // ── By status ───────────────────────────────────────────────────────────
  const byStatus = {}
  for (const s of JOB_STATUSES) byStatus[s] = 0
  for (const j of jobs) byStatus[j.status] = (byStatus[j.status] ?? 0) + 1

  // ── Interview rate & offer rate ─────────────────────────────────────────
  const interviewCount = jobs.filter((j) => INTERVIEW_STAGES.includes(j.status)).length
  const offerCount     = byStatus['offer'] ?? 0
  const interviewRate  = activeCount > 0 ? (interviewCount / activeCount) * 100 : 0
  const offerRate      = activeCount > 0 ? (offerCount / activeCount) * 100 : 0

  // ── Days to interview (for jobs that reached interview+) ─────────────────
  const now            = Date.now()
  const msPerDay       = 1000 * 60 * 60 * 24
  const daysList       = jobs
    .filter((j) => INTERVIEW_STAGES.includes(j.status))
    .map((j) => Math.max(0, Math.floor((now - new Date(jobDate(j)).getTime()) / msPerDay)))
    .sort((a, b) => a - b)

  const avgDaysToInterview    = daysList.length
    ? Math.round(daysList.reduce((s, d) => s + d, 0) / daysList.length)
    : 0
  const medianDaysToInterview = daysList.length
    ? daysList[Math.floor(daysList.length / 2)]
    : 0

  // ── Resume performance ───────────────────────────────────────────────────
  const resumeMap = {}
  for (const j of jobs) {
    const key = j.resumeTag?.trim() || null
    if (!key) continue
    if (!resumeMap[key]) resumeMap[key] = { resume: key, apps: 0, interviews: 0 }
    resumeMap[key].apps++
    if (INTERVIEW_STAGES.includes(j.status)) resumeMap[key].interviews++
  }
  const resumePerformance = Object.values(resumeMap)
    .map((r) => ({ ...r, rate: r.apps > 0 ? (r.interviews / r.apps) * 100 : 0 }))
    .sort((a, b) => b.rate - a.rate)

  // ── Apps this month ──────────────────────────────────────────────────────
  const todayObj   = new Date()
  const monthStart = new Date(todayObj.getFullYear(), todayObj.getMonth(), 1).getTime()
  const appsThisMonth = jobs.filter((j) => new Date(jobDate(j)).getTime() >= monthStart).length

  // ── Funnel ───────────────────────────────────────────────────────────────
  const funnel = FUNNEL_STAGES.map((stage) => ({
    stage,
    count: jobs.filter((j) => FUNNEL_INCLUDES[stage].includes(j.status)).length,
  }))

  // ── 30-day timeline ──────────────────────────────────────────────────────
  const timeline = getApplicationsTimeline(jobs, 30)

  return {
    total,
    activeCount,
    byStatus,
    interviewRate,
    offerRate,
    avgDaysToInterview,
    medianDaysToInterview,
    resumePerformance,
    appsThisMonth,
    funnel,
    timeline,
  }
}

/**
 * Returns an array of daily buckets for the last `days` days.
 * Each entry: { date, label, count (new that day), cumulative }
 * @param {import('../types').Job[]} jobs
 * @param {number} [days]
 */
export function getApplicationsTimeline(jobs, days = 30) {
  const today  = new Date()
  today.setHours(0, 0, 0, 0)

  const cutoff = new Date(today)
  cutoff.setDate(today.getDate() - days + 1)

  // Jobs before the window — needed for correct cumulative start
  const before = jobs.filter((j) => new Date(jobDate(j)) < cutoff).length

  // Count new jobs per day inside the window
  const bucket = {}
  for (const j of jobs) {
    const d = new Date(jobDate(j))
    d.setHours(0, 0, 0, 0)
    if (d >= cutoff) {
      const key      = d.toISOString().split('T')[0]
      bucket[key]    = (bucket[key] ?? 0) + 1
    }
  }

  // Build the result array
  const result = []
  let cumulative = before
  for (let i = 0; i < days; i++) {
    const d = new Date(cutoff)
    d.setDate(cutoff.getDate() + i)
    const key   = d.toISOString().split('T')[0]
    const count = bucket[key] ?? 0
    cumulative  += count
    result.push({
      date:       key,
      label:      d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      count,
      cumulative,
    })
  }

  return result
}
