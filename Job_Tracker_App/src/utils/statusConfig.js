export const COLUMN_ORDER = ['wishlist', 'applied', 'phone_screen', 'interview', 'offer', 'rejected']

// All class strings must be complete so Tailwind can detect them at build time
export const STATUS_CONFIG = {
  wishlist: {
    label:       'Wishlist',
    border:      'border-l-blue-500',
    dot:         'bg-blue-500',
    headerText:  'text-blue-400',
    badge:       'bg-blue-500/15 text-blue-300',
  },
  applied: {
    label:       'Applied',
    border:      'border-l-amber-500',
    dot:         'bg-amber-500',
    headerText:  'text-amber-400',
    badge:       'bg-amber-500/15 text-amber-300',
  },
  phone_screen: {
    label:       'Phone Screen',
    border:      'border-l-violet-500',
    dot:         'bg-violet-500',
    headerText:  'text-violet-400',
    badge:       'bg-violet-500/15 text-violet-300',
  },
  interview: {
    label:       'Interview',
    border:      'border-l-orange-500',
    dot:         'bg-orange-500',
    headerText:  'text-orange-400',
    badge:       'bg-orange-500/15 text-orange-300',
  },
  offer: {
    label:       'Offer',
    border:      'border-l-emerald-500',
    dot:         'bg-emerald-500',
    headerText:  'text-emerald-400',
    badge:       'bg-emerald-500/15 text-emerald-300',
  },
  rejected: {
    label:       'Rejected',
    border:      'border-l-red-400',
    dot:         'bg-red-400',
    headerText:  'text-red-400',
    badge:       'bg-red-500/15 text-red-300',
  },
}
