import { useState, useEffect, useCallback } from 'react'
import {
  getAllJobs,
  addJob,
  updateJob,
  deleteJob,
  getJobsByStatus,
} from '../db/database'
import { validateJobData } from '../utils/helpers'

export function useJobs() {
  const [jobs,    setJobs]    = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      setJobs(await getAllJobs())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const create = useCallback(async (data) => {
    const { valid, errors } = validateJobData(data)
    if (!valid) throw new Error(errors.join(', '))
    const job = await addJob(data)
    setJobs((prev) => [...prev, job])
    return job
  }, [])

  const update = useCallback(async (id, changes) => {
    if (changes.companyName !== undefined || changes.jobTitle !== undefined) {
      const current = jobs.find((j) => j.id === id) ?? {}
      const merged  = { ...current, ...changes }
      const { valid, errors } = validateJobData(merged)
      if (!valid) throw new Error(errors.join(', '))
    }
    const updated = await updateJob(id, changes)
    setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)))
    return updated
  }, [jobs])

  const remove = useCallback(async (id) => {
    await deleteJob(id)
    setJobs((prev) => prev.filter((j) => j.id !== id))
  }, [])

  const byStatus = useCallback(async (status) => {
    return getJobsByStatus(status)
  }, [])

  return { jobs, loading, error, create, update, remove, byStatus, refresh }
}
