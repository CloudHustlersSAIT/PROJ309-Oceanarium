import { defineStore } from 'pinia'
import { getTours, getBookings, rescheduleBooking } from '../services/api'

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

function getDateField(record) {
  const dateFields = ['date', 'booking_date', 'start_date', 'start', 'datetime', 'time']
  const raw = dateFields.map((f) => record?.[f]).find(Boolean)
  if (!raw) return null

  const parsed = new Date(raw)
  return isNaN(parsed) ? null : parsed
}

function normalizeTour(tour) {
  const start = getDateField(tour) || new Date()
  const end = addMinutes(start, 60)

  return {
    id: `tour-${tour.id ?? safeId('tour')}`,
    source: 'tour',
    sourceId: tour.id ?? null,
    title: tour.tour || tour.title || 'Tour',
    start: toIso(start),
    end: toIso(end),
    resourceId: `guide-${tour.guide_id ?? tour.guide ?? 'unassigned'}`,
    resourceName: tour.guide || tour.guide_name || 'Unassigned Guide',
    status: 'scheduled',
    type: 'tour',
    priority: 'medium',
    conflictFlag: false,
    notes: '',
  }
}

function normalizeBooking(booking) {
  const start = getDateField(booking) || new Date()
  const end = addMinutes(start, 60)
  const sourceId = booking.id ?? booking.booking_id ?? booking.bookingId ?? null

  return {
    id: `booking-${sourceId ?? safeId('booking')}`,
    source: 'booking',
    sourceId,
    title: booking.tour || booking.tour_name || booking.title || 'Booking',
    start: toIso(start),
    end: toIso(end),
    resourceId: `guide-${booking.guide_id ?? booking.guide ?? 'unassigned'}`,
    resourceName: booking.guide || booking.guide_name || 'Unassigned Guide',
    status: booking.status || 'pending',
    type: booking.type || 'booking',
    priority: booking.priority || 'medium',
    conflictFlag: false,
    notes: booking.notes || '',
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
        if (!grouped[event.resourceId]) grouped[event.resourceId] = []
        grouped[event.resourceId].push(event)
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
        const [tours, bookings] = await Promise.all([getTours(), getBookings()])
        const normalizedTours = (Array.isArray(tours) ? tours : []).map(normalizeTour)
        const normalizedBookings = (Array.isArray(bookings) ? bookings : []).map(normalizeBooking)
        this.events = [...normalizedTours, ...normalizedBookings]

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

