<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import CalendarToolbar from '../components/calendar/CalendarToolbar.vue'
import CalendarGrid from '../components/calendar/CalendarGrid.vue'
import { useCalendarStore } from '../stores/calendar'
import { createBooking } from '../services/api'
import { downloadCsv } from '../utils/calendar'
import { LANGUAGE_OPTIONS } from '../constants/languages'

const calendar = useCalendarStore()
const bulkMode = ref(false)
const searchText = ref('')
const showEvents = ref(false)
const showTask = ref(false)
const showAppointment = ref(false)
const showCreatePopup = ref(false)
const showTourDetailsPopup = ref(false)
const showDayEventsPopup = ref(false)
const formError = ref('')
const createDraftSnapshot = ref('')
const creatingReservation = ref(false)
const ID_MAX_LENGTH = 6
const SHORT_NUMERIC_MAX_LENGTH = 2

const createForm = ref({
  customerId: '',
  tourId: '',
  date: '',
  startTime: '09:00',
  endTime: '10:00',
  adultTickets: '',
  childTickets: '',
  language: 'English',
})

const timeOptions = Array.from({ length: 15 }, (_, i) => {
  const minutes = (9 * 60) + i * 30
  const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
  const mm = String(minutes % 60).padStart(2, '0')
  const value = `${hh}:${mm}`
  const label = new Date(`2000-01-01T${value}:00`).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
  return { value, label }
})

const startTimeOptions = computed(() => timeOptions.slice(0, -1))

const endTimeOptions = computed(() =>
  timeOptions.filter((option) => option.value > createForm.value.startTime),
)

