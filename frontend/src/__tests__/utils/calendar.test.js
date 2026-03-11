import { describe, it, expect, vi } from 'vitest'
import {
  addMinutesToTime,
  formatMinutesCompact,
  minutesToDurationLabel,
  toIsoFromParts,
  createEventId,
  downloadCsv,
} from '../../utils/calendar'

describe('addMinutesToTime', () => {
  it('adds minutes within the same hour', () => {
    expect(addMinutesToTime('10:00', 15)).toBe('10:15')
  })

  it('rolls over to the next hour', () => {
    expect(addMinutesToTime('10:45', 30)).toBe('11:15')
  })

  it('clamps at 23:59', () => {
    expect(addMinutesToTime('23:30', 60)).toBe('23:59')
  })

  it('handles midnight start', () => {
    expect(addMinutesToTime('00:00', 90)).toBe('01:30')
  })
})

describe('formatMinutesCompact', () => {
  it('formats morning time', () => {
    expect(formatMinutesCompact(9 * 60)).toBe('9:00a.m.')
  })

  it('formats afternoon time', () => {
    expect(formatMinutesCompact(14 * 60 + 30)).toBe('2:30p.m.')
  })

  it('formats noon', () => {
    expect(formatMinutesCompact(12 * 60)).toBe('12:00p.m.')
  })

  it('formats midnight', () => {
    expect(formatMinutesCompact(0)).toBe('12:00a.m.')
  })

  it('handles negative values via normalization', () => {
    const result = formatMinutesCompact(-60)
    expect(result).toMatch(/\d{1,2}:\d{2}[ap]\.m\./)
  })
})

describe('minutesToDurationLabel', () => {
  it('formats zero', () => {
    expect(minutesToDurationLabel(0)).toBe('(0 mins)')
  })

  it('formats minutes under an hour', () => {
    expect(minutesToDurationLabel(45)).toBe('(45 mins)')
  })

  it('formats exactly one hour', () => {
    expect(minutesToDurationLabel(60)).toBe('(1 hr)')
  })

  it('formats multiple exact hours', () => {
    expect(minutesToDurationLabel(120)).toBe('(2 hrs)')
  })

  it('formats hours with remaining minutes', () => {
    expect(minutesToDurationLabel(90)).toBe('(1 hr 30 mins)')
  })

  it('formats negative as (0 mins)', () => {
    expect(minutesToDurationLabel(-10)).toBe('(0 mins)')
  })
})

describe('toIsoFromParts', () => {
  it('combines date and time into ISO string', () => {
    const result = toIsoFromParts('2026-03-10', '14:30')
    const parsed = new Date(result)
    expect(parsed.getFullYear()).toBe(2026)
    expect(parsed.getMonth()).toBe(2)
    expect(parsed.getDate()).toBe(10)
    expect(parsed.getHours()).toBe(14)
    expect(parsed.getMinutes()).toBe(30)
  })
})

describe('createEventId', () => {
  it('returns a string starting with the prefix', () => {
    const id = createEventId('test')
    expect(id).toMatch(/^test-/)
  })

  it('generates unique ids', () => {
    const a = createEventId('evt')
    const b = createEventId('evt')
    expect(a).not.toBe(b)
  })
})

describe('downloadCsv', () => {
  it('creates and clicks a download link', () => {
    const revokeObjectURL = vi.fn()
    const createObjectURL = vi.fn(() => 'blob:mock')
    globalThis.URL.createObjectURL = createObjectURL
    globalThis.URL.revokeObjectURL = revokeObjectURL

    const clickSpy = vi.fn()
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {})
    vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click: clickSpy,
    })

    downloadCsv({
      filename: 'test.csv',
      headers: ['Name', 'Value'],
      rows: [
        ['Alice', '100'],
        ['=Bob', 'formula'],
      ],
    })

    expect(createObjectURL).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')

    appendChildSpy.mockRestore()
    removeChildSpy.mockRestore()
  })
})
