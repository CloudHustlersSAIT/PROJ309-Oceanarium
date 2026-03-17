<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import CalendarToolbar from '../components/calendar/CalendarToolbar.vue'
import CalendarGrid from '../components/calendar/CalendarGrid.vue'
import CancelButton from '../components/CancelButton.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import ManualAssignPopup from '../components/ManualAssignPopup.vue'
import SaveButton from '../components/SaveButton.vue'
import { useCalendarStore } from '../stores/calendar'
import { autoAssignGuide, cancelGuideFromSchedule, createSchedule, getTours } from '../services/api'
import { downloadCsv } from '../utils/calendar'
import { formatLocalTimeLowerAmPm } from '../utils/reservation'

const calendar = useCalendarStore()
const showCreatePopup = ref(false)
const showConfirmCreatePopup = ref(false)
const showConfirmCancelGuidePopup = ref(false)
const showTourDetailsPopup = ref(false)
const showDayEventsPopup = ref(false)
const formError = ref('')
const createDraftSnapshot = ref('')
const creatingSchedule = ref(false)
const toursLoading = ref(false)
const toursError = ref('')
const availableTours = ref([])
const assignmentNotice = ref({ type: '', lines: [] })
const showManualAssignPopup = ref(false)
const cancellingGuideAssignment = ref(false)
const autoAssignWeekLoading = ref(false)

const LANGUAGE_CODE_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
  { code: 'zh', label: 'Chinese' },
]

const createForm = ref({
  tourId: '',
  languageCode: 'en',
  eventDate: '',
  startTime: '10:00',
  endTime: '11:00',
})

const selectedCreateTour = computed(() => {
  const selectedId = Number(createForm.value.tourId)
  if (!Number.isInteger(selectedId) || selectedId <= 0) return null
  return availableTours.value.find((tour) => Number(tour?.id) === selectedId) || null
})

const canSaveCreatedEvent = computed(
  () =>
    Boolean(createForm.value.tourId) &&
    Boolean(createForm.value.languageCode) &&
    Boolean(createForm.value.eventDate) &&
    Boolean(createForm.value.startTime) &&
    Boolean(createForm.value.endTime),
)

const selectedDate = computed(() => new Date(calendar.selectedDate))
const monthLabel = computed(() =>
  selectedDate.value.toLocaleDateString('en-CA', { month: 'long', year: 'numeric' }),
)

const selectedDayLabel = computed(() =>
  selectedDate.value.toLocaleDateString('en-CA', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }),
)

const selectedDayEvents = computed(() => {
  const year = selectedDate.value.getFullYear()
  const month = selectedDate.value.getMonth()
  const day = selectedDate.value.getDate()

  return calendar.events
    .filter((event) => {
      const start = new Date(event.start)
      return start.getFullYear() === year && start.getMonth() === month && start.getDate() === day
    })
    .sort((a, b) => new Date(a.start) - new Date(b.start))
})

const selectedTourDetails = computed(() => {
  const selected = calendar.selectedEvent
  if (!selected) return null
  if (!isDetailsPopupAllowedSource(selected.source)) return null

  const start = new Date(selected.start)
  const end = new Date(selected.end)
  const hasValidStart = !Number.isNaN(start.getTime())
  const hasValidEnd = !Number.isNaN(end.getTime())
  const status = String(selected.status || '-').trim()

  return {
    source: selected.source,
    schedule_id: selected.sourceId ?? '-',
    status,
    tour_id: selected.tourId ?? '-',
    tour_title: selected.title || '-',
    language: selected.language || 'English',
    reservation_count: selected.reservationCount ?? '-',
    guide_id: selected.guideId ?? '-',
    guide_name: selected.resourceName || 'Unassigned Guide',
    date: hasValidStart ? start.toLocaleDateString('en-CA') : '-',
    time_range:
      hasValidStart && hasValidEnd
        ? `${formatLocalTimeLowerAmPm(start)} - ${formatLocalTimeLowerAmPm(end)}`
        : '-',
  }
})

const isSelectedStatusCancelled = computed(() => {
  const status = String(selectedTourDetails.value?.status || '')
    .trim()
    .toLowerCase()
  return status === 'cancelled' || status === 'canceled'
})

