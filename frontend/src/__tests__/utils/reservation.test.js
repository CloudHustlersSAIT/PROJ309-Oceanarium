import { describe, it, expect } from 'vitest'
import {
  sanitizeNumericInput,
  parseApiDateTimeAsWallClock,
  formatStatusLabel,
  mapLanguageCodeToName,
  extractScheduleTimeHHMM,
  formatScheduleTimeForDisplay,
  formatScheduleDateTimeForDisplay,
  formatLocalTimeLowerAmPm,
} from '../../utils/reservation'

describe('sanitizeNumericInput', () => {
  it('strips non-digit characters', () => {
    expect(sanitizeNumericInput('abc123def', 10)).toBe('123')
  })

  it('truncates to maxLength', () => {
    expect(sanitizeNumericInput('123456', 3)).toBe('123')
  })

  it('handles null/undefined', () => {
    expect(sanitizeNumericInput(null, 5)).toBe('')
    expect(sanitizeNumericInput(undefined, 5)).toBe('')
  })
})

describe('parseApiDateTimeAsWallClock', () => {
  it('parses ISO datetime string to local Date', () => {
    const result = parseApiDateTimeAsWallClock('2026-03-10T14:30:00')
    expect(result).toBeInstanceOf(Date)
    expect(result.getFullYear()).toBe(2026)
    expect(result.getMonth()).toBe(2)
    expect(result.getDate()).toBe(10)
    expect(result.getHours()).toBe(14)
    expect(result.getMinutes()).toBe(30)
  })

  it('parses date-only string with zeroed time', () => {
    const result = parseApiDateTimeAsWallClock('2026-06-15')
    expect(result.getFullYear()).toBe(2026)
    expect(result.getHours()).toBe(0)
  })

  it('returns null for null/undefined/empty', () => {
    expect(parseApiDateTimeAsWallClock(null)).toBeNull()
    expect(parseApiDateTimeAsWallClock(undefined)).toBeNull()
    expect(parseApiDateTimeAsWallClock('')).toBeNull()
  })

  it('returns null for unparseable string', () => {
    expect(parseApiDateTimeAsWallClock('not-a-date')).toBeNull()
  })
})

describe('formatStatusLabel', () => {
  it('capitalizes first letter', () => {
    expect(formatStatusLabel('confirmed')).toBe('Confirmed')
  })

  it('handles uppercase input', () => {
    expect(formatStatusLabel('CANCELLED')).toBe('Cancelled')
  })

  it('returns fallback for empty/null', () => {
    expect(formatStatusLabel('')).toBe('-')
    expect(formatStatusLabel(null)).toBe('-')
    expect(formatStatusLabel(null, 'N/A')).toBe('N/A')
  })
})

describe('mapLanguageCodeToName', () => {
  it('maps known codes', () => {
    expect(mapLanguageCodeToName('en')).toBe('English')
    expect(mapLanguageCodeToName('pt')).toBe('Portuguese')
    expect(mapLanguageCodeToName('es')).toBe('Spanish')
    expect(mapLanguageCodeToName('fr')).toBe('French')
    expect(mapLanguageCodeToName('zh')).toBe('Chinese')
  })

  it('returns empty for unknown codes', () => {
    expect(mapLanguageCodeToName('xx')).toBe('')
  })

  it('handles null/empty', () => {
    expect(mapLanguageCodeToName('')).toBe('')
    expect(mapLanguageCodeToName(null)).toBe('')
  })
})

describe('extractScheduleTimeHHMM', () => {
  it('extracts time from ISO string', () => {
    expect(extractScheduleTimeHHMM('2026-03-10T14:30:00')).toBe('14:30')
  })

  it('extracts time from generic time string', () => {
    expect(extractScheduleTimeHHMM('09:15')).toBe('09:15')
  })

  it('returns --:-- for empty/null', () => {
    expect(extractScheduleTimeHHMM('')).toBe('--:--')
    expect(extractScheduleTimeHHMM(null)).toBe('--:--')
  })
})

describe('formatScheduleTimeForDisplay', () => {
  it('formats in US style by default', () => {
    expect(formatScheduleTimeForDisplay('2026-03-10T14:30:00')).toBe('02:30 pm')
  })

  it('formats midnight correctly', () => {
    expect(formatScheduleTimeForDisplay('2026-03-10T00:00:00')).toBe('12:00 am')
  })

  it('returns raw HH:MM for non-US style', () => {
    expect(formatScheduleTimeForDisplay('2026-03-10T14:30:00', { style: '24h' })).toBe('14:30')
  })

  it('returns --:-- for invalid input', () => {
    expect(formatScheduleTimeForDisplay('')).toBe('--:--')
  })
})

describe('formatScheduleDateTimeForDisplay', () => {
  it('formats full datetime string', () => {
    const result = formatScheduleDateTimeForDisplay('2026-03-10T14:30:00')
    expect(result).toContain('Mar')
    expect(result).toContain('10')
    expect(result).toContain('2026')
  })

  it('returns dash for invalid input', () => {
    expect(formatScheduleDateTimeForDisplay(null)).toBe('-')
  })
})

describe('formatLocalTimeLowerAmPm', () => {
  it('formats a valid date to lowercase am/pm time', () => {
    const result = formatLocalTimeLowerAmPm(new Date(2026, 2, 10, 14, 30))
    expect(result).toMatch(/02:30\s*pm/)
  })

  it('returns --:-- for invalid date', () => {
    expect(formatLocalTimeLowerAmPm('garbage')).toBe('--:--')
  })
})
