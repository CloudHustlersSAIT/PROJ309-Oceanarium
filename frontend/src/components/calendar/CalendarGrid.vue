<script setup>
import { computed } from 'vue'
import CalendarEventCard from './CalendarEventCard.vue'

const props = defineProps({
  view: { type: String, required: true },
  selectedDate: { type: Date, required: true },
  events: { type: Array, required: true },
  selectedEvent: { type: Object, default: null },
  conflicts: { type: Object, required: true },
  resources: { type: Array, required: true },
  bulkMode: { type: Boolean, default: false },
  bulkSelection: { type: Array, required: true },
})

const emit = defineEmits([
  'select-event',
  'move-event',
  'toggle-bulk',
  'navigate-next',
  'navigate-prev',
  'select-date',
])

function keyDate(date) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatHourLabel(hour24) {
  const period = hour24 >= 12 ? 'p.m.' : 'a.m.'
  const hour12 = hour24 % 12 || 12
  return `${String(hour12).padStart(2, '0')}:00${period}`
}

const weekDays = computed(() => {
  const start = new Date(props.selectedDate)
  start.setDate(start.getDate() - start.getDay())
  start.setHours(0, 0, 0, 0)

  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(start)
    day.setDate(start.getDate() + i)
    return day
  })
})

const daySlots = computed(() =>
  Array.from({ length: 24 }, (_, i) => {
    const hour = i
    return {
      key: `${String(hour).padStart(2, '0')}:00`,
      hour,
      label: formatHourLabel(hour),
    }
  }),
)

const monthCells = computed(() => {
  const first = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth(), 1)
  const last = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth() + 1, 0)
  const cells = []
  for (let i = 0; i < first.getDay(); i += 1) cells.push(null)
  for (let d = 1; d <= last.getDate(); d += 1) cells.push(new Date(first.getFullYear(), first.getMonth(), d))
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
})

function eventsForDate(dateLike) {
  const key = keyDate(dateLike)
  return props.events.filter((event) => keyDate(event.start) === key)
}

function eventsForHour(dateLike, hour) {
  const dayKey = keyDate(dateLike)

  return props.events.filter((event) => {
    const eventStart = new Date(event.start)
    return keyDate(eventStart) === dayKey && eventStart.getHours() === hour
  })
}

function dropToDate(event, dateLike) {
  const raw = event.dataTransfer.getData('text/plain')
  if (!raw) return

  const droppedDate = new Date(dateLike)
  const selected = props.events.find((item) => item.id === raw)
  if (!selected) return

  const old = new Date(selected.start)
  droppedDate.setHours(old.getHours(), old.getMinutes(), 0, 0)
  emit('move-event', { id: selected.id, start: droppedDate.toISOString() })
}

function dropToHour(event, dateLike, hour) {
  const raw = event.dataTransfer.getData('text/plain')
  if (!raw) return

  const droppedDate = new Date(dateLike)
  const selected = props.events.find((item) => item.id === raw)
  if (!selected) return

  const old = new Date(selected.start)
  droppedDate.setHours(hour, old.getMinutes(), 0, 0)
  emit('move-event', { id: selected.id, start: droppedDate.toISOString() })
}

function isToday(dateLike) {
  const date = new Date(dateLike)
  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )
}

function isSelectedDate(dateLike) {
  const date = new Date(dateLike)
  return (
    date.getFullYear() === props.selectedDate.getFullYear() &&
    date.getMonth() === props.selectedDate.getMonth() &&
    date.getDate() === props.selectedDate.getDate()
  )
}
</script>

