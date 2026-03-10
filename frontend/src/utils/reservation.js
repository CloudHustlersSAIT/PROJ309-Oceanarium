export function sanitizeNumericInput(value, maxLength) {
  return String(value ?? '')
    .replace(/\D/g, '')
    .slice(0, maxLength)
}

export function parseApiDateTimeAsWallClock(rawValue) {
  if (rawValue == null) return null
  const raw = String(rawValue).trim()
  if (!raw) return null

  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2})(?::(\d{2}))?)?/)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const hour = Number(match[4] ?? 0)
  const minute = Number(match[5] ?? 0)
  const second = Number(match[6] ?? 0)

  const parsed = new Date(year, month - 1, day, hour, minute, second, 0)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatStatusLabel(status, emptyFallback = '-') {
  const normalized = String(status || '')
    .trim()
    .toLowerCase()
  if (!normalized) return emptyFallback
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

export function mapLanguageCodeToName(code) {
  const normalized = String(code || '')
    .trim()
    .toLowerCase()
  if (normalized === 'en') return 'English'
  if (normalized === 'pt') return 'Portuguese'
  if (normalized === 'es') return 'Spanish'
  if (normalized === 'fr') return 'French'
  if (normalized === 'zh') return 'Chinese'
  return ''
}

export function extractScheduleTimeHHMM(rawValue) {
  const raw = String(rawValue || '').trim()
  if (!raw) return '--:--'

  const isoMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/)
  if (isoMatch) return `${isoMatch[4]}:${isoMatch[5]}`

  const genericTimeMatch = raw.match(/(\d{2}):(\d{2})/)
  return genericTimeMatch ? `${genericTimeMatch[1]}:${genericTimeMatch[2]}` : '--:--'
}

export function formatScheduleTimeForDisplay(rawValue, options = {}) {
  const { style = 'us' } = options
  const hhmm = extractScheduleTimeHHMM(rawValue)
  if (hhmm === '--:--') return hhmm
  if (style !== 'us') return hhmm

  const [hourText, minuteText] = hhmm.split(':')
  const hour24 = Number(hourText)
  if (!Number.isInteger(hour24)) return hhmm

  const period = hour24 >= 12 ? 'pm' : 'am'
  const hour12 = hour24 % 12 || 12
  return `${String(hour12).padStart(2, '0')}:${minuteText} ${period}`
}

export function formatScheduleDateTimeForDisplay(rawValue) {
  const parsed = parseApiDateTimeAsWallClock(rawValue)
  if (!parsed) return '-'

  const month = parsed.toLocaleDateString('en-US', { month: 'short' })
  const day = String(parsed.getDate()).padStart(2, '0')
  const year = parsed.getFullYear()
  const time = formatScheduleTimeForDisplay(rawValue, { style: 'us' })
  return `${month} ${day}, ${year}, ${time}`
}

export function formatLocalTimeLowerAmPm(dateLike) {
  const parsed = new Date(dateLike)
  if (Number.isNaN(parsed.getTime())) return '--:--'

  return parsed
    .toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
    .toLowerCase()
}
