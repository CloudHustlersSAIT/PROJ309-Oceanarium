<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import CalendarToolbar from '../components/calendar/CalendarToolbar.vue'
import CalendarGrid from '../components/calendar/CalendarGrid.vue'
import CancelButton from '../components/CancelButton.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import SaveButton from '../components/SaveButton.vue'
import { useCalendarStore } from '../stores/calendar'
import {
  autoAssignGuide,
  cancelGuideFromSchedule,
  createSchedule,
  getEligibleGuides,
  getGuideLanguages,
  getTours,
  manualAssignGuide,
} from '../services/api'
import { downloadCsv } from '../utils/calendar'
import {
  formatLocalTimeLowerAmPm,
} from '../utils/reservation'

const calendar = useCalendarStore()
const showCreatePopup = ref(false)
const showConfirmCreatePopup = ref(false)
const showConfirmCancelGuidePopup = ref(false)
const manualAssignRequestToken = ref(0)
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
const manualAssignLoadingCandidates = ref(false)
const manualAssignSubmitting = ref(false)
const cancellingGuideAssignment = ref(false)
const eligibleGuides = ref([])
const eligibleGuideReasons = ref([])
const manualAssignGuideId = ref('')
const manualAssignReason = ref('')
const manualAssignError = ref('')
const guideLanguageCache = ref({})
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

const canSaveCreatedEvent = computed(() =>
  Boolean(createForm.value.tourId)
  && Boolean(createForm.value.languageCode)
  && Boolean(createForm.value.eventDate)
  && Boolean(createForm.value.startTime)
  && Boolean(createForm.value.endTime),
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
    time_range: hasValidStart && hasValidEnd
      ? `${formatLocalTimeLowerAmPm(start)} - ${formatLocalTimeLowerAmPm(end)}`
      : '-',
  }
})

const isSelectedStatusCancelled = computed(() => {
  const status = String(selectedTourDetails.value?.status || '').trim().toLowerCase()
  return status === 'cancelled' || status === 'canceled'
})