<template>
  <section class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500 h-full min-h-[640px] xl:min-h-[865px]">
    <div v-if="view === 'month'">
      <div class="flex items-center justify-end mb-2">
        <div class="flex items-center gap-2">
          <button
            class="h-9 w-9 rounded-full border border-[#ACBAC4] bg-white text-gray-700 hover:bg-gray-50 text-lg leading-none flex items-center justify-center"
            @click="emit('navigate-prev')"
            aria-label="Previous month"
          >
            &lt;
          </button>
          <button
            class="h-9 w-9 rounded-full border border-[#ACBAC4] bg-white text-gray-700 hover:bg-gray-50 text-lg leading-none flex items-center justify-center"
            @click="emit('navigate-next')"
            aria-label="Next month"
          >
            &gt;
          </button>
        </div>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="name in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']"
          :key="name"
          class="text-[11px] font-semibold uppercase tracking-wide text-gray-600 text-center py-1.5 border border-[#ACBAC4] rounded bg-gray-50"
        >
          {{ name }}
        </div>

        <div
          v-for="(cell, index) in monthCells"
          :key="index"
          class="min-h-[110px] xl:min-h-[132px] border rounded p-1.5 transition-colors"
          :class="
            cell
              ? isSelectedDate(cell)
                ? 'border-blue-600 bg-blue-50 cursor-pointer'
                : isToday(cell)
                  ? 'border-blue-400 bg-blue-50/40 cursor-pointer hover:bg-gray-50'
                  : 'border-[#ACBAC4] bg-white cursor-pointer hover:bg-gray-50'
              : 'border-[#ACBAC4] bg-gray-50'
          "
          @click="cell && emit('select-date', cell)"
          @dragover.prevent
          @drop.prevent="cell && dropToDate($event, cell)"
        >
          <div v-if="cell" class="text-[11px] font-semibold text-gray-700 mb-1.5">{{ cell.getDate() }}</div>
          <div class="space-y-1">
            <CalendarEventCard
              v-for="event in eventsForDate(cell)"
              :key="event.id"
              :event="event"
              :selected="selectedEvent?.id === event.id"
              :conflict="Boolean(conflicts[event.id])"
              :bulk-mode="bulkMode"
              :checked="bulkSelection.includes(event.id)"
              draggable="true"
              @dragstart="$event.dataTransfer.setData('text/plain', event.id)"
              @select="emit('select-event', event)"
              @toggle-bulk="emit('toggle-bulk', event.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="view === 'week'" class="h-full">
      <div class="flex items-center justify-end mb-2">
        <button
          class="bg-white border border-[#ACBAC4] text-gray-700 px-3 py-1.5 rounded text-sm hover:bg-gray-50"
          @click="emit('navigate-next')"
        >
          Next week
        </button>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="day in weekDays"
          :key="day.toISOString()"
          class="border rounded p-1.5 min-h-[560px] xl:min-h-[680px] bg-white"
          :class="isToday(day) ? 'border-blue-400' : 'border-[#ACBAC4]'"
          @dragover.prevent
          @drop.prevent="dropToDate($event, day)"
        >
          <div class="mb-2 pb-2 border-b border-[#ACBAC4]">
            <div class="text-[11px] font-semibold uppercase tracking-wide text-gray-600">
              {{ day.toLocaleDateString('en-CA', { weekday: 'short' }) }}
            </div>
            <div class="text-sm font-semibold" :class="isToday(day) ? 'text-blue-700' : 'text-gray-700'">
              {{ day.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }) }}
            </div>
          </div>

          <div class="space-y-2">
            <CalendarEventCard
              v-for="event in eventsForDate(day)"
              :key="event.id"
              :event="event"
              :selected="selectedEvent?.id === event.id"
              :conflict="Boolean(conflicts[event.id])"
              :bulk-mode="bulkMode"
              :checked="bulkSelection.includes(event.id)"
              draggable="true"
              @dragstart="$event.dataTransfer.setData('text/plain', event.id)"
              @select="emit('select-event', event)"
              @toggle-bulk="emit('toggle-bulk', event.id)"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="grid grid-cols-[86px_1fr] gap-2">
        <div class="space-y-2">
          <div
            v-for="slot in daySlots"
            :key="slot.key"
            class="h-12 xl:h-14 text-xs text-gray-600 flex items-center px-2 border border-[#ACBAC4] rounded bg-gray-50 font-medium"
          >
            {{ slot.label }}
          </div>
        </div>
        <div class="space-y-2">
          <div
            v-for="slot in daySlots"
            :key="`day-slot-${slot.key}`"
            class="min-h-12 xl:min-h-14 border border-[#ACBAC4] rounded p-1.5 bg-white"
            @dragover.prevent
            @drop.prevent="dropToHour($event, selectedDate, slot.hour)"
          >
            <div class="space-y-1">
              <CalendarEventCard
                v-for="event in eventsForHour(selectedDate, slot.hour)"
                :key="event.id"
                :event="event"
                :selected="selectedEvent?.id === event.id"
                :conflict="Boolean(conflicts[event.id])"
                :bulk-mode="bulkMode"
                :checked="bulkSelection.includes(event.id)"
                draggable="true"
                @dragstart="$event.dataTransfer.setData('text/plain', event.id)"
                @select="emit('select-event', event)"
                @toggle-bulk="emit('toggle-bulk', event.id)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

