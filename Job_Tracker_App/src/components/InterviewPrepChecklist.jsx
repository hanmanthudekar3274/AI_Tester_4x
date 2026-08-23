import { useState, useEffect } from 'react'
import { CheckSquare, Square, ClipboardList } from 'lucide-react'

const PREP_ITEMS = [
  'Research company (mission, products, culture, recent news)',
  'Review the job description carefully',
  'Prepare 3–5 STAR stories (Situation, Task, Action, Result)',
  'Practice common behavioral interview questions',
  'Prepare 5+ thoughtful questions to ask the interviewer',
  'Research the interviewers on LinkedIn',
  'Review your own resume top-to-bottom',
  'Test your tech setup (camera, mic, lighting)',
  'Plan travel or login logistics',
  'Send a thank-you note within 24 hours of the interview',
]

function storageKey(jobId) {
  return `prep_checklist_${jobId}`
}

export default function InterviewPrepChecklist({ jobId }) {
  const [checked, setChecked] = useState({})

  useEffect(() => {
    if (!jobId) return
    try {
      const stored = localStorage.getItem(storageKey(jobId))
      setChecked(stored ? JSON.parse(stored) : {})
    } catch {
      setChecked({})
    }
  }, [jobId])

  function toggle(index) {
    setChecked((prev) => {
      const next = { ...prev, [index]: !prev[index] }
      try { localStorage.setItem(storageKey(jobId), JSON.stringify(next)) } catch {}
      return next
    })
  }

  const doneCount = PREP_ITEMS.filter((_, i) => checked[i]).length

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ClipboardList size={13} className="text-violet-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Interview Prep</span>
        </div>
        <span className="text-xs text-gray-600 tabular-nums">{doneCount}/{PREP_ITEMS.length}</span>
      </div>

      <div className="h-1 bg-gray-800 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-violet-500 rounded-full transition-all duration-500"
          style={{ width: `${(doneCount / PREP_ITEMS.length) * 100}%` }}
        />
      </div>

      <div className="space-y-1.5">
        {PREP_ITEMS.map((item, i) => (
          <button
            key={i}
            onClick={() => toggle(i)}
            className="w-full flex items-start gap-2.5 text-left p-2 rounded-lg hover:bg-gray-800/60 transition-colors group"
          >
            <span className="shrink-0 mt-0.5">
              {checked[i]
                ? <CheckSquare size={14} className="text-violet-400" />
                : <Square size={14} className="text-gray-600 group-hover:text-gray-400 transition-colors" />
              }
            </span>
            <span className={`text-xs leading-relaxed ${checked[i] ? 'text-gray-600 line-through' : 'text-gray-400'}`}>
              {item}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
