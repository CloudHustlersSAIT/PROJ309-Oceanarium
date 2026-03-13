<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import CalendarToolbar from '../components/calendar/CalendarToolbar.vue'
import CalendarGrid from '../components/calendar/CalendarGrid.vue'
import CancelButton from '../components/CancelButton.vue'
import SaveButton from '../components/SaveButton.vue'
import { useCalendarStore } from '../stores/calendar'
import { createSchedule, getTours } from '../services/api'
import { downloadCsv } from '../utils/calendar'
import {
  formatLocalTimeLowerAmPm,
} from '../utils/reservation'

const calendar = useCalendarStore()
const bulkMode = ref(false)
const showCreatePopup = ref(false)
const showConfirmCreatePopup = ref(false)
const showTourDetailsPopup = ref(false)
const showDayEventsPopup = ref(false)
const formError = ref('')
const createDraftSnapshot = ref('')
const creatingSchedule = ref(false)
const toursLoading = ref(false)
const toursError = ref('')
const availableTours = ref([])

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

  const formatDate = (d) =>
    `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`
  const formatTime = (d) =>
    `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`

  return {
    source: selected.source,
    guide_id: selected.guideId ?? '-',
    reservation_count: selected.reservationCount ?? '-',
    status: selected.status || '-',
    customer_id: selected.customerId ?? '-',
    tour_id: selected.tourId ?? '-',
    date: hasValidStart ? formatDate(start) : '',
    start_time: hasValidStart ? formatTime(start) : '',
    end_time: hasValidEnd ? formatTime(end) : '',
    adult_tickets: selected.adultTickets ?? '-',
    child_tickets: selected.childTickets ?? '-',
    language: selected.language || 'English',
  }
})

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

function reservationDetailsStatusClass(status) {
  const normalized = String(status || '')
    .trim()
    .toLowerCase()
  if (normalized === 'confirmed') {
    return 'sharp-green-300 bg-green-50 text-green-800'
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
  const selectedId = calendar.selectedEvent?.id
  if (!selectedId) return

  const confirmed = window.confirm('Delete selected tour?')
  if (!confirmed) return

  calendar.deleteEvent(selectedId)
  showTourDetailsPopup.value = false
}

watch(
  () => calendar.selectedDate,
  () => {
    if (!showCreatePopup.value) return
    createForm.value.eventDate = getSelectedDateIso()
  },
)

onMounted(() => {
  calendar.setView('month')
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
              class="px-3 py-1.5 rounded border border-gray-300 text-sm"
              :class="
                bulkMode ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700'
              "
              @click="bulkMode = !bulkMode"
            >
              Bulk selection
            </button>
            <button
              v-if="calendar.selectedEvent"
              class="px-3 py-1.5 rounded bg-red-600 text-white text-sm"
              @click="handleDeleteSelectedEvent"
            >
              Delete selected
            </button>
            <CancelButton
              v-if="bulkMode"
              label="Cancel selected"
              @cancel="calendar.applyBulkStatus('cancelled')"
            />
            <button v-if="bulkMode" class="px-3 py-1.5 rounded border border-gray-300 text-sm" @click="calendar.clearBulkSelection()">Clear</button>
          </div>
        </div>

        <CalendarGrid
          :view="calendar.currentView"
          :selected-date="selectedDate"
          :events="calendar.eventsInRange"
          :selected-event="calendar.selectedEvent"
          :conflicts="calendar.conflicts"
          :resources="calendar.resources"
          :bulk-mode="bulkMode"
          :bulk-selection="calendar.bulkSelection"
          @select-event="handleSelectEvent"
          @toggle-bulk="calendar.toggleBulkSelection"
          @select-date="handleSelectDate"
          @open-day-events="handleOpenDayEvents"
          @navigate-next="handleNavigateNext"
          @navigate-prev="handleNavigatePrev"
        />
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

        <div class="space-y-2 text-sm text-gray-700">
          <div><span class="font-semibold">guide_id:</span> {{ selectedTourDetails.guide_id }}</div>
          <div
            class="rounded border px-2 py-1"
            :class="reservationDetailsStatusClass(selectedTourDetails.status)"
          >
            <span class="font-semibold">status:</span> {{ selectedTourDetails.status }}
          </div>
          <div>
            <span class="font-semibold">reservation_count:</span>
            {{ selectedTourDetails.reservation_count }}
          </div>
          <div>
            <span class="font-semibold">customer_id:</span> {{ selectedTourDetails.customer_id }}
          </div>
          <div><span class="font-semibold">tour_id:</span> {{ selectedTourDetails.tour_id }}</div>
          <div><span class="font-semibold">date:</span> {{ selectedTourDetails.date }}</div>
          <div>
            <span class="font-semibold">start_time:</span> {{ selectedTourDetails.start_time }}
          </div>
          <div><span class="font-semibold">end_time:</span> {{ selectedTourDetails.end_time }}</div>
          <div>
            <span class="font-semibold">adult_tickets:</span>
            {{ selectedTourDetails.adult_tickets }}
          </div>
          <div>
            <span class="font-semibold">child_tickets:</span>
            {{ selectedTourDetails.child_tickets }}
          </div>
          <div><span class="font-semibold">language:</span> {{ selectedTourDetails.language }}</div>
        </div>

        <div class="mt-5 flex justify-end">
          <button
            class="px-4 py-2 rounded border border-red-200 bg-red-50 text-red-600 hover:bg-red-100"
            @click="closeTourDetailsPopup"
          >
            Close
          </button>
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

    <div
      v-if="showConfirmCreatePopup"
      class="fixed inset-0 z-[60] bg-black/50 p-4 flex items-center justify-center"
      @click.self="showConfirmCreatePopup = false"
    >
      <div class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-5 shadow-xl">
        <h4 class="typo-modal-title">Confirm creation</h4>
        <p class="mt-2 typo-body">Do you want to proceed with creating this schedule?</p>
        <div class="mt-5 flex items-center justify-end gap-2">
          <CancelButton @cancel="showConfirmCreatePopup = false" />
          <SaveButton
            label="Yes, proceed"
            :loading="creatingSchedule"
            :disabled="creatingSchedule"
            @save="saveCreatedEvent"
          />
        </div>
      </div>
    </div>
  </div>
</template>
