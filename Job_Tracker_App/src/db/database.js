import { openDB } from 'idb'
import { generateId } from '../utils/helpers'
import { createJob } from '../types/index'

const DB_NAME    = 'job-tracker'
const DB_VERSION = 1
const STORE      = 'jobs'

function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      const store = db.createObjectStore(STORE, { keyPath: 'id' })
      store.createIndex('status',    'status')
      store.createIndex('createdAt', 'createdAt')
    },
  })
}

export async function initDB() {
  const db = await getDB()
  db.close()
}

/** @param {Partial<import('../types').Job>} data */
export async function addJob(data) {
  const db  = await getDB()
  const now = new Date().toISOString()
  const job = createJob({ ...data, id: generateId(), createdAt: now, updatedAt: now })
  await db.add(STORE, job)
  db.close()
  return job
}

/** @returns {Promise<import('../types').Job[]>} */
export async function getAllJobs() {
  const db   = await getDB()
  const jobs = await db.getAll(STORE)
  db.close()
  return jobs
}

/** @param {string} id */
export async function getJob(id) {
  const db  = await getDB()
  const job = await db.get(STORE, id)
  db.close()
  return job ?? null
}

/**
 * @param {string} id
 * @param {Partial<import('../types').Job>} changes
 */
export async function updateJob(id, changes) {
  const db      = await getDB()
  const existing = await db.get(STORE, id)
  if (!existing) { db.close(); return null }
  const updated = { ...existing, ...changes, id, updatedAt: new Date().toISOString() }
  await db.put(STORE, updated)
  db.close()
  return updated
}

/** @param {string} id */
export async function deleteJob(id) {
  const db = await getDB()
  await db.delete(STORE, id)
  db.close()
}

/** @param {string} status */
export async function getJobsByStatus(status) {
  const db   = await getDB()
  const jobs = await db.getAllFromIndex(STORE, 'status', status)
  db.close()
  return jobs
}

export async function clearAllJobs() {
  const db = await getDB()
  await db.clear(STORE)
  db.close()
}

// ─── Export / Import ────────────────────────────────────────────────────────

const EXPORT_VERSION = '1.0'
const VALID_STATUSES  = new Set(['wishlist', 'applied', 'phone_screen', 'interview', 'offer', 'rejected'])

/** @returns {Promise<string>} JSON string ready to save to disk */
export async function exportJobsAsJSON() {
  const db   = await getDB()
  const jobs = await db.getAll(STORE)
  db.close()
  return JSON.stringify({
    version:    EXPORT_VERSION,
    exportedAt: new Date().toISOString(),
    totalJobs:  jobs.length,
    jobs,
  }, null, 2)
}

/**
 * Upserts jobs from a JSON export string into IndexedDB.
 * Duplicate IDs are updated; existing unrelated jobs are untouched.
 * @param {string} jsonString
 * @returns {Promise<{success: boolean, jobsImported: number, skipped: number}>}
 */
export async function importJobsFromJSON(jsonString) {
  let parsed
  try {
    parsed = JSON.parse(jsonString)
  } catch {
    throw new Error('Invalid JSON — could not parse the file')
  }

  if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.jobs)) {
    throw new Error('Invalid format — file must contain a "jobs" array')
  }

  const valid = []
  let skipped = 0

  for (const job of parsed.jobs) {
    if (!job.id || !job.companyName || !job.jobTitle || !job.status) {
      console.warn('[import] Skipping job missing required fields:', job)
      skipped++
      continue
    }
    if (!VALID_STATUSES.has(job.status)) {
      console.warn(`[import] Skipping job with unknown status "${job.status}":`, job.companyName)
      skipped++
      continue
    }
    // Warn about missing optional fields but allow import
    if (!job.createdAt) console.warn('[import] job.createdAt missing for', job.companyName)
    if (!job.updatedAt) console.warn('[import] job.updatedAt missing for', job.companyName)
    valid.push({ ...job, updatedAt: job.updatedAt ?? new Date().toISOString() })
  }

  if (valid.length === 0 && parsed.jobs.length > 0) {
    throw new Error('No valid jobs found — all entries failed validation')
  }

  // Batch upsert in a single transaction
  const db = await getDB()
  const tx = db.transaction(STORE, 'readwrite')
  await Promise.all([...valid.map((job) => tx.store.put(job)), tx.done])
  db.close()

  return { success: true, jobsImported: valid.length, skipped }
}

const DEFAULT_RESUMES = ['Resume_v1', 'Resume_v2', 'Resume_v3']

/** @returns {Promise<string[]>} Sorted unique resume names from DB, merged with defaults */
export async function getAllResumeNames() {
  const db   = await getDB()
  const jobs = await db.getAll(STORE)
  db.close()
  const fromDB = jobs.map((j) => j.resumeTag).filter(Boolean)
  const merged = Array.from(new Set([...DEFAULT_RESUMES, ...fromDB]))
  return merged.sort()
}
