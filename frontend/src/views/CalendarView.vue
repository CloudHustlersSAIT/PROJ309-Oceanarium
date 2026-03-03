<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import CalendarToolbar from '../components/calendar/CalendarToolbar.vue'
import CalendarGrid from '../components/calendar/CalendarGrid.vue'
import { useCalendarStore } from '../stores/calendar'
import {
  addMinutesToTime,
  createEventId,
  downloadCsv,
  formatMinutesCompact,
  minutesToDurationLabel,
  toIsoFromParts,
} from '../utils/calendar'

const calendar = useCalendarStore()
const bulkMode = ref(false)
const searchText = ref('')
const showEvents = ref(false)
const showTask = ref(false)
const showAppointment = ref(false)
const showCreatePopup = ref(false)
const createType = ref('event')
const createAllDay = ref(false)

const createForm = ref({
  title: '',
  date: '',
  startTime: '09:00',
  endTime: '09:15',
  guests: '',
  location: '',
  description: '',
})


const startTimeOptions = computed(() => {
  const options = []
  for (let minutes = 0; minutes < 24 * 60; minutes += 15) {
    const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
    const mm = String(minutes % 60).padStart(2, '0')
    options.push({ value: `${hh}:${mm}`, label: formatMinutesCompact(minutes) })
  }
  return options
})

const endTimeOptions = computed(() => {
  const [startH, startM] = createForm.value.startTime.split(':').map(Number)
  const startMinutes = startH * 60 + startM
  const options = []

  for (let minutes = startMinutes; minutes <= Math.min(startMinutes + 12 * 60, 23 * 60 + 45); minutes += 15) {
    const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
    const mm = String(minutes % 60).padStart(2, '0')
    const duration = minutes - startMinutes
    options.push({ value: `${hh}:${mm}`, label: `${formatMinutesCompact(minutes)} ${minutesToDurationLabel(duration)}` })
  }

  if (createForm.value.startTime === '23:45') {
    options.push({ value: '23:59', label: `${formatMinutesCompact(23 * 60 + 59)} (${minutesToDurationLabel(14)})` })
  }

  return options
})

const selectedDate = computed(() => new Date(calendar.selectedDate))
const monthLabel = computed(() =>
  selectedDate.value.toLocaleDateString('en-CA', { month: 'long', year: 'numeric' }),
)

function handleCreateEvent() {
  const selected = new Date(calendar.selectedDate)
  createForm.value = {
    title: '',
    date: `${selected.getFullYear()}-${String(selected.getMonth() + 1).padStart(2, '0')}-${String(selected.getDate()).padStart(2, '0')}`,
    startTime: '09:00',
    endTime: '09:15',
    guests: '',
    location: '',
    description: '',
  }
  createAllDay.value = false
  createType.value = 'event'
  showCreatePopup.value = true
}

function closeCreatePopup() {
  showCreatePopup.value = false
}

