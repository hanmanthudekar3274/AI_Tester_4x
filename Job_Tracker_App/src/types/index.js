/**
 * @typedef {'wishlist' | 'applied' | 'phone_screen' | 'interview' | 'offer' | 'rejected'} JobStatus
 */

/**
 * @typedef {Object} InterviewFeedback
 * @property {string} [skills]          - Strengths noted during interviews
 * @property {string} [weaknesses]      - Areas for improvement
 * @property {string} [rejectionReason] - Why the application was rejected
 * @property {string} [interviewNotes]  - General interview notes
 * @property {string} [followUpDate]    - ISO date for follow-up
 */

/**
 * @typedef {Object} OfferDetails
 * @property {string} [baseSalary]   - Base salary as a number string
 * @property {string} [currency]     - Currency code (default: USD)
 * @property {string} [bonus]        - Bonus amount or description
 * @property {string} [stockOptions] - Stock/equity description
 * @property {string} [startDate]    - ISO start date
 * @property {string} [benefits]     - Benefits summary
 * @property {string} [deadline]     - ISO offer expiration date
 * @property {string} [notes]        - Offer-specific notes
 */

/**
 * @typedef {Object} Job
 * @property {string}             id            - Unique ID (nanoid)
 * @property {string}             companyName   - Company name (required)
 * @property {string}             jobTitle      - Job title (required)
 * @property {JobStatus}          status        - Application status
 * @property {string}             [location]    - Office location or "Remote"
 * @property {string}             [salary]      - Salary range
 * @property {string}             [url]         - Link to job posting
 * @property {string}             [notes]       - Free-form notes
 * @property {string}             [resumeTag]   - Resume version used
 * @property {string}             [appliedDate] - ISO date when application was submitted
 * @property {InterviewFeedback}  [interviewFeedback] - Interview notes and feedback
 * @property {OfferDetails}       [offerDetails]      - Details of any offer received
 * @property {string}             createdAt     - ISO timestamp of record creation
 * @property {string}             updatedAt     - ISO timestamp of last update
 */

export const JOB_STATUSES = /** @type {const} */ ([
  'wishlist',
  'applied',
  'phone_screen',
  'interview',
  'offer',
  'rejected',
])

export const STATUS_LABELS = {
  wishlist:     'Wishlist',
  applied:      'Applied',
  phone_screen: 'Phone Screen',
  interview:    'Interview',
  offer:        'Offer',
  rejected:     'Rejected',
}

/** @param {Partial<Job>} overrides */
export function createJob(overrides = {}) {
  const now = new Date().toISOString()
  return /** @type {Job} */ ({
    id:          '',
    companyName: '',
    jobTitle:    '',
    status:      'wishlist',
    location:    '',
    salary:      '',
    url:         '',
    notes:       '',
    resumeTag:   '',
    appliedDate: '',
    interviewFeedback: {
      skills: '', weaknesses: '', rejectionReason: '', interviewNotes: '', followUpDate: '',
    },
    offerDetails: {
      baseSalary: '', currency: 'USD', bonus: '', stockOptions: '',
      startDate: '', benefits: '', deadline: '', notes: '',
    },
    createdAt:   now,
    updatedAt:   now,
    ...overrides,
  })
}
