import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCalendarStore } from '../../stores/calendar'

vi.mock('../../services/api', () => ({
  getSchedules: vi.fn(),
  rescheduleBooking: vi.fn(),
}))

import { getSchedules } from '../../services/api'

describe('useCalendarStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useCalendarStore()
  })

  describe('initial state', () => {
    it('starts with month view', () => {
      expect(store.currentView).toBe('month')
    })

    it('starts with empty events', () => {
      expect(store.events).toEqual([])
    })

    it('starts with no loading or error', () => {
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('setView', () => {
    it('changes the current view', () => {
      store.setView('week')
      expect(store.currentView).toBe('week')
    })
  })

  describe('setDate', () => {
    it('sets the selected date as ISO string', () => {
      const date = new Date(2026, 5, 15)
      store.setDate(date)
      expect(new Date(store.selectedDate).getMonth()).toBe(5)
    })
  })

  describe('navigate', () => {
    it('moves forward by one day in day view', () => {
      store.setView('day')
      store.setDate(new Date(2026, 0, 10))
      store.navigate(1)
      expect(new Date(store.selectedDate).getDate()).toBe(11)
    })

    it('moves backward by one month in month view', () => {
      store.setView('month')
      store.setDate(new Date(2026, 5, 15))
      store.navigate(-1)
      expect(new Date(store.selectedDate).getMonth()).toBe(4)
    })
  })

  describe('setFilters', () => {
    it('merges partial filter updates', () => {
      store.setFilters({ search: 'dolphin' })
      expect(store.filters.search).toBe('dolphin')
      expect(store.filters.statuses).toEqual([])
    })
  })

  describe('filteredEvents', () => {
    beforeEach(() => {
      store.events = [
        {
          id: 'e1',
          title: 'Dolphin Tour',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'Guide A',
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
        {
          id: 'e2',
          title: 'Shark Dive',
          type: 'event',
          status: 'pending',
          notes: '',
          resourceName: 'Guide B',
          start: new Date(2026, 0, 10, 12, 0).toISOString(),
          end: new Date(2026, 0, 10, 13, 0).toISOString(),
        },
      ]
    })

    it('returns all events when no filters are set', () => {
      expect(store.filteredEvents).toHaveLength(2)
    })

    it('filters by status', () => {
      store.setFilters({ statuses: ['confirmed'] })
      expect(store.filteredEvents).toHaveLength(1)
      expect(store.filteredEvents[0].id).toBe('e1')
    })

    it('filters by search text', () => {
      store.setFilters({ search: 'shark' })
      expect(store.filteredEvents).toHaveLength(1)
      expect(store.filteredEvents[0].id).toBe('e2')
    })

    it('filters by event type', () => {
      store.setFilters({ eventTypes: ['tour'] })
      expect(store.filteredEvents).toHaveLength(1)
    })
  })

  describe('recomputeConflicts', () => {
    it('detects overlapping events for the same guide', () => {
      store.events = [
        {
          id: 'a',
          guideId: 1,
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
        {
          id: 'b',
          guideId: 1,
          start: new Date(2026, 0, 10, 10, 30).toISOString(),
          end: new Date(2026, 0, 10, 11, 30).toISOString(),
        },
      ]
      store.recomputeConflicts()
      expect(store.conflicts).toHaveProperty('a')
      expect(store.conflicts).toHaveProperty('b')
      expect(store.hasConflicts).toBe(true)
    })

    it('does not flag non-overlapping events', () => {
      store.events = [
        {
          id: 'a',
          guideId: 1,
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
        {
          id: 'b',
          guideId: 1,
          start: new Date(2026, 0, 10, 12, 0).toISOString(),
          end: new Date(2026, 0, 10, 13, 0).toISOString(),
        },
      ]
      store.recomputeConflicts()
      expect(store.hasConflicts).toBe(false)
    })

    it('ignores events without guideId', () => {
      store.events = [
        {
          id: 'a',
          guideId: null,
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
        {
          id: 'b',
          guideId: null,
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
      ]
      store.recomputeConflicts()
      expect(store.hasConflicts).toBe(false)
    })
  })

  describe('loadEvents', () => {
    it('loads and normalizes schedules from API', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 1,
          tour_id: 10,
          tour_name: 'Ocean Walk',
          guide_id: 5,
          guide_name: 'Maria',
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          status: 'CONFIRMED',
          language_code: 'en',
          reservation_count: 3,
        },
      ])

      await store.loadEvents()

      expect(store.loading).toBe(false)
      expect(store.events).toHaveLength(1)
      expect(store.events[0].title).toBe('Ocean Walk')
      expect(store.events[0].language).toBe('English')
      expect(store.resources.length).toBeGreaterThan(0)
    })

    it('sets error on API failure', async () => {
      getSchedules.mockRejectedValue(new Error('Network error'))

      await store.loadEvents()

      expect(store.loading).toBe(false)
      expect(store.error).toBe('Network error')
    })
  })

  describe('deleteEvent', () => {
    it('removes the event from the list', () => {
      store.events = [{ id: 'x', guideId: null, start: '', end: '' }]
      store.deleteEvent('x')
      expect(store.events).toHaveLength(0)
    })

    it('clears selectedEvent if it was the deleted one', () => {
      store.events = [{ id: 'x', guideId: null, start: '', end: '' }]
      store.selectedEvent = { id: 'x' }
      store.deleteEvent('x')
      expect(store.selectedEvent).toBeNull()
    })
  })

  describe('toggleBulkSelection', () => {
    it('adds event id to selection', () => {
      store.toggleBulkSelection('e1')
      expect(store.bulkSelection).toContain('e1')
    })

    it('removes event id if already selected', () => {
      store.bulkSelection = ['e1']
      store.toggleBulkSelection('e1')
      expect(store.bulkSelection).not.toContain('e1')
    })
  })

  describe('visibleRange', () => {
    it('returns day range for day view', () => {
      store.setView('day')
      store.setDate(new Date(2026, 0, 15))
      const range = store.visibleRange
      expect(range.start.getDate()).toBe(15)
      expect(range.end.getDate()).toBe(15)
    })

    it('returns week range for week view', () => {
      store.setView('week')
      store.setDate(new Date(2026, 0, 15))
      const range = store.visibleRange
      expect(range.end - range.start).toBeGreaterThan(5 * 24 * 60 * 60 * 1000)
    })

    it('returns month range for month view', () => {
      store.setView('month')
      store.setDate(new Date(2026, 0, 15))
      const range = store.visibleRange
      expect(range.start.getDate()).toBe(1)
    })
  })

  describe('eventsInRange', () => {
    it('returns only events within the visible range', () => {
      store.setView('day')
      store.setDate(new Date(2026, 0, 10))
      store.events = [
        {
          id: 'in',
          title: 'In Range',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'Guide',
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
        {
          id: 'out',
          title: 'Out of Range',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'Guide',
          start: new Date(2026, 0, 20, 10, 0).toISOString(),
          end: new Date(2026, 0, 20, 11, 0).toISOString(),
        },
      ]
      expect(store.eventsInRange).toHaveLength(1)
      expect(store.eventsInRange[0].id).toBe('in')
    })
  })

  describe('occupancyByResource', () => {
    it('computes occupancy percentages', () => {
      store.setView('day')
      store.setDate(new Date(2026, 0, 10))
      store.events = [
        {
          id: 'e1',
          resourceId: 'guide-1',
          title: '',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'Guide 1',
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 14, 0).toISOString(),
        },
      ]
      const occ = store.occupancyByResource
      expect(occ['guide-1']).toBeGreaterThan(0)
      expect(occ['guide-1']).toBeLessThanOrEqual(100)
    })
  })

  describe('selectEvent', () => {
    it('sets selected event as a copy', () => {
      const event = { id: 'e1', title: 'Test' }
      store.selectEvent(event)
      expect(store.selectedEvent).toEqual(event)
      expect(store.selectedEvent).not.toBe(event)
    })

    it('clears selected event with null', () => {
      store.selectedEvent = { id: 'e1' }
      store.selectEvent(null)
      expect(store.selectedEvent).toBeNull()
    })
  })

  describe('applyBulkStatus', () => {
    it('updates status for selected events', () => {
      store.events = [
        { id: 'a', status: 'pending', guideId: null, start: '', end: '' },
        { id: 'b', status: 'pending', guideId: null, start: '', end: '' },
      ]
      store.bulkSelection = ['a']
      store.applyBulkStatus('confirmed')
      expect(store.events.find((e) => e.id === 'a').status).toBe('confirmed')
      expect(store.events.find((e) => e.id === 'b').status).toBe('pending')
    })
  })

  describe('clearBulkSelection', () => {
    it('empties the bulk selection array', () => {
      store.bulkSelection = ['a', 'b']
      store.clearBulkSelection()
      expect(store.bulkSelection).toEqual([])
    })
  })

  describe('duplicateEvent', () => {
    it('adds a copy shifted by 1 hour', () => {
      const start = new Date(2026, 0, 10, 10, 0)
      const end = new Date(2026, 0, 10, 11, 0)
      store.events = [
        {
          id: 'orig',
          source: 'schedule',
          sourceId: 1,
          title: 'Original',
          start: start.toISOString(),
          end: end.toISOString(),
          guideId: null,
        },
      ]
      store.duplicateEvent('orig')
      expect(store.events).toHaveLength(2)
      const clone = store.events[1]
      expect(clone.title).toBe('Original (Copy)')
      expect(new Date(clone.start).getHours()).toBe(11)
    })

    it('does nothing for non-existent event', () => {
      store.events = []
      store.duplicateEvent('nope')
      expect(store.events).toHaveLength(0)
    })
  })

  describe('moveEvent', () => {
    it('moves event to a new start time preserving duration', () => {
      const start = new Date(2026, 0, 10, 10, 0)
      const end = new Date(2026, 0, 10, 11, 0)
      store.events = [
        { id: 'm1', start: start.toISOString(), end: end.toISOString(), guideId: null },
      ]
      store.moveEvent('m1', new Date(2026, 0, 10, 14, 0))
      const moved = store.events.find((e) => e.id === 'm1')
      expect(new Date(moved.start).getHours()).toBe(14)
      expect(new Date(moved.end).getHours()).toBe(15)
    })

    it('does nothing for non-existent event', () => {
      store.events = []
      store.moveEvent('nope', new Date())
      expect(store.events).toHaveLength(0)
    })
  })

  describe('resizeEventDuration', () => {
    it('extends the event end time', () => {
      const start = new Date(2026, 0, 10, 10, 0)
      const end = new Date(2026, 0, 10, 11, 0)
      store.events = [
        { id: 'r1', start: start.toISOString(), end: end.toISOString(), guideId: null },
      ]
      store.resizeEventDuration('r1', 30)
      const resized = store.events.find((e) => e.id === 'r1')
      expect(new Date(resized.end).getMinutes()).toBe(30)
    })

    it('does not shrink past the start', () => {
      const start = new Date(2026, 0, 10, 10, 0)
      const end = new Date(2026, 0, 10, 10, 30)
      store.events = [
        { id: 'r1', start: start.toISOString(), end: end.toISOString(), guideId: null },
      ]
      store.resizeEventDuration('r1', -60)
      const unchanged = store.events.find((e) => e.id === 'r1')
      expect(new Date(unchanged.end).getMinutes()).toBe(30)
    })

    it('does nothing for non-existent event', () => {
      store.events = []
      store.resizeEventDuration('nope', 30)
      expect(store.events).toHaveLength(0)
    })
  })

  describe('navigate week', () => {
    it('moves forward by 7 days in week view', () => {
      store.setView('week')
      store.setDate(new Date(2026, 0, 10))
      store.navigate(1)
      expect(new Date(store.selectedDate).getDate()).toBe(17)
    })
  })

  describe('updateEvent', () => {
    it('replaces the event and selects it', () => {
      store.events = [{ id: 'u1', title: 'Old', guideId: null, start: '', end: '' }]
      store.updateEvent({ id: 'u1', title: 'New', guideId: null, start: '', end: '' })
      expect(store.events[0].title).toBe('New')
      expect(store.selectedEvent.title).toBe('New')
    })
  })

  describe('loadEvents edge cases', () => {
    it('handles non-array API response', async () => {
      getSchedules.mockResolvedValue(null)
      await store.loadEvents()
      expect(store.events).toEqual([])
      expect(store.loading).toBe(false)
    })

    it('normalizes schedule without event_end_datetime', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 2,
          tour_id: 10,
          tour_name: 'Reef Walk',
          event_start_datetime: '2026-03-10T10:00:00',
          status: 'CONFIRMED',
          language_code: 'pt',
        },
      ])
      await store.loadEvents()
      expect(store.events).toHaveLength(1)
      expect(store.events[0].language).toBe('Portuguese')
      expect(store.events[0].durationMinutes).toBe(60)
    })

    it('normalizes schedule with end before start (uses fallback)', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 3,
          tour_id: 10,
          event_start_datetime: '2026-03-10T12:00:00',
          event_end_datetime: '2026-03-10T10:00:00',
          status: 'CONFIRMED',
          language_code: 'es',
        },
      ])
      await store.loadEvents()
      expect(store.events[0].durationMinutes).toBe(60)
    })

    it('normalizes schedule with missing guide and tour name', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 4,
          tour_id: 5,
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          status: 'CONFIRMED',
        },
      ])
      await store.loadEvents()
      expect(store.events[0].resourceName).toBe('Unassigned Guide')
      expect(store.events[0].title).toContain('Tour')
    })

    it('normalizes schedule with null id falls back to generated id', async () => {
      getSchedules.mockResolvedValue([
        {
          tour_id: 10,
          tour_name: 'Test',
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          status: 'CONFIRMED',
          language_code: 'fr',
        },
      ])
      await store.loadEvents()
      expect(store.events[0].id).toMatch(/^schedule-/)
      expect(store.events[0].language).toBe('French')
    })

    it('normalizes schedule with unknown language code', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 5,
          tour_id: 10,
          tour_name: 'Test',
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          language_code: 'de',
        },
      ])
      await store.loadEvents()
      expect(store.events[0].language).toBe('de')
    })

    it('normalizes schedule with null language code', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 6,
          tour_id: 10,
          tour_name: 'Test',
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          language_code: null,
        },
      ])
      await store.loadEvents()
      expect(store.events[0].language).toBe('English')
    })

    it('normalizes schedule with reservation_count', async () => {
      getSchedules.mockResolvedValue([
        {
          id: 7,
          tour_id: 10,
          tour_name: 'Test',
          event_start_datetime: '2026-03-10T10:00:00',
          event_end_datetime: '2026-03-10T11:00:00',
          reservation_count: 5,
          language_code: 'zh',
        },
      ])
      await store.loadEvents()
      expect(store.events[0].notes).toContain('5')
      expect(store.events[0].reservationCount).toBe(5)
      expect(store.events[0].language).toBe('Chinese')
    })
  })

  describe('saveSelectedEvent', () => {
    it('does nothing when no event is selected', async () => {
      store.selectedEvent = null
      await store.saveSelectedEvent()
      expect(store.events).toEqual([])
    })
  })

  describe('filteredEvents edge cases', () => {
    it('filters by conflictsOnly', () => {
      store.events = [
        {
          id: 'c1',
          title: 'Event',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'G',
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
      ]
      store.conflicts = {}
      store.setFilters({ conflictsOnly: true })
      expect(store.filteredEvents).toHaveLength(0)
    })

    it('returns events that are in conflicts', () => {
      store.events = [
        {
          id: 'c1',
          title: 'Event',
          type: 'tour',
          status: 'confirmed',
          notes: '',
          resourceName: 'G',
          start: new Date(2026, 0, 10, 10, 0).toISOString(),
          end: new Date(2026, 0, 10, 11, 0).toISOString(),
        },
      ]
      store.conflicts = { c1: { conflictWith: ['c2'] } }
      store.setFilters({ conflictsOnly: true })
      expect(store.filteredEvents).toHaveLength(1)
    })
  })

  describe('selectedDateObj getter', () => {
    it('returns a Date object from selectedDate', () => {
      store.setDate(new Date(2026, 5, 1))
      expect(store.selectedDateObj).toBeInstanceOf(Date)
      expect(store.selectedDateObj.getMonth()).toBe(5)
    })
  })
})