function saveCreatedEvent() {
  if (!createForm.value.title.trim() || !createForm.value.date) return

  let start = createAllDay.value
    ? toIsoFromParts(createForm.value.date, '00:00')
    : toIsoFromParts(createForm.value.date, createForm.value.startTime)
  let end = createAllDay.value
    ? toIsoFromParts(createForm.value.date, '23:59')
    : toIsoFromParts(createForm.value.date, createForm.value.endTime)

  if (!createAllDay.value && new Date(end) <= new Date(start)) {
    const fixedEndTime = createForm.value.startTime === '23:45' ? '23:59' : addMinutesToTime(createForm.value.startTime, 15)
    createForm.value.endTime = fixedEndTime
    end = toIsoFromParts(createForm.value.date, fixedEndTime)
  }

  if (new Date(end) <= new Date(start)) return

  const draft = {
    id: createEventId(),
    source: 'manual',
    sourceId: null,
    title: createForm.value.title.trim(),
    start,
    end,
    resourceId: calendar.resources[0]?.id || 'guide-unassigned',
    resourceName: calendar.resources[0]?.name || 'Unassigned Guide',
    status: 'scheduled',
    type: createType.value,
    priority: 'medium',
    conflictFlag: false,
    notes: [createForm.value.location, createForm.value.guests, createForm.value.description].filter(Boolean).join(' • '),
  }

  calendar.events.push(draft)
  calendar.setDate(new Date(`${createForm.value.date}T12:00:00`))
  calendar.selectEvent(draft)
  calendar.recomputeConflicts()
  showCreatePopup.value = false
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

function handleNavigateNext() {
  calendar.navigate(1)
}

function handleNavigatePrev() {
  calendar.navigate(-1)
}

function syncQuickFilters() {
  const types = []
  if (showEvents.value) types.push('event')
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
  (startTime) => {
    const nextEndTime = addMinutesToTime(startTime, 15)
    createForm.value.endTime = endTimeOptions.value.some((option) => option.value === nextEndTime)
      ? nextEndTime
      : endTimeOptions.value[0]?.value || nextEndTime
  },
)

onMounted(() => {
  calendar.setView('month')
  calendar.loadEvents()
  syncQuickFilters()
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
          @export="exportVisibleEvents"
        />

        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between bg-white rounded-xl shadow-md p-3 border-1 border-blue-500">
          <div class="text-sm text-gray-600">{{ calendar.loading ? 'Loading events...' : `${calendar.eventsInRange.length} events in range` }}</div>
          <div class="flex items-center gap-2 flex-wrap">
            <button class="px-3 py-1.5 rounded border border-gray-300 text-sm" :class="bulkMode ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700'" @click="bulkMode = !bulkMode">
              Bulk selection
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

        <div class="grid grid-cols-1 xl:grid-cols-[260px_minmax(865px,1fr)] gap-4 min-h-[680px] xl:min-h-[865px]">
          <aside class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500 h-fit xl:sticky xl:top-4 space-y-4">
            <button
              class="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium"
              @click="handleCreateEvent"
            >
              + Create
            </button>

            <div>
              <div class="text-sm font-semibold text-gray-800 mb-2">{{ monthLabel }}</div>
              <div class="flex gap-2">
                <button class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-700" @click="calendar.navigate(-1)">
                  Previous
                </button>
                <button class="flex-1 border border-[#ACBAC4] rounded px-2 py-1.5 text-sm text-gray-700" @click="calendar.navigate(1)">
                  Next
                </button>
              </div>
            </div>

            <div>
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Search events</label>
              <input
                v-model="searchText"
                type="text"
                placeholder="Search by title or resource"
                class="mt-1 w-full border border-[#ACBAC4] rounded px-3 py-2 text-sm"
              />
            </div>

            <div class="space-y-2">
              <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide">My calendars</div>
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="showEvents" type="checkbox" class="accent-blue-600" />
                Events
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="showTask" type="checkbox" class="accent-blue-600" />
                Task
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="showAppointment" type="checkbox" class="accent-blue-600" />
                Appointment
              </label>
            </div>
          </aside>

          <CalendarGrid
            :view="calendar.currentView"
            :selected-date="selectedDate"
            :events="calendar.eventsInRange"
            :selected-event="calendar.selectedEvent"
            :conflicts="calendar.conflicts"
            :resources="calendar.resources"
            :bulk-mode="bulkMode"
            :bulk-selection="calendar.bulkSelection"
            @select-event="calendar.selectEvent"
            @move-event="handleMoveEvent"
            @toggle-bulk="calendar.toggleBulkSelection"
            @select-date="handleSelectDate"
            @navigate-next="handleNavigateNext"
            @navigate-prev="handleNavigatePrev"
          />
        </div>
      </div>
    </main>

    <div v-if="showCreatePopup" class="fixed inset-0 z-50 bg-black/40" @click.self="closeCreatePopup">
      <div class="absolute right-0 top-0 h-full w-full max-w-[420px] bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <div class="text-sm text-gray-300">Create</div>
          <button class="text-gray-300 hover:text-white text-xl leading-none" @click="closeCreatePopup">×</button>
        </div>

        <input
          v-model="createForm.title"
          type="text"
          placeholder="Add title"
          class="w-full bg-transparent border-b border-[#ACBAC4] pb-2 text-3xl font-semibold outline-none placeholder:text-gray-400"
        />

        <div class="mt-4 flex items-center gap-2">
          <button
            class="px-3 py-1.5 rounded text-sm"
            :class="createType === 'event' ? 'bg-blue-700 text-white' : 'bg-[#2d2d2d] text-gray-300'"
            @click="createType = 'event'"
          >
            Event
          </button>
          <button
            class="px-3 py-1.5 rounded text-sm"
            :class="createType === 'task' ? 'bg-blue-700 text-white' : 'bg-[#2d2d2d] text-gray-300'"
            @click="createType = 'task'"
          >
            Task
          </button>
          <button
            class="px-3 py-1.5 rounded text-sm"
            :class="createType === 'appointment' ? 'bg-blue-700 text-white' : 'bg-[#2d2d2d] text-gray-300'"
            @click="createType = 'appointment'"
          >
            Appointment
          </button>
        </div>

        <div class="mt-5 space-y-4 text-sm">
          <div>
            <label class="inline-flex items-center gap-2 text-gray-200">
              <input v-model="createAllDay" type="checkbox" class="accent-blue-600" />
              All day
            </label>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Date</label>
            <input v-model="createForm.date" type="date" class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2" />
          </div>

          <div :class="createAllDay ? 'opacity-50 pointer-events-none' : ''">
            <label class="text-gray-300 block mb-1">Time</label>
            <div class="grid grid-cols-[1fr_auto_1fr] gap-2 items-center">
              <select v-model="createForm.startTime" class="bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2">
                <option v-for="option in startTimeOptions" :key="`start-${option.value}`" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <span class="text-gray-400 text-center">—</span>
              <select v-model="createForm.endTime" class="bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2">
                <option v-for="option in endTimeOptions" :key="`end-${option.value}`" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Guests</label>
            <input
              v-model="createForm.guests"
              type="text"
              placeholder="Add guests"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Location</label>
            <input
              v-model="createForm.location"
              type="text"
              placeholder="Add location"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Description</label>
            <textarea
              v-model="createForm.description"
              rows="4"
              placeholder="Add description"
              class="w-full bg-[#2d2d2d] border border-[#ACBAC4] rounded px-3 py-2 placeholder:text-gray-400"
            />
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button class="px-4 py-2 rounded border border-[#ACBAC4] text-gray-200" @click="closeCreatePopup">Cancel</button>
          <button class="px-5 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white font-medium" @click="saveCreatedEvent">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