const selectedWeekScheduleEvents = computed(() =>
  calendar.eventsInRange.filter((event) => {
    if (String(event.source || '').toLowerCase() !== 'schedule') return false
    const status = String(event.status || '')
      .trim()
      .toLowerCase()
    return status === 'unassigned' || status === 'unassignable'
  }),
)

const selectedScheduleId = computed(() => {
  const selected = calendar.selectedEvent
  if (!selected) return null
  if (String(selected.source || '').toLowerCase() !== 'schedule') return null

  const scheduleId = Number(selected.sourceId)
  if (!Number.isInteger(scheduleId) || scheduleId <= 0) return null
  return scheduleId
})

const selectedDeletableEventIds = computed(() =>
  calendar.bulkSelection.filter((eventId) => {
    const selectedEvent = calendar.events.find((event) => event.id === eventId)
    return Boolean(selectedEvent) && selectedEvent.sourceId == null
  }),
)

function getCreateDraftSnapshot() {
  return JSON.stringify({
    form: createForm.value,
  })
}

function isDetailsPopupAllowedSource(source) {
  const normalized = String(source || '').toLowerCase()
  return normalized === 'booking' || normalized === 'manual' || normalized === 'schedule'
}

function getSelectedDateIso() {
  const selected = new Date(calendar.selectedDate)
  return `${selected.getFullYear()}-${String(selected.getMonth() + 1).padStart(2, '0')}-${String(selected.getDate()).padStart(2, '0')}`
}

function buildTourOptionLabel(tour) {
  const name = String(tour?.name || '').trim()
  return name ? `${tour.id} - ${name}` : `${tour.id}`
}

function toIsoDateTime(dateText, timeText) {
  return new Date(`${dateText}T${timeText}:00`).toISOString()
}

async function loadCreateTours() {
  toursLoading.value = true
  toursError.value = ''

  try {
    const tours = await getTours()
    const nextTours = (Array.isArray(tours) ? tours : [])
      .filter((tour) => Number.isInteger(Number(tour?.id)) && Number(tour.id) > 0)
      .sort((a, b) => Number(a.id) - Number(b.id))

    availableTours.value = nextTours

    const selectedId = Number(createForm.value.tourId)
    if (!nextTours.some((tour) => Number(tour?.id) === selectedId)) {
      createForm.value.tourId = nextTours.length === 1 ? String(nextTours[0]?.id) : ''
    }
  } catch (err) {
    availableTours.value = []
    createForm.value.tourId = ''
    toursError.value = err?.message || 'Failed to load tours.'
  } finally {
    toursLoading.value = false
  }
}

function hasUnsavedCreateDraft() {
  return showCreatePopup.value && createDraftSnapshot.value !== getCreateDraftSnapshot()
}

function handleCreateEvent() {
  const selectedDateIso = getSelectedDateIso()
  createForm.value = {
    tourId: '',
    languageCode: 'en',
    eventDate: selectedDateIso,
    startTime: '10:00',
    endTime: '11:00',
  }
  formError.value = ''
  toursError.value = ''
  createDraftSnapshot.value = getCreateDraftSnapshot()
  showCreatePopup.value = true
  loadCreateTours()
}

function handlePrimaryCreateClick() {
  handleCreateEvent()
}

function handleSelectEvent(event) {
  assignmentNotice.value = { type: '', lines: [] }
  calendar.selectEvent(event)
  if (!isDetailsPopupAllowedSource(event?.source)) {
    showTourDetailsPopup.value = false
    return
  }
  showTourDetailsPopup.value = true
}

function closeTourDetailsPopup() {
  showTourDetailsPopup.value = false
}

function setAssignmentNotice(type, lines) {
  assignmentNotice.value = {
    type,
    lines: Array.isArray(lines) ? lines.filter(Boolean).map((line) => String(line)) : [],
  }
}

