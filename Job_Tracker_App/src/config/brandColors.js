export const BRAND = {
  name: 'JobFlow',
  tagline: 'Track smarter. Land faster.',
}

// Reusable focus-ring class string — Tailwind detects these via static scan
export const FOCUS_RING = [
  'focus-visible:outline-none',
  'focus-visible:ring-2',
  'focus-visible:ring-primary-500',
  'focus-visible:ring-offset-2',
  'focus-visible:ring-offset-gray-900',
].join(' ')

export const FOCUS_RING_DARK = [
  'focus-visible:outline-none',
  'focus-visible:ring-2',
  'focus-visible:ring-primary-500',
  'focus-visible:ring-offset-2',
  'focus-visible:ring-offset-gray-950',
].join(' ')

// Semantic button class presets
export const BTN_PRIMARY = [
  'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-all',
  'bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-500/20',
  FOCUS_RING,
].join(' ')

export const BTN_GHOST = [
  'flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
  'bg-gray-800 border border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600',
  FOCUS_RING,
].join(' ')