const canSaveCreatedEvent = computed(() =>
  Boolean(createForm.value.customerId.trim())
  && Boolean(createForm.value.tourId.trim())
  && Boolean(createForm.value.date)
  && Boolean(createForm.value.startTime)
  && Boolean(createForm.value.endTime)
  && ((Number(createForm.value.adultTickets) || 0) + (Number(createForm.value.childTickets) || 0) > 0),
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
      return (
        start.getFullYear() === year
        && start.getMonth() === month
        && start.getDate() === day
      )
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

function sanitizeNumericId(value, maxLength) {
  return String(value ?? '')
    .replace(/\D/g, '')
    .slice(0, maxLength)
}

function handleNumericBeforeInput(event) {
  if (event?.data && /\D/.test(event.data)) {
    event.preventDefault()
  }
}

function handleNumericPaste(event, setter, maxLength) {
  const pastedText = event?.clipboardData?.getData('text') ?? ''
  const sanitized = sanitizeNumericId(pastedText, maxLength)
  event.preventDefault()
  setter(sanitized)
}

function setNumericField(event, field, maxLength) {
  const digitsOnly = sanitizeNumericId(event?.target?.value, maxLength)
  if (event?.target) event.target.value = digitsOnly
  createForm.value[field] = digitsOnly
}

function handleCustomerIdInput(event) {
  setNumericField(event, 'customerId', ID_MAX_LENGTH)
}

function handleTourIdInput(event) {
  setNumericField(event, 'tourId', SHORT_NUMERIC_MAX_LENGTH)
}

function handleAdultTicketsInput(event) {
  setNumericField(event, 'adultTickets', SHORT_NUMERIC_MAX_LENGTH)
}

function handleChildTicketsInput(event) {
  setNumericField(event, 'childTickets', SHORT_NUMERIC_MAX_LENGTH)
}

function hasUnsavedCreateDraft() {
  return showCreatePopup.value && createDraftSnapshot.value !== getCreateDraftSnapshot()
}

function handleCreateEvent() {
  const selected = new Date(calendar.selectedDate)
  createForm.value = {
    customerId: '',
    tourId: '',
    date: `${selected.getFullYear()}-${String(selected.getMonth() + 1).padStart(2, '0')}-${String(selected.getDate()).padStart(2, '0')}`,
    startTime: '09:00',
    endTime: '10:00',
    adultTickets: '',
    childTickets: '',
    language: 'English',
  }
  formError.value = ''
  createDraftSnapshot.value = getCreateDraftSnapshot()
  showCreatePopup.value = true
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
  const normalized = String(status || '').trim().toLowerCase()
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
  showCreatePopup.value = false
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
  formError.value = ''

  // Keep create flow aligned with Reservation page sanitization rules.
  createForm.value.customerId = sanitizeNumericId(createForm.value.customerId, ID_MAX_LENGTH)
  createForm.value.tourId = sanitizeNumericId(createForm.value.tourId, SHORT_NUMERIC_MAX_LENGTH)
  createForm.value.adultTickets = sanitizeNumericId(createForm.value.adultTickets, SHORT_NUMERIC_MAX_LENGTH)
  createForm.value.childTickets = sanitizeNumericId(createForm.value.childTickets, SHORT_NUMERIC_MAX_LENGTH)

  const customerId = Number(createForm.value.customerId)
  const tourId = Number(createForm.value.tourId)
  const adultTickets = Number(createForm.value.adultTickets) || 0
  const childTickets = Number(createForm.value.childTickets) || 0

  if (!customerId || !tourId || !createForm.value.date) {
    formError.value = 'Customer ID, Tour ID, and date are required.'
    return
  }

  if (!createForm.value.startTime || !createForm.value.endTime) {
    formError.value = 'Start time and End time are required.'
    return
  }

  if (createForm.value.endTime <= createForm.value.startTime) {
    formError.value = 'End time must be after Start time.'
    return
  }

  if (!/^\d{1,6}$/.test(createForm.value.customerId)) {
    formError.value = 'Customer ID must contain only numbers (up to 6 digits).'
    return
  }

  if (!/^\d{1,2}$/.test(createForm.value.tourId)) {
    formError.value = 'Tour ID must contain only numbers (up to 2 digits).'
    return
  }

  if (!/^\d{0,2}$/.test(createForm.value.adultTickets) || !/^\d{0,2}$/.test(createForm.value.childTickets)) {
    formError.value = 'Adult and Child Tickets must contain only numbers (up to 2 digits).'
    return
  }

  const parsedTourId = Number(createForm.value.tourId)
  if (!Number.isInteger(parsedTourId) || parsedTourId <= 0) {
    formError.value = 'Tour ID must be a valid positive number.'
    return
  }

  if (adultTickets + childTickets <= 0) {
    formError.value = 'At least one ticket is required.'
    return
  }

  creatingReservation.value = true

  createBooking({
    customer_id: createForm.value.customerId.trim(),
    tour_id: parsedTourId,
    language: createForm.value.language,
    date: createForm.value.date,
    start_time: `${createForm.value.startTime}:00`,
    end_time: `${createForm.value.endTime}:00`,
    adult_tickets: adultTickets,
    child_tickets: childTickets,
  })
    .then(async () => {
      await calendar.loadEvents()
      calendar.setDate(new Date(`${createForm.value.date}T12:00:00`))
      formError.value = ''
      createDraftSnapshot.value = ''
      showCreatePopup.value = false
    })
    .catch((error) => {
      formError.value = error?.message || 'Failed to create reservation.'
    })
    .finally(() => {
      creatingReservation.value = false
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

function handleMoveEvent({ id, start }) {
  calendar.moveEvent(id, start)
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

function syncQuickFilters() {
  const types = []
  if (showEvents.value) types.push('tour')
  if (showTask.value) types.push('task')
  if (showAppointment.value) types.push('appointment')

  calendar.setFilters({
    search: searchText.value,
    eventTypes: types,
  })
}

watch([searchText, showEvents, showTask, showAppointment], syncQuickFilters)

watch(
  () => createForm.value.startTime,
  () => {
    if (!endTimeOptions.value.length) {
      createForm.value.endTime = createForm.value.startTime
      return
    }

    if (!endTimeOptions.value.some((option) => option.value === createForm.value.endTime)) {
      createForm.value.endTime = endTimeOptions.value[0].value
    }
  },
)

onMounted(() => {
  calendar.setView('month')
  calendar.loadEvents()
  syncQuickFilters()
  document.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="flex min-h-screen bg-gray-50 overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-3 md:p-4 xl:p-6">
      <div class="space-y-4">
        <CalendarToolbar
          :current-view="calendar.currentView"
          :selected-date="selectedDate"
          @change-view="calendar.setView"
          @primary-create="handlePrimaryCreateClick"
          @export="exportVisibleEvents"
        />

        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between bg-white rounded-xl shadow-md p-3 border border-blue-500">
          <div class="text-sm text-gray-600">{{ calendar.loading ? 'Loading tours...' : `${calendar.eventsInRange.length} tours in range` }}</div>
          <div class="flex items-center gap-2 flex-wrap">
            <button class="px-3 py-1.5 rounded border border-gray-300 text-sm" :class="bulkMode ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700'" @click="bulkMode = !bulkMode">
              Bulk selection
            </button>
            <button
              v-if="calendar.selectedEvent"
              class="px-3 py-1.5 rounded bg-red-600 text-white text-sm"
              @click="handleDeleteSelectedEvent"
            >
              Delete selected
            </button>
            <button
              v-if="bulkMode"
              class="px-3 py-1.5 rounded bg-gray-500 text-white text-sm"
              @click="calendar.applyBulkStatus('cancelled')"
            >
              Cancel selected
            </button>
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
          @move-event="handleMoveEvent"
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
      <div class="absolute left-1/2 top-1/2 w-[94%] max-w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-5 shadow-2xl border border-[#ACBAC4]">
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

        <div v-if="selectedDayEvents.length === 0" class="rounded border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-sm text-gray-600">
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
                {{ new Date(event.start).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) }}
                -
                {{ new Date(event.end).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) }}
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
          <div class="rounded border px-2 py-1" :class="reservationDetailsStatusClass(selectedTourDetails.status)">
            <span class="font-semibold">status:</span> {{ selectedTourDetails.status }}
          </div>
          <div><span class="font-semibold">reservation_count:</span> {{ selectedTourDetails.reservation_count }}</div>
          <div><span class="font-semibold">customer_id:</span> {{ selectedTourDetails.customer_id }}</div>
          <div><span class="font-semibold">tour_id:</span> {{ selectedTourDetails.tour_id }}</div>
          <div><span class="font-semibold">date:</span> {{ selectedTourDetails.date }}</div>
          <div><span class="font-semibold">start_time:</span> {{ selectedTourDetails.start_time }}</div>
          <div><span class="font-semibold">end_time:</span> {{ selectedTourDetails.end_time }}</div>
          <div><span class="font-semibold">adult_tickets:</span> {{ selectedTourDetails.adult_tickets }}</div>
          <div><span class="font-semibold">child_tickets:</span> {{ selectedTourDetails.child_tickets }}</div>
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

    <div v-if="showCreatePopup" class="fixed inset-0 z-50 bg-black/40" @click.self="closeCreatePopup">
      <div class="absolute right-0 top-0 h-full w-full max-w-[420px] bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <div class="text-sm text-gray-300">Create</div>
          <button class="text-gray-300 hover:text-white text-xl leading-none" aria-label="Close create popup" @click="closeCreatePopup">×</button>
        </div>

        <div v-if="formError" class="mt-3 rounded border border-red-400 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {{ formError }}
        </div>

        <div class="mt-5 space-y-4 text-sm">
          <div class="rounded border border-[#ACBAC4] p-3 space-y-3">
            <div>
              <div class="text-sm font-semibold text-gray-200 mb-2">{{ monthLabel }}</div>
              <div class="flex gap-2">
                <button class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-200" @click="calendar.navigate(-1)">
                  Previous
                </button>
                <button class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-200" @click="calendar.navigate(1)">
                  Next
                </button>
              </div>
            </div>

            <div>
              <label class="text-xs font-semibold text-gray-300 uppercase tracking-wide">Search tours</label>
              <input
                v-model="searchText"
                type="text"
                placeholder="Search by title or resource"
                class="mt-1 w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 text-sm"
              />
            </div>

            <div class="space-y-2">
              <div class="text-xs font-semibold text-gray-300 uppercase tracking-wide">My calendars</div>
              <label class="flex items-center gap-2 text-sm text-gray-200">
                <input v-model="showEvents" type="checkbox" class="accent-blue-600" />
                Tours
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-200">
                <input v-model="showTask" type="checkbox" class="accent-blue-600" />
                Task
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-200">
                <input v-model="showAppointment" type="checkbox" class="accent-blue-600" />
                Appointment
              </label>
            </div>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Customer ID</label>
            <div class="flex items-stretch rounded border border-[#ACBAC4] bg-[#2d2d2d] overflow-hidden">
              <span class="inline-flex items-center border-r border-[#ACBAC4] bg-[#252525] px-3 text-sm text-gray-300">CUST-</span>
              <input
                :value="createForm.customerId"
                type="text"
                inputmode="numeric"
                :maxlength="ID_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="000000"
                class="w-full px-3 py-2 text-sm bg-transparent text-white outline-none placeholder:text-gray-500"
                @beforeinput="handleNumericBeforeInput"
                @paste="(event) => handleNumericPaste(event, (value) => (createForm.customerId = value), ID_MAX_LENGTH)"
                @input="handleCustomerIdInput"
              />
            </div>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Tour ID</label>
            <input
              :value="createForm.tourId"
              type="text"
              inputmode="numeric"
              :maxlength="SHORT_NUMERIC_MAX_LENGTH"
              pattern="[0-9]*"
              autocomplete="off"
              placeholder="00"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
              @beforeinput="handleNumericBeforeInput"
              @paste="(event) => handleNumericPaste(event, (value) => (createForm.tourId = value), SHORT_NUMERIC_MAX_LENGTH)"
              @input="handleTourIdInput"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Language</label>
            <select v-model="createForm.language" class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2">
              <option v-for="language in LANGUAGE_OPTIONS" :key="language" :value="language">
                {{ language }}
              </option>
            </select>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Date</label>
            <input v-model="createForm.date" type="date" required class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2" />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Start time</label>
            <select v-model="createForm.startTime" class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2">
              <option v-for="option in startTimeOptions" :key="`start-${option.value}`" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">End time</label>
            <select v-model="createForm.endTime" class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2">
              <option v-for="option in endTimeOptions" :key="`end-${option.value}`" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Adult Tickets</label>
            <input
              :value="createForm.adultTickets"
              type="text"
              inputmode="numeric"
              :maxlength="SHORT_NUMERIC_MAX_LENGTH"
              pattern="[0-9]*"
              autocomplete="off"
              placeholder="0"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
              @beforeinput="handleNumericBeforeInput"
              @paste="(event) => handleNumericPaste(event, (value) => (createForm.adultTickets = value), SHORT_NUMERIC_MAX_LENGTH)"
              @input="handleAdultTicketsInput"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Child Tickets</label>
            <input
              :value="createForm.childTickets"
              type="text"
              inputmode="numeric"
              :maxlength="SHORT_NUMERIC_MAX_LENGTH"
              pattern="[0-9]*"
              autocomplete="off"
              placeholder="0"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
              @beforeinput="handleNumericBeforeInput"
              @paste="(event) => handleNumericPaste(event, (value) => (createForm.childTickets = value), SHORT_NUMERIC_MAX_LENGTH)"
              @input="handleChildTicketsInput"
            />
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button class="px-4 py-2 rounded border border-[#ACBAC4] text-gray-200" @click="closeCreatePopup">Cancel</button>
          <button
            class="px-5 py-2 rounded text-white font-medium"
            :class="canSaveCreatedEvent && !creatingReservation ? 'bg-blue-500 hover:bg-blue-600' : 'bg-blue-500/40 cursor-not-allowed'"
            :disabled="!canSaveCreatedEvent || creatingReservation"
            @click="saveCreatedEvent"
          >
            {{ creatingReservation ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