const selectedWeekScheduleEvents = computed(() =>
  calendar.eventsInRange.filter((event) => {
    if (String(event.source || '').toLowerCase() !== 'schedule') return false
    const status = String(event.status || '').trim().toLowerCase()
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

const canSubmitManualAssign = computed(() => {
  const guideId = Number(manualAssignGuideId.value)
  return Number.isInteger(guideId) && guideId > 0 && !manualAssignSubmitting.value
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
  manualAssignError.value = ''
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

function mapGuideLanguageResponse(response) {
  const languages = Array.isArray(response?.languages) ? response.languages : []
  const labels = languages
    .map((item) => String(item?.name || item?.code || '').trim())
    .filter(Boolean)

  return labels.length > 0 ? labels.join(', ') : 'Not mapped'
}

function withCachedGuideLanguages(guideRows) {
  const rows = Array.isArray(guideRows) ? guideRows : []
  return rows.map((guide) => {
    const guideId = Number(guide?.id)
    const cachedLanguage = guideLanguageCache.value[String(guideId)]
    return {
      ...guide,
      languageLabel: cachedLanguage || guide.languageLabel || 'Loading...',
    }
  })
}

async function enrichEligibleGuideLanguages(requestToken, scheduleId) {
  if (!showManualAssignPopup.value || eligibleGuides.value.length === 0) return
  if (manualAssignRequestToken.value !== requestToken) return
  if (selectedScheduleId.value !== scheduleId) return

  const uniqueGuideIds = Array.from(
    new Set(
      eligibleGuides.value
        .map((guide) => Number(guide?.id))
        .filter((guideId) => Number.isInteger(guideId) && guideId > 0),
    ),
  )

  const missingGuideIds = uniqueGuideIds.filter((guideId) => !guideLanguageCache.value[String(guideId)])

  if (missingGuideIds.length > 0) {
    const results = await Promise.allSettled(
      missingGuideIds.map((guideId) => getGuideLanguages(guideId)),
    )

    const nextCache = { ...guideLanguageCache.value }
    for (let index = 0; index < missingGuideIds.length; index += 1) {
      const guideId = missingGuideIds[index]
      const result = results[index]
      if (result.status === 'fulfilled') {
        nextCache[String(guideId)] = mapGuideLanguageResponse(result.value)
      } else {
        nextCache[String(guideId)] = 'Not mapped'
      }
    }

    guideLanguageCache.value = nextCache
  }

  if (!showManualAssignPopup.value) {
    return
  }

  if (manualAssignRequestToken.value !== requestToken) {
    return
  }

  if (selectedScheduleId.value !== scheduleId) {
    return
  }

  eligibleGuides.value = withCachedGuideLanguages(eligibleGuides.value)
}

async function refreshCalendarSelection(scheduleId) {
  await calendar.loadEvents()

  const refreshed = calendar.events.find(
    (event) => String(event.source || '').toLowerCase() === 'schedule' && Number(event.sourceId) === scheduleId,
  )

  if (refreshed) {
    calendar.selectEvent(refreshed)
    showTourDetailsPopup.value = true
    return
  }

  calendar.selectEvent(null)
  showTourDetailsPopup.value = false
}

function closeManualAssignPopup() {
  showManualAssignPopup.value = false
  manualAssignRequestToken.value += 1
  manualAssignGuideId.value = ''
  manualAssignReason.value = ''
  manualAssignError.value = ''
  eligibleGuides.value = []
  eligibleGuideReasons.value = []
}

async function openManualAssignPopup() {
  const scheduleId = selectedScheduleId.value
  if (!scheduleId) {
    setAssignmentNotice('error', ['Select a schedule event before manual assignment.'])
    return
  }

  const requestToken = manualAssignRequestToken.value + 1
  manualAssignRequestToken.value = requestToken

  showManualAssignPopup.value = true
  manualAssignGuideId.value = ''
  manualAssignReason.value = ''
  manualAssignError.value = ''
  eligibleGuides.value = []
  eligibleGuideReasons.value = []
  manualAssignLoadingCandidates.value = true

  try {
    const eligibleResponse = await getEligibleGuides(scheduleId)

    if (manualAssignRequestToken.value !== requestToken || !showManualAssignPopup.value) {
      return
    }

    if (selectedScheduleId.value !== scheduleId) {
      return
    }

    eligibleGuides.value = Array.isArray(eligibleResponse?.eligible_guides)
      ? eligibleResponse.eligible_guides.map((guide) => ({ ...guide, languageLabel: 'Loading...' }))
      : []

    eligibleGuideReasons.value = Array.isArray(eligibleResponse?.reasons) ? eligibleResponse.reasons : []

    if (eligibleGuides.value.length === 1) {
      manualAssignGuideId.value = String(eligibleGuides.value[0].id)
    }
  } catch (error) {
    if (manualAssignRequestToken.value === requestToken) {
      manualAssignError.value = error?.message || 'Failed to load eligible guides.'
    }
  } finally {
    if (manualAssignRequestToken.value === requestToken) {
      manualAssignLoadingCandidates.value = false
    }
  }

  // Language labels are enriched in background to avoid blocking modal rendering.
  void enrichEligibleGuideLanguages(requestToken, scheduleId)
}

async function submitManualAssign() {
  const scheduleId = selectedScheduleId.value
  if (!scheduleId) {
    manualAssignError.value = 'No schedule selected for manual assignment.'
    return
  }

  const guideId = Number(manualAssignGuideId.value)
  if (!Number.isInteger(guideId) || guideId <= 0) {
    manualAssignError.value = 'Select a guide before confirming manual assignment.'
    return
  }

  manualAssignSubmitting.value = true
  manualAssignError.value = ''

  try {
    const response = await manualAssignGuide(
      scheduleId,
      guideId,
      manualAssignReason.value,
    )

    const warningLines = Array.isArray(response?.warnings)
      ? response.warnings.filter(Boolean).map((warning) => `Warning: ${warning}`)
      : []

    setAssignmentNotice('success', [
      `Guide assigned manually: ${response.guide_name} (ID ${response.guide_id}).`,
      ...warningLines,
    ])

    closeManualAssignPopup()
    await refreshCalendarSelection(scheduleId)
  } catch (error) {
    manualAssignError.value = error?.message || 'Failed to assign selected guide manually.'
  } finally {
    manualAssignSubmitting.value = false
  }
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
    return 'border-green-300 bg-green-50 text-green-800'
  }
  if (normalized === 'canceled' || normalized === 'cancelled') {
    return 'border-red-300 bg-red-50 text-red-800'
  }
  return 'border-[#ACBAC4] bg-white text-gray-700'
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
  if (showManualAssignPopup.value) {
    event.preventDefault()
    closeManualAssignPopup()
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
  const languageCode = String(createForm.value.languageCode || '').trim().toLowerCase()
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

  const confirmed = window.confirm(`Delete ${selectedDeletableEventIds.value.length} selected event(s)?`)
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
  <div class="flex min-h-screen bg-gray-50 overflow-x-hidden">
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
          class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between bg-white rounded-xl shadow-md p-3 border border-blue-500"
        >
          <div class="text-sm text-gray-600">
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
              class="px-3 py-1.5 rounded border border-gray-300 text-sm"
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
              ? 'border-red-300 bg-red-50 text-red-700'
              : assignmentNotice.type === 'warning'
                ? 'border-amber-300 bg-amber-50 text-amber-800'
                : 'border-emerald-300 bg-emerald-50 text-emerald-700'
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
        class="absolute left-1/2 top-1/2 w-[94%] max-w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-5 shadow-2xl border border-[#ACBAC4]"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">Events on {{ selectedDayLabel }}</h3>
          <button
            class="text-red-300 hover:text-red-500 text-xl leading-none"
            aria-label="Close day events popup"
            @click="closeDayEventsPopup"
          >
            ×
          </button>
        </div>

        <div
          v-if="selectedDayEvents.length === 0"
          class="rounded border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-sm text-gray-600"
        >
          No events scheduled for this date.
        </div>

        <ul v-else class="max-h-[420px] overflow-y-auto space-y-2 pr-1">
          <li
            v-for="event in selectedDayEvents"
            :key="event.id"
            class="rounded border border-[#ACBAC4] px-3 py-2 hover:bg-gray-50"
          >
            <button class="w-full text-left" @click="handleSelectEvent(event)">
              <div class="text-sm font-semibold text-gray-800">{{ event.title }}</div>
              <div class="text-xs text-gray-600 mt-0.5">
                {{ formatLocalTimeLowerAmPm(event.start) }}
                -
                {{ formatLocalTimeLowerAmPm(event.end) }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">{{ event.resourceName }}</div>
            </button>
          </li>
        </ul>

        <div class="mt-5 flex justify-end">
          <button
            class="px-4 py-2 rounded border border-red-200 bg-red-50 text-red-600 hover:bg-red-100"
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
        class="absolute left-1/2 top-1/2 w-[92%] max-w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-xl p-5 shadow-2xl border border-[#ACBAC4] bg-white"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">Reservation Details</h3>
          <button
            class="text-red-300 hover:text-red-500 text-xl leading-none"
            aria-label="Close tour details popup"
            @click="closeTourDetailsPopup"
          >
            ×
          </button>
        </div>

        <div class="space-y-4 text-sm text-gray-700">
          <div
            v-if="String(selectedTourDetails.status || '').trim().toLowerCase() !== 'unassignable'"
            class="rounded border px-2 py-1"
            :class="reservationDetailsStatusClass(selectedTourDetails.status)"
          >
            <span class="font-semibold">Status:</span> {{ selectedTourDetails.status }}
          </div>

          <div class="grid grid-cols-1 gap-3 rounded border border-[#ACBAC4] bg-gray-50 p-3 sm:grid-cols-2">
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Schedule ID</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.schedule_id }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Tour ID</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.tour_id }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2 sm:col-span-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Tour</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.tour_title }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Date</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.date }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Time</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.time_range }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Language</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.language }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Total People</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.reservation_count }}</p>
            </div>
            <div class="rounded border border-[#D6DEE5] bg-white px-3 py-2 sm:col-span-2">
              <p class="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Guide</p>
              <p class="mt-0.5 text-sm font-semibold text-gray-800">{{ selectedTourDetails.guide_name }}</p>
            </div>
          </div>
        </div>

        <div v-if="selectedScheduleId && !isSelectedStatusCancelled" class="mt-4 rounded border border-[#ACBAC4] bg-gray-50 p-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-gray-500">Guide Assignment</p>

          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-1">
            <button
              type="button"
              class="rounded border border-[#ACBAC4] bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="manualAssignSubmitting || cancellingGuideAssignment"
              @click="openManualAssignPopup"
            >
              Manual Assign
            </button>

            <button
              type="button"
              class="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="manualAssignSubmitting || cancellingGuideAssignment"
              @click="requestCancelGuideAssignment"
            >
              {{ cancellingGuideAssignment ? 'Cancelling...' : 'Cancel Guide' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showManualAssignPopup"
      class="fixed inset-0 z-50 bg-black/40"
      @click.self="closeManualAssignPopup"
    >
      <div
        class="absolute left-1/2 top-1/2 w-[92%] max-w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[#ACBAC4] bg-white p-5 shadow-2xl"
      >
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-lg font-semibold text-gray-800">Manual Assign Guide</h3>
          <button
            type="button"
            class="text-red-300 hover:text-red-500 text-xl leading-none"
            aria-label="Close manual assign popup"
            @click="closeManualAssignPopup"
          >
            ×
          </button>
        </div>

        <p class="mt-1 text-xs text-gray-500">Schedule ID: {{ selectedScheduleId }}</p>

        <div
          v-if="manualAssignError"
          class="mt-3 rounded border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700"
        >
          {{ manualAssignError }}
        </div>

        <div v-if="manualAssignLoadingCandidates" class="mt-4 text-sm text-gray-600">
          Loading eligible guides...
        </div>

        <div v-else class="mt-4 space-y-3">
          <div
            v-if="eligibleGuideReasons.length > 0"
            class="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800"
          >
            <p class="font-semibold">No fully eligible guides found.</p>
            <p v-for="reason in eligibleGuideReasons" :key="reason">Reason: {{ formatReasonCode(reason) }}</p>
          </div>

          <div class="max-h-56 space-y-2 overflow-y-auto pr-1">
            <label
              v-for="guide in eligibleGuides"
              :key="guide.id"
              class="flex cursor-pointer items-start gap-3 rounded border border-[#ACBAC4] px-3 py-2 hover:bg-gray-50"
            >
              <input
                v-model="manualAssignGuideId"
                type="radio"
                name="manual-assign-guide"
                :value="String(guide.id)"
                class="mt-0.5"
              />
              <div class="text-sm text-gray-700">
                <p class="font-semibold">{{ guide.first_name }} {{ guide.last_name }} (ID {{ guide.id }})</p>
                <p class="text-xs text-gray-500">
                  Rating: {{ guide.guide_rating ?? 'N/A' }} · Same-day assignments: {{ guide.same_day_assignments }} · Languages: {{ guide.languageLabel }}
                </p>
              </div>
            </label>
            <p v-if="eligibleGuides.length === 0" class="text-sm text-gray-600">
              No eligible guide candidates returned by backend preview.
            </p>
          </div>

          <div>
            <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">Reason (optional)</label>
            <textarea
              v-model="manualAssignReason"
              rows="3"
              class="w-full rounded border border-[#ACBAC4] px-3 py-2 text-sm text-gray-700"
              placeholder="Example: Customer requested specific guide"
            />
          </div>
        </div>

        <div class="mt-5 flex items-center justify-end gap-2">
          <CancelButton @cancel="closeManualAssignPopup" />
          <SaveButton
            label="Assign"
            loading-label="Assigning..."
            :loading="manualAssignSubmitting"
            :disabled="!canSubmitManualAssign"
            @save="submitManualAssign"
          />
        </div>
      </div>
    </div>

    <div
      v-if="showCreatePopup"
      class="fixed inset-0 z-50 bg-black/40"
      @click.self="closeCreatePopup"
    >
      <div
        class="absolute right-0 top-0 h-full w-full max-w-[420px] bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="typo-modal-eyebrow">Create</div>
          <button
            class="text-gray-300 hover:text-white text-xl leading-none"
            aria-label="Close create popup"
            @click="closeCreatePopup"
          >
            ×
          </button>
        </div>

        <div
          v-if="formError"
          class="mt-3 rounded border border-red-400 bg-red-500/10 px-3 py-2 text-sm text-red-200"
        >
          {{ formError }}
        </div>

        <div class="mt-5 space-y-4 text-sm">
          <div class="rounded border border-[#ACBAC4] p-3 space-y-3">
            <div>
              <div class="text-sm font-semibold text-gray-200 mb-2">{{ monthLabel }}</div>
              <div class="flex gap-2">
                <button
                  class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-200"
                  @click="calendar.navigate(-1)"
                >
                  Previous
                </button>
                <button
                  class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-200"
                  @click="calendar.navigate(1)"
                >
                  Next
                </button>
              </div>
            </div>

          </div>

          <div>
            <label class="mb-1 flex items-center gap-1 text-sm text-gray-300">
              <button
                type="button"
                class="inline-flex items-center rounded p-0.5 text-gray-300 hover:bg-[#2d2d2d] disabled:cursor-not-allowed disabled:opacity-60"
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
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 text-sm"
              :disabled="toursLoading || availableTours.length === 0"
            >
              <option value="">Select a tour</option>
              <option v-for="tour in availableTours" :key="`tour-${tour.id}`" :value="String(tour.id)">
                {{ buildTourOptionLabel(tour) }}
              </option>
            </select>
            <p v-if="toursLoading" class="mt-1 text-xs text-gray-400">Loading tours...</p>
            <p v-else-if="toursError" class="mt-1 text-xs text-red-300">{{ toursError }}</p>
            <p v-else-if="!availableTours.length" class="mt-1 text-xs text-amber-300">No tours available.</p>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Language</label>
            <select
              v-model="createForm.languageCode"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 text-sm"
            >
              <option v-for="lang in LANGUAGE_CODE_OPTIONS" :key="lang.code" :value="lang.code">
                {{ lang.label }} ({{ lang.code }})
              </option>
            </select>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Date</label>
            <input
              v-model="createForm.eventDate"
              type="date"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="text-gray-300 block mb-1">Start Time</label>
              <input
                v-model="createForm.startTime"
                type="time"
                class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2"
              />
            </div>
            <div>
              <label class="text-gray-300 block mb-1">End Time</label>
              <input
                v-model="createForm.endTime"
                type="time"
                class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2"
              />
            </div>
          </div>

          <div
            v-if="selectedCreateTour"
            class="rounded border border-[#ACBAC4] bg-[#2a2a2a] px-3 py-2 text-xs text-gray-200"
          >
            <div><span class="font-semibold">Tour:</span> {{ selectedCreateTour.name || `Tour ${selectedCreateTour.id}` }}</div>
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
