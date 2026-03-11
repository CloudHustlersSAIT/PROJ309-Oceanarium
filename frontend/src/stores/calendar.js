import { defineStore } from 'pinia'
import { getSchedules, rescheduleBooking } from '../services/api'

const DEFAULT_EVENT_DURATION_MINUTES = 60

function toIso(date) {
  return new Date(date).toISOString()
}

function startOfDay(date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfDay(date) {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d
}

function addMinutes(dateLike, minutes) {
  const d = new Date(dateLike)
  d.setMinutes(d.getMinutes() + minutes)
  return d
}

function safeId(prefix) {
  if (globalThis.crypto?.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}`
}

function overlaps(aStart, aEnd, bStart, bEnd) {
  return aStart < bEnd && bStart < aEnd
}

function parseDateTimeKeepingWallClock(rawValue) {
  if (rawValue == null) return null
  const raw = String(rawValue).trim()
  if (!raw) return null

  // Keep API wall-clock values stable across browsers by ignoring timezone suffixes.
  const dateTimeMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2})(?::(\d{2}))?)?/)

  if (dateTimeMatch) {
    const year = Number(dateTimeMatch[1])
    const month = Number(dateTimeMatch[2])
    const day = Number(dateTimeMatch[3])
    const hour = Number(dateTimeMatch[4] ?? 0)
    const minute = Number(dateTimeMatch[5] ?? 0)
    const second = Number(dateTimeMatch[6] ?? 0)

    const parsed = new Date(year, month - 1, day, hour, minute, second, 0)
    if (!Number.isNaN(parsed.getTime())) return parsed
  }

  const fallback = new Date(raw)
  return Number.isNaN(fallback.getTime()) ? null : fallback
}

function getDateField(record) {
  const dateFields = ['date', 'booking_date', 'start_date', 'start', 'datetime', 'time']
  const raw = dateFields.map((f) => record?.[f]).find(Boolean)
  if (!raw) return null

  return parseDateTimeKeepingWallClock(raw)
}

function mapLanguage(languageCode) {
  if (!languageCode) return 'English'
  const normalized = String(languageCode).trim().toLowerCase()
  if (normalized === 'en' || normalized === 'english') return 'English'
  if (normalized === 'pt' || normalized === 'portuguese') return 'Portuguese'
  if (normalized === 'es' || normalized === 'spanish') return 'Spanish'
  if (normalized === 'fr' || normalized === 'french') return 'French'
  if (normalized === 'zh' || normalized === 'chinese') return 'Chinese'
  return String(languageCode)
}

function normalizeSchedule(schedule) {
  const start =
    parseDateTimeKeepingWallClock(schedule.event_start_datetime) ||
    getDateField(schedule) ||
    new Date()
  const fallbackEnd = addMinutes(start, DEFAULT_EVENT_DURATION_MINUTES)
  const rawEndCandidate = schedule.event_end_datetime
    ? parseDateTimeKeepingWallClock(schedule.event_end_datetime)
    : fallbackEnd
  const rawEnd = rawEndCandidate instanceof Date ? rawEndCandidate : fallbackEnd
  const end = Number.isNaN(rawEnd.getTime()) || rawEnd <= start ? fallbackEnd : rawEnd
  const durationMinutes = Math.max(15, Math.round((end - start) / 60000))

  return {
    id: `schedule-${schedule.id ?? safeId('schedule')}`,
    source: 'schedule',
    sourceId: schedule.id ?? null,
    title: schedule.tour_name || `Tour ${schedule.tour_id ?? ''}`.trim() || 'Scheduled Tour',
    start: toIso(start),
    end: toIso(end),
    resourceId: `guide-${schedule.guide_id ?? 'unassigned'}`,
    resourceName: schedule.guide_name || 'Unassigned Guide',
    guideId: schedule.guide_id ?? null,
    productId: schedule.tour_id ?? null,
    durationMinutes,
    status: schedule.status || 'scheduled',
    type: 'tour',
    priority: 'medium',
    conflictFlag: false,
    notes: schedule.reservation_count != null ? `Reservations: ${schedule.reservation_count}` : '',
    customerId: null,
    tourId: Number(schedule.tour_id ?? 0),
    adultTickets: null,
    childTickets: null,
    language: mapLanguage(schedule.language_code),
    reservationCount: Number(schedule.reservation_count ?? 0),
  }
}

export const useCalendarStore = defineStore('calendar', {
  state: () => ({
    currentView: 'month',
    selectedDate: toIso(new Date()),
    events: [],
    filters: {
      userIds: [],
      teamIds: [],
      statuses: [],
      eventTypes: [],
      conflictsOnly: false,
      search: '',
    },
    selectedEvent: null,
    conflicts: {},
    resources: [],
    bulkSelection: [],
    loading: false,
    error: null,
  }),
  getters: {
    selectedDateObj: (state) => new Date(state.selectedDate),
    visibleRange(state) {
      const selected = new Date(state.selectedDate)

      if (state.currentView === 'day') {
        return { start: startOfDay(selected), end: endOfDay(selected) }
      }

      if (state.currentView === 'week') {
        const start = startOfDay(selected)
        start.setDate(start.getDate() - start.getDay())
        const end = endOfDay(start)
        end.setDate(end.getDate() + 6)
        return { start, end }
      }

      const start = new Date(selected.getFullYear(), selected.getMonth(), 1)
      const end = endOfDay(new Date(selected.getFullYear(), selected.getMonth() + 1, 0))
      return { start, end }
    },
    filteredEvents(state) {
      const text = state.filters.search.trim().toLowerCase()

      return state.events.filter((event) => {
        if (state.filters.statuses.length && !state.filters.statuses.includes(event.status))
          return false
        if (state.filters.eventTypes.length && !state.filters.eventTypes.includes(event.type))
          return false
        if (state.filters.conflictsOnly && !state.conflicts[event.id]) return false

        if (text) {
          const searchable = `${event.title} ${event.notes} ${event.resourceName}`.toLowerCase()
          if (!searchable.includes(text)) return false
        }

        return true
      })
    },
    eventsInRange() {
      return this.filteredEvents.filter((event) => {
        const start = new Date(event.start)
        const end = new Date(event.end)
        return start <= this.visibleRange.end && end >= this.visibleRange.start
      })
    },
    occupancyByResource() {
      const totals = {}
      const perResourceCapacityMinutes = this.currentView === 'day' ? 8 * 60 : 40 * 60

      this.eventsInRange.forEach((event) => {
        const start = new Date(event.start)
        const end = new Date(event.end)
        const duration = Math.max(15, Math.round((end - start) / 60000))
        totals[event.resourceId] = (totals[event.resourceId] || 0) + duration
      })

      return Object.fromEntries(
        Object.entries(totals).map(([resourceId, minutes]) => [
          resourceId,
          Math.min(100, Math.round((minutes / perResourceCapacityMinutes) * 100)),
        ]),
      )
    },
    hasConflicts: (state) => Object.keys(state.conflicts).length > 0,
  },
  actions: {
    setView(view) {
      this.currentView = view
    },
    setDate(dateLike) {
      this.selectedDate = toIso(dateLike)
    },
    navigate(direction) {
      const next = new Date(this.selectedDate)

      if (this.currentView === 'day') next.setDate(next.getDate() + direction)
      if (this.currentView === 'week') next.setDate(next.getDate() + 7 * direction)
      if (this.currentView === 'month') next.setMonth(next.getMonth() + direction)

      this.selectedDate = toIso(next)
    },
    setFilters(payload) {
      this.filters = {
        ...this.filters,
        ...payload,
      }
    },
    selectEvent(eventOrNull) {
      this.selectedEvent = eventOrNull ? { ...eventOrNull } : null
    },
    toggleBulkSelection(eventId) {
      if (this.bulkSelection.includes(eventId)) {
        this.bulkSelection = this.bulkSelection.filter((id) => id !== eventId)
      } else {
        this.bulkSelection.push(eventId)
      }
    },
    clearBulkSelection() {
      this.bulkSelection = []
    },
    applyBulkStatus(status) {
      this.events = this.events.map((event) =>
        this.bulkSelection.includes(event.id) ? { ...event, status } : event,
      )
      this.recomputeConflicts()
    },
    updateEvent(updated) {
      this.events = this.events.map((event) => (event.id === updated.id ? { ...updated } : event))
      this.selectEvent(updated)
      this.recomputeConflicts()
    },
    duplicateEvent(eventId) {
      const found = this.events.find((event) => event.id === eventId)
      if (!found) return

      const start = addMinutes(found.start, 60)
      const end = addMinutes(found.end, 60)

      const clone = {
        ...found,
        id: safeId(found.source),
        sourceId: null,
        start: toIso(start),
        end: toIso(end),
        title: `${found.title} (Copy)`,
      }

      this.events.push(clone)
      this.selectEvent(clone)
      this.recomputeConflicts()
    },
    deleteEvent(eventId) {
      this.events = this.events.filter((event) => event.id !== eventId)
      if (this.selectedEvent?.id === eventId) this.selectedEvent = null
      this.bulkSelection = this.bulkSelection.filter((id) => id !== eventId)
      this.recomputeConflicts()
    },
    moveEvent(eventId, startLike) {
      const found = this.events.find((event) => event.id === eventId)
      if (!found) return

      const start = new Date(startLike)
      const duration = new Date(found.end) - new Date(found.start)
      const end = new Date(start.getTime() + duration)
      this.updateEvent({ ...found, start: toIso(start), end: toIso(end) })
    },
    resizeEventDuration(eventId, minutesDelta) {
      const found = this.events.find((event) => event.id === eventId)
      if (!found) return

      const end = addMinutes(found.end, minutesDelta)
      if (end <= new Date(found.start)) return
      this.updateEvent({ ...found, end: toIso(end) })
    },
    async saveSelectedEvent() {
      if (!this.selectedEvent) return

      const selectedBefore = this.events.find((event) => event.id === this.selectedEvent.id)
      this.updateEvent(this.selectedEvent)

      if (this.selectedEvent.source === 'booking' && this.selectedEvent.sourceId) {
        const oldDate = selectedBefore ? new Date(selectedBefore.start).toDateString() : ''
        const newDate = new Date(this.selectedEvent.start).toDateString()
        if (oldDate !== newDate) {
          await rescheduleBooking(
            this.selectedEvent.sourceId,
            this.selectedEvent.start.slice(0, 10),
          )
        }
      }
    },
    recomputeConflicts() {
      const conflicts = {}
      const grouped = {}

      this.events.forEach((event) => {
        // Conflict only matters when a concrete guide is assigned.
        if (!event.guideId) return
        const key = `guide-${event.guideId}`
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(event)
      })

      Object.values(grouped).forEach((events) => {
        const sorted = [...events].sort((a, b) => new Date(a.start) - new Date(b.start))
        for (let i = 0; i < sorted.length; i += 1) {
          for (let j = i + 1; j < sorted.length; j += 1) {
            const a = sorted[i]
            const b = sorted[j]
            const doOverlap = overlaps(
              new Date(a.start),
              new Date(a.end),
              new Date(b.start),
              new Date(b.end),
            )
            if (doOverlap) {
              if (!conflicts[a.id]) conflicts[a.id] = { conflictWith: [] }
              if (!conflicts[b.id]) conflicts[b.id] = { conflictWith: [] }
              conflicts[a.id].conflictWith.push(b.id)
              conflicts[b.id].conflictWith.push(a.id)
            }
          }
        }
      })

      this.conflicts = conflicts
      this.events = this.events.map((event) => ({
        ...event,
        conflictFlag: Boolean(conflicts[event.id]),
      }))
    },
    async loadEvents() {
      this.loading = true
      this.error = null

      try {
        const schedules = await getSchedules()
        const normalizedSchedules = (Array.isArray(schedules) ? schedules : []).map(
          normalizeSchedule,
        )
        this.events = [...normalizedSchedules]

        const resourceMap = {}
        this.events.forEach((event) => {
          resourceMap[event.resourceId] = {
            id: event.resourceId,
            name: event.resourceName,
            type: event.resourceId.startsWith('team-') ? 'team' : 'user',
          }
        })
        this.resources = Object.values(resourceMap)

        this.recomputeConflicts()
      } catch (error) {
        this.error = error?.message || String(error)
      } finally {
        this.loading = false
      }
    },
  },
})
