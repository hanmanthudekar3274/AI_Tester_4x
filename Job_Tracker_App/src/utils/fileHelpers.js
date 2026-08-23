/**
 * Triggers a browser download of `data` as a pretty-printed JSON file.
 * @param {object} data
 * @param {string} filename
 */
export function downloadJSON(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href     = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Reads a File object and returns its parsed JSON content.
 * @param {File} file
 * @returns {Promise<object>}
 */
export async function readFileAsJSON(file) {
  const text = await file.text()
  try {
    return JSON.parse(text)
  } catch {
    throw new Error('File is not valid JSON')
  }
}
