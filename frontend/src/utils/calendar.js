export function addMinutesToTime(time, minutesToAdd) {
  const [hour, minute] = time.split(':').map(Number)
  const totalMinutes = hour * 60 + minute + minutesToAdd
  const clampedMinutes = Math.min(totalMinutes, 23 * 60 + 59)
  const hh = String(Math.floor(clampedMinutes / 60)).padStart(2, '0')
  const mm = String(clampedMinutes % 60).padStart(2, '0')
  return `${hh}:${mm}`
}

export function createEventId(prefix = 'manual') {
  if (globalThis.crypto?.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}`
}

export function formatMinutesCompact(totalMinutes) {
  const normalized = ((totalMinutes % (24 * 60)) + 24 * 60) % (24 * 60)
  const hour24 = Math.floor(normalized / 60)
  const minute = normalized % 60
  const period = hour24 >= 12 ? 'p.m.' : 'a.m.'
  const hour12 = hour24 % 12 || 12
  return `${hour12}:${String(minute).padStart(2, '0')}${period}`
}

export function minutesToDurationLabel(totalMinutes) {
  if (totalMinutes <= 0) return '(0 mins)'
  if (totalMinutes < 60) return `(${totalMinutes} mins)`
  if (totalMinutes % 60 === 0) {
    const hours = totalMinutes / 60
    return hours === 1 ? '(1 hr)' : `(${hours} hrs)`
  }
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `(${hours} hr ${minutes} mins)`
}

export function toIsoFromParts(date, time) {
  const [year, month, day] = date.split('-').map(Number)
  const [hour24, minute] = time.split(':').map(Number)
  return new Date(year, month - 1, day, hour24, minute, 0, 0).toISOString()
}

function csvCell(value) {
  let safe = String(value ?? '')
  if (/^[=+\-@]/.test(safe)) {
    safe = "'" + safe
  }
  return `"${safe.replaceAll('"', '""')}"`
}

export function downloadCsv({ filename, headers, rows }) {
  const content = [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\n')
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
