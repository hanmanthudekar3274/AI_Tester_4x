export const COLUMN_MESSAGES = {
  wishlist: {
    empty:  'Your wishlist is empty',
    sub:    'Add jobs you\'re excited about exploring.',
    dropHint: 'Drop here',
  },
  applied: {
    empty:  'No active applications',
    sub:    'Log every application — consistency compounds.',
    dropHint: 'Drop here',
  },
  phone_screen: {
    empty:  'No phone screens yet',
    sub:    'Keep applying — that call is coming.',
    dropHint: 'Drop here',
  },
  interview: {
    empty:  'No interviews scheduled',
    sub:    'Prep well and you\'ll be here soon.',
    dropHint: 'Drop here',
  },
  offer: {
    empty:  'No offers yet',
    sub:    'Great things take time. Keep going.',
    dropHint: 'Drop here',
  },
  rejected: {
    empty:  'Nothing here',
    sub:    'Every no gets you closer to the right yes.',
    dropHint: 'Drop here',
  },
}

export const EMPTY_BOARD = {
  heading: 'Welcome to JobFlow',
  sub:     'Your job search, organized. Track applications, log interviews, and land your dream role.',
  cta:     'Add your first job',
  features: ['100% private', 'Works offline', 'Export anytime'],
}

export const TOASTS = {
  jobAdded:   () => '🎉 Application added! Keep building that pipeline.',
  jobDeleted: () => 'Application removed.',
  exported:   (n) => `✅ Exported ${n} job${n !== 1 ? 's' : ''}`,
  imported:   (n, skipped) =>
    skipped > 0
      ? `✅ Imported ${n} jobs (${skipped} skipped)`
      : `✅ Imported ${n} job${n !== 1 ? 's' : ''}`,
  importFailed: (msg) => `❌ Import failed: ${msg}`,
  exportFailed: (msg) => `❌ Export failed: ${msg}`,
  deleteFailed: () => '❌ Failed to remove application',
}