function formatReasonCode(reasonCode) {
  const normalized = String(reasonCode || '').trim()
  if (!normalized) return 'No reason provided'
  return normalized
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

async function refreshCalendarSelection(scheduleId) {
  await calendar.loadEvents()

  const refreshed = calendar.events.find(
    (event) =>
      String(event.source || '').toLowerCase() === 'schedule' &&
      Number(event.sourceId) === scheduleId,
  )

  if (refreshed) {
    calendar.selectEvent(refreshed)
    showTourDetailsPopup.value = true
    return
  }

  calendar.selectEvent(null)
  showTourDetailsPopup.value = false
}

async function handleManualAssignSuccess({ scheduleId, guideId, guideName, warnings }) {
  showManualAssignPopup.value = false

  const warningLines = Array.isArray(warnings)
    ? warnings.map((warning) => `Warning: ${warning}`)
    : []

  setAssignmentNotice('success', [
    `Guide assigned manually: ${guideName} (ID ${guideId}).`,
    ...warningLines,
  ])

  await refreshCalendarSelection(scheduleId)
}

function requestCancelGuideAssignment() {
  if (cancellingGuideAssignment.value) return

  if (!selectedScheduleId.value) {
    setAssignmentNotice('error', ['Select a schedule event before cancelling guide assignment.'])
    return
  }

  showConfirmCancelGuidePopup.value = true
}

async function handleCancelGuideAssignment() {
  showConfirmCancelGuidePopup.value = false

  if (cancellingGuideAssignment.value) return
  const scheduleId = selectedScheduleId.value
  if (!scheduleId) {
    setAssignmentNotice('error', ['Select a schedule event before cancelling guide assignment.'])
    return
  }

  cancellingGuideAssignment.value = true

  try {
    const result = await cancelGuideFromSchedule(scheduleId)

    if (String(result?.status || '').toUpperCase() === 'UNASSIGNABLE') {
      const reasonLines = Array.isArray(result?.reasons)
        ? result.reasons.map((reason) => `Reason: ${formatReasonCode(reason)}`)
        : []

      setAssignmentNotice('warning', [
        `Guide removed from schedule ${result.schedule_id}. No replacement was found.`,
        ...reasonLines,
      ])
    } else {
      setAssignmentNotice('success', [
        `Guide cancellation processed for schedule ${result.schedule_id}.`,
        result.new_guide_id
          ? `Replacement guide: ${result.new_guide_name} (ID ${result.new_guide_id}).`
          : 'Guide was unassigned successfully.',
      ])
    }

    await refreshCalendarSelection(scheduleId)
  } catch (error) {
    setAssignmentNotice('error', [error?.message || 'Failed to cancel guide assignment.'])
  } finally {
    cancellingGuideAssignment.value = false
  }
}

async function handleAutoAssignWeek() {
  if (autoAssignWeekLoading.value) return
  if (calendar.currentView !== 'week') {
    setAssignmentNotice('warning', ['Switch to week view to run Auto Assign for the current week.'])
    return
  }

  const weekEvents = selectedWeekScheduleEvents.value
  if (weekEvents.length === 0) {
    setAssignmentNotice('warning', ['No unassigned schedule events found in the selected week.'])
    return
  }

  autoAssignWeekLoading.value = true
  assignmentNotice.value = { type: '', lines: [] }

  try {
    const results = await Promise.allSettled(
      weekEvents.map((event) => autoAssignGuide(Number(event.sourceId))),
    )

    const successCount = results.filter((result) => result.status === 'fulfilled').length
    const failed = results.filter((result) => result.status === 'rejected')

    if (failed.length > 0) {
      const firstError = failed[0].reason?.message || 'Unknown assignment error'
      setAssignmentNotice('warning', [
        `Auto Assign processed ${successCount} of ${weekEvents.length} schedule events.`,
        `Some assignments failed: ${firstError}`,
      ])
    } else {
      setAssignmentNotice('success', [
        `Auto Assign completed for ${successCount} schedule events in the current week.`,
      ])
    }

    try {
      await calendar.loadEvents()
    } catch (error) {
      setAssignmentNotice('warning', [
        ...assignmentNotice.value.lines,
        error?.message || 'Calendar refresh failed after Auto Assign.',
      ])
    }
  } finally {
    autoAssignWeekLoading.value = false
  }
}

function reservationDetailsStatusClass(status) {
  const normalized = String(status || '')
    .trim()
    .toLowerCase()
  if (normalized === 'confirmed') {
    return 'border-green-300 bg-green-50 text-green-800 dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300'
  }
  if (normalized === 'canceled' || normalized === 'cancelled') {
    return 'border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
  }
  return 'border-[#ACBAC4] bg-white text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300'
}

function closeDayEventsPopup() {
  showDayEventsPopup.value = false
}

function closeCreatePopup() {
  if (hasUnsavedCreateDraft()) {
    const confirmed = window.confirm('Discard unsaved changes?')
    if (!confirmed) return
  }

  formError.value = ''
  createDraftSnapshot.value = ''
  showConfirmCreatePopup.value = false
  showCreatePopup.value = false
}

function requestCreateConfirmation() {
  if (creatingSchedule.value || !canSaveCreatedEvent.value) return
  showConfirmCreatePopup.value = true
}

function handleGlobalKeydown(event) {
  if (event.key !== 'Escape') return
  if (showDayEventsPopup.value) {
    event.preventDefault()
    closeDayEventsPopup()
    return
  }
  if (showTourDetailsPopup.value) {
    event.preventDefault()
    closeTourDetailsPopup()
    return
  }
  if (!showCreatePopup.value) return
  event.preventDefault()
  closeCreatePopup()
}

function saveCreatedEvent() {
  showConfirmCreatePopup.value = false
  formError.value = ''

  const tourId = Number(createForm.value.tourId)
  const languageCode = String(createForm.value.languageCode || '')
    .trim()
    .toLowerCase()
  const eventDate = String(createForm.value.eventDate || '').trim()
  const startTime = String(createForm.value.startTime || '').trim()
  const endTime = String(createForm.value.endTime || '').trim()

  if (!Number.isInteger(tourId) || tourId <= 0) {
    formError.value = 'Tour is required.'
    return
  }

  if (!/^[a-z]{2}$/.test(languageCode)) {
    formError.value = 'Language code must have 2 letters (e.g., en, pt).'
    return
  }

  if (!eventDate || !startTime || !endTime) {
    formError.value = 'Date, Start time, and End time are required.'
    return
  }

  const startIso = toIsoDateTime(eventDate, startTime)
  const endIso = toIsoDateTime(eventDate, endTime)
  if (Number.isNaN(new Date(startIso).getTime()) || Number.isNaN(new Date(endIso).getTime())) {
    formError.value = 'Date/time values are invalid.'
    return
  }

  if (new Date(endIso) <= new Date(startIso)) {
    formError.value = 'End time must be after Start time.'
    return
  }

  creatingSchedule.value = true

  createSchedule({
    tour_id: tourId,
    language_code: languageCode,
    event_start_datetime: startIso,
    event_end_datetime: endIso,
  })
    .then(async () => {
      await Promise.all([calendar.loadEvents(), loadCreateTours()])
      calendar.setDate(new Date(startIso))
      formError.value = ''
      createDraftSnapshot.value = ''
      showCreatePopup.value = false
    })
    .catch((error) => {
      formError.value = error?.message || 'Failed to create reservation.'
    })
    .finally(() => {
      creatingSchedule.value = false
    })
}

function exportVisibleEvents() {
  const selected = new Date(calendar.selectedDate)
  const yyyy = selected.getFullYear()
  const mm = String(selected.getMonth() + 1).padStart(2, '0')
  const dd = String(selected.getDate()).padStart(2, '0')

  downloadCsv({
    filename: `calendar-export-${yyyy}-${mm}-${dd}.csv`,
    headers: ['Title', 'Type', 'Status', 'Start', 'End', 'Resource', 'Notes'],
    rows: calendar.eventsInRange.map((event) => [
      event.title,
      event.type,
      event.status,
      event.start,
      event.end,
      event.resourceName,
      event.notes,
    ]),
  })
}

function handleSelectDate(date) {
  calendar.setDate(date)
}

function handleOpenDayEvents(date) {
  calendar.setDate(date)
  showDayEventsPopup.value = true
}

function handleNavigateNext() {
  calendar.navigate(1)
}

function handleNavigatePrev() {
  calendar.navigate(-1)
}

function handleDeleteSelectedEvent() {
  if (!calendar.bulkSelection.length) return

  if (selectedDeletableEventIds.value.length === 0) {
    setAssignmentNotice('warning', [
      'Delete selected is available only for local events that have not been persisted yet.',
    ])
    return
  }

  const confirmed = window.confirm(
    `Delete ${selectedDeletableEventIds.value.length} selected event(s)?`,
  )
  if (!confirmed) return

  const selectedIds = [...selectedDeletableEventIds.value]
  selectedIds.forEach((eventId) => calendar.deleteEvent(eventId))

  if (selectedIds.length !== calendar.bulkSelection.length) {
    setAssignmentNotice('warning', [
      'Only local non-persisted events were removed. Persisted schedule events were kept unchanged.',
    ])
  }
}

watch(
  () => calendar.selectedDate,
  () => {
    if (!showCreatePopup.value) return
    createForm.value.eventDate = getSelectedDateIso()
  },
)

onMounted(() => {
  calendar.setView('week')
  calendar.loadEvents()
  document.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="flex min-h-screen overflow-x-hidden bg-gray-50 dark:bg-[#0F1117]">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-3 md:p-4 xl:p-6">
      <div class="space-y-4">
        <CalendarToolbar
          :current-view="calendar.currentView"
          :selected-date="selectedDate"
          @change-view="calendar.setView"
          @primary-create="handlePrimaryCreateClick"
          @export="exportVisibleEvents"
        />

        <div
          class="flex flex-col gap-3 rounded-xl border border-blue-500 bg-white p-3 shadow-md dark:border-sky-700/40 dark:bg-[#161B27] dark:shadow-black/30 md:flex-row md:items-center md:justify-between"
        >
          <div class="text-sm text-gray-600 dark:text-slate-400">
            {{
              calendar.loading
                ? 'Loading tours...'
                : `${calendar.eventsInRange.length} tours in range`
            }}
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <button
              :disabled="calendar.bulkSelection.length === 0"
              class="px-3 py-1.5 rounded bg-red-600 text-white text-sm"
              @click="handleDeleteSelectedEvent"
            >
              Delete selected
            </button>
            <button
              class="rounded border border-gray-300 px-3 py-1.5 text-sm dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300"
              :disabled="calendar.bulkSelection.length === 0"
              @click="calendar.clearBulkSelection()"
            >
              Clear
            </button>
          </div>
        </div>

        <CalendarGrid
          :view="calendar.currentView"
          :selected-date="selectedDate"
          :events="calendar.eventsInRange"
          :selected-event="calendar.selectedEvent"
          :conflicts="calendar.conflicts"
          :resources="calendar.resources"
          :bulk-selection="calendar.bulkSelection"
          :auto-assign-loading="autoAssignWeekLoading"
          @select-event="handleSelectEvent"
          @toggle-bulk="calendar.toggleBulkSelection"
          @select-date="handleSelectDate"
          @open-day-events="handleOpenDayEvents"
          @navigate-next="handleNavigateNext"
          @navigate-prev="handleNavigatePrev"
          @auto-assign-week="handleAutoAssignWeek"
        />

        <div
          v-if="assignmentNotice.lines.length > 0"
          class="rounded border px-3 py-2 text-sm"
          :class="
            assignmentNotice.type === 'error'
              ? 'border-red-300 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
              : assignmentNotice.type === 'warning'
                ? 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
                : 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300'
          "
        >
          <p v-for="line in assignmentNotice.lines" :key="line">{{ line }}</p>
        </div>
      </div>
    </main>

    <div
      v-if="showDayEventsPopup"
      class="fixed inset-0 z-50 bg-black/40"
      @click.self="closeDayEventsPopup"
    >
      <div
        class="absolute left-1/2 top-1/2 w-[94%] max-w-160 -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[#ACBAC4] bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-slate-100">
            Events on {{ selectedDayLabel }}
          </h3>
          <button
            class="text-xl leading-none text-red-300 hover:text-red-500 dark:text-slate-500 dark:hover:text-slate-200"
            aria-label="Close day events popup"
            @click="closeDayEventsPopup"
          >
            ×
          </button>
        </div>

        <div
          v-if="selectedDayEvents.length === 0"
          class="rounded border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-sm text-gray-600 dark:border-white/15 dark:bg-[#1A2231] dark:text-slate-400"
        >
          No events scheduled for this date.
        </div>

        <ul v-else class="max-h-105 overflow-y-auto space-y-2 pr-1">
          <li
            v-for="event in selectedDayEvents"
            :key="event.id"
            class="rounded border border-[#ACBAC4] px-3 py-2 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:hover:bg-white/5"
          >
            <button class="w-full text-left" @click="handleSelectEvent(event)">
              <div class="text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ event.title }}
              </div>
              <div class="mt-0.5 text-xs text-gray-600 dark:text-slate-400">
                {{ formatLocalTimeLowerAmPm(event.start) }}
                -
                {{ formatLocalTimeLowerAmPm(event.end) }}
              </div>
              <div class="mt-0.5 text-xs text-gray-500 dark:text-slate-500">
                {{ event.resourceName }}
              </div>
            </button>
          </li>
        </ul>

        <div class="mt-5 flex justify-end">
          <button
            class="rounded border border-red-200 bg-red-50 px-4 py-2 text-red-600 hover:bg-red-100 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300 dark:hover:bg-red-950/60"
            @click="closeDayEventsPopup"
          >
            Close
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showTourDetailsPopup && selectedTourDetails"
      class="fixed inset-0 z-50 bg-black/40"
      @click.self="closeTourDetailsPopup"
    >
      <div
        class="absolute left-1/2 top-1/2 w-[92%] max-w-130 -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[#ACBAC4] bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-slate-100">
            Reservation Details
          </h3>
          <button
            class="text-xl leading-none text-red-300 hover:text-red-500 dark:text-slate-500 dark:hover:text-slate-200"
            aria-label="Close tour details popup"
            @click="closeTourDetailsPopup"
          >
            ×
          </button>
        </div>

        <div class="space-y-4 text-sm text-gray-700 dark:text-slate-300">
          <div
            v-if="
              String(selectedTourDetails.status || '')
                .trim()
                .toLowerCase() !== 'unassignable'
            "
            class="rounded border px-2 py-1"
            :class="reservationDetailsStatusClass(selectedTourDetails.status)"
          >
            <span class="font-semibold">Status:</span> {{ selectedTourDetails.status }}
          </div>

          <div
            class="grid grid-cols-1 gap-3 rounded border border-[#ACBAC4] bg-gray-50 p-3 dark:border-white/10 dark:bg-[#1A2231] sm:grid-cols-2"
          >
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Schedule ID
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.schedule_id }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Tour ID
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.tour_id }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333] sm:col-span-2"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Tour
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.tour_title }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Date
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.date }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Time
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.time_range }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Language
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.language }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Total People
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.reservation_count }}
              </p>
            </div>
            <div
              class="rounded border border-[#D6DEE5] bg-white px-3 py-2 dark:border-white/10 dark:bg-[#1C2333] sm:col-span-2"
            >
              <p
                class="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
              >
                Guide
              </p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800 dark:text-slate-100">
                {{ selectedTourDetails.guide_name }}
              </p>
            </div>
          </div>
        </div>

        <div
          v-if="selectedScheduleId && !isSelectedStatusCancelled"
          class="mt-4 rounded border border-[#ACBAC4] bg-gray-50 p-3 dark:border-white/10 dark:bg-[#1A2231]"
        >
          <p
            class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
          >
            Guide Assignment
          </p>

          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-1">
            <button
              type="button"
              class="rounded border border-[#ACBAC4] bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
              :disabled="showManualAssignPopup || cancellingGuideAssignment"
              @click="showManualAssignPopup = true"
            >
              Manual Assign
            </button>

            <button
              type="button"
              class="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300 dark:hover:bg-red-950/60"
              :disabled="showManualAssignPopup || cancellingGuideAssignment"
              @click="requestCancelGuideAssignment"
            >
              {{ cancellingGuideAssignment ? 'Cancelling...' : 'Cancel Guide' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <ManualAssignPopup
      :schedule-id="selectedScheduleId"
      :visible="showManualAssignPopup"
      @close="showManualAssignPopup = false"
      @assigned="handleManualAssignSuccess"
    />

    <div
      v-if="showCreatePopup"
      class="fixed inset-0 z-50 bg-black/40"
      @click.self="closeCreatePopup"
    >
      <div
        class="absolute right-0 top-0 h-full w-full max-w-105 overflow-y-auto border-l border-[#ACBAC4] bg-white p-5 text-gray-700 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:text-slate-100"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="typo-modal-eyebrow">Create</div>
          <button
            class="text-xl leading-none text-gray-400 hover:text-gray-700 dark:text-slate-500 dark:hover:text-slate-100"
            aria-label="Close create popup"
            @click="closeCreatePopup"
          >
            ×
          </button>
        </div>

        <div
          v-if="formError"
          class="mt-3 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-400 dark:bg-red-500/10 dark:text-red-200"
        >
          {{ formError }}
        </div>

        <div class="mt-5 space-y-4 text-sm">
          <div
            class="space-y-3 rounded border border-[#ACBAC4] bg-gray-50 p-3 dark:border-white/10 dark:bg-[#1A2231]"
          >
            <div>
              <div class="mb-2 text-sm font-semibold text-gray-700 dark:text-slate-200">
                {{ monthLabel }}
              </div>
              <div class="flex gap-2">
                <button
                  class="flex-1 rounded border border-[#ACBAC4] bg-white px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-200 dark:hover:bg-white/5"
                  @click="calendar.navigate(-1)"
                >
                  Previous
                </button>
                <button
                  class="flex-1 rounded border border-[#ACBAC4] bg-white px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-200 dark:hover:bg-white/5"
                  @click="calendar.navigate(1)"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <div>
            <label class="mb-1 flex items-center gap-1 text-sm text-gray-600 dark:text-slate-300">
              <button
                type="button"
                class="inline-flex items-center rounded p-0.5 text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-300 dark:hover:bg-white/5"
                :disabled="toursLoading"
                aria-label="Refresh tours"
                title="Refresh tours"
                @click="loadCreateTours"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="h-4 w-4"
                  :class="{ 'animate-spin': toursLoading }"
                  aria-hidden="true"
                >
                  <path d="M21 2v6h-6" />
                  <path d="M3 12a9 9 0 0 1 15.3-6.3L21 8" />
                  <path d="M3 22v-6h6" />
                  <path d="M21 12a9 9 0 0 1-15.3 6.3L3 16" />
                </svg>
              </button>
              <span>Tour</span>
            </label>
            <select
              v-model="createForm.tourId"
              class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-sm text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
              :disabled="toursLoading || availableTours.length === 0"
            >
              <option value="">Select a tour</option>
              <option
                v-for="tour in availableTours"
                :key="`tour-${tour.id}`"
                :value="String(tour.id)"
              >
                {{ buildTourOptionLabel(tour) }}
              </option>
            </select>
            <p v-if="toursLoading" class="mt-1 text-xs text-gray-500 dark:text-slate-500">
              Loading tours...
            </p>
            <p v-else-if="toursError" class="mt-1 text-xs text-red-300">{{ toursError }}</p>
            <p v-else-if="!availableTours.length" class="mt-1 text-xs text-amber-300">
              No tours available.
            </p>
          </div>

          <div>
            <label class="mb-1 block text-gray-600 dark:text-slate-300">Language</label>
            <select
              v-model="createForm.languageCode"
              class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-sm text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
            >
              <option v-for="lang in LANGUAGE_CODE_OPTIONS" :key="lang.code" :value="lang.code">
                {{ lang.label }} ({{ lang.code }})
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-gray-600 dark:text-slate-300">Date</label>
            <input
              v-model="createForm.eventDate"
              type="date"
              class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block text-gray-600 dark:text-slate-300">Start Time</label>
              <input
                v-model="createForm.startTime"
                type="time"
                class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
              />
            </div>
            <div>
              <label class="mb-1 block text-gray-600 dark:text-slate-300">End Time</label>
              <input
                v-model="createForm.endTime"
                type="time"
                class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
              />
            </div>
          </div>

          <div
            v-if="selectedCreateTour"
            class="rounded border border-[#ACBAC4] bg-gray-50 px-3 py-2 text-xs text-gray-700 dark:border-white/10 dark:bg-[#1A2231] dark:text-slate-200"
          >
            <div>
              <span class="font-semibold">Tour:</span>
              {{ selectedCreateTour.name || `Tour ${selectedCreateTour.id}` }}
            </div>
            <div><span class="font-semibold">Language:</span> {{ createForm.languageCode }}</div>
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <CancelButton @cancel="closeCreatePopup" />
          <SaveButton
            :disabled="!canSaveCreatedEvent || creatingSchedule"
            :loading="creatingSchedule"
            @save="requestCreateConfirmation"
          />
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="showConfirmCreatePopup"
      title="Confirm creation"
      message="Do you want to proceed with creating this schedule?"
      :loading="creatingSchedule"
      :disabled="creatingSchedule"
      @cancel="showConfirmCreatePopup = false"
      @confirm="saveCreatedEvent"
    />

    <ConfirmDialog
      :open="showConfirmCancelGuidePopup"
      title="Confirm guide cancellation"
      message="Do you want to cancel the current guide assignment for this schedule?"
      :loading="cancellingGuideAssignment"
      :disabled="cancellingGuideAssignment"
      @cancel="showConfirmCancelGuidePopup = false"
      @confirm="handleCancelGuideAssignment"
    />
  </div>
</template>
