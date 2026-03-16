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
  bulkSelection: { type: Array, required: true },
  autoAssignLoading: { type: Boolean, default: false },
})

const emit = defineEmits([
  'select-event',
  'toggle-bulk',
  'navigate-next',
  'navigate-prev',
  'select-date',
  'open-day-events',
  'auto-assign-week',
])

function keyDate(date) {
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatSlotLabel(totalMinutes) {
  const hour24 = Math.floor(totalMinutes / 60)
  const minute = totalMinutes % 60
  const period = hour24 >= 12 ? 'pm' : 'am'
  const hour12 = hour24 % 12 || 12
  return `${String(hour12).padStart(2, '0')}:${String(minute).padStart(2, '0')} ${period}`
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
  Array.from({ length: (18 * 60 + 30 - 10 * 60) / 30 + 1 }, (_, i) => {
    const minuteOfDay = 10 * 60 + i * 30
    return {
      key: String(minuteOfDay),
      minuteOfDay,
      label: formatSlotLabel(minuteOfDay),
    }
  }),
)

const monthCells = computed(() => {
  const first = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth(), 1)
  const last = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth() + 1, 0)
  const cells = []
  for (let i = 0; i < first.getDay(); i += 1) cells.push(null)
  for (let d = 1; d <= last.getDate(); d += 1)
    cells.push(new Date(first.getFullYear(), first.getMonth(), d))
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
})

function eventsForDate(dateLike) {
  if (!dateLike) return []
  const key = keyDate(dateLike)
  return props.events.filter((event) => keyDate(event.start) === key)
}

function visibleEventsForDate(dateLike) {
  return eventsForDate(dateLike).slice(0, 3)
}

function hiddenEventsCountForDate(dateLike) {
  const total = eventsForDate(dateLike).length
  return Math.max(0, total - 3)
}

function eventsForSlot(dateLike, minuteOfDay) {
  const dayKey = keyDate(dateLike)

  return props.events.filter((event) => {
    const eventStart = new Date(event.start)
    return (
      keyDate(eventStart) === dayKey &&
      eventStart.getHours() * 60 + eventStart.getMinutes() === minuteOfDay
    )
  })
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
  <section
    class="h-full min-h-[640px] rounded-xl border border-blue-500 bg-white p-4 shadow-md dark:border-sky-700/40 dark:bg-[#161B27] dark:shadow-black/30 xl:min-h-[865px]"
  >
    <div v-if="view === 'month'">
      <div class="flex items-center justify-end mb-2 gap-2">
        <div class="flex items-center gap-2">
          <button
            class="flex h-9 w-9 items-center justify-center rounded-full border border-[#ACBAC4] bg-white text-lg leading-none text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
            aria-label="Previous month"
            @click="emit('navigate-prev')"
          >
            &lt;
          </button>
          <button
            class="flex h-9 w-9 items-center justify-center rounded-full border border-[#ACBAC4] bg-white text-lg leading-none text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
            aria-label="Next month"
            @click="emit('navigate-next')"
          >
            &gt;
          </button>
        </div>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="name in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']"
          :key="name"
          class="rounded border border-[#ACBAC4] bg-gray-50 py-1.5 text-center text-[11px] font-semibold uppercase tracking-wide text-gray-600 dark:border-white/15 dark:bg-[#1A2231] dark:text-slate-400"
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
                ? 'border-blue-600 bg-blue-50 cursor-pointer dark:bg-sky-950/45'
                : isToday(cell)
                  ? 'border-blue-400 bg-blue-50/40 cursor-pointer hover:bg-gray-50 dark:bg-sky-950/30 dark:hover:bg-white/5'
                  : 'border-[#ACBAC4] bg-white cursor-pointer hover:bg-gray-50 dark:border-white/10 dark:bg-[#1C2333] dark:hover:bg-white/5'
              : 'border-[#ACBAC4] bg-gray-50 dark:border-white/10 dark:bg-[#1A2231]'
          "
          @click="cell && emit('select-date', cell)"
        >
          <div v-if="cell" class="mb-1.5 text-[11px] font-semibold text-gray-700 dark:text-slate-300">
            {{ cell.getDate() }}
          </div>
          <div class="space-y-1">
            <CalendarEventCard
              v-for="event in visibleEventsForDate(cell)"
              :key="event.id"
              :event="event"
              :selected="selectedEvent?.id === event.id"
              :conflict="Boolean(conflicts[event.id])"
              :checked="bulkSelection.includes(event.id)"
              @select="emit('select-event', event)"
              @toggle-bulk="emit('toggle-bulk', event.id)"
            />
            <button
              v-if="hiddenEventsCountForDate(cell) > 0"
              class="w-full rounded border border-dashed border-blue-300 bg-blue-50 px-1.5 py-1 text-[10px] font-medium text-blue-700 hover:bg-blue-100 dark:border-sky-700/50 dark:bg-sky-950/40 dark:text-sky-300 dark:hover:bg-sky-950/60"
              @click.stop="emit('open-day-events', cell)"
            >
              +{{ hiddenEventsCountForDate(cell) }} more
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="view === 'week'" class="h-full">
      <div class="flex items-center justify-between gap-2 mb-2">
        <button
          type="button"
          class="rounded border border-blue-600 bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="autoAssignLoading"
          @click="emit('auto-assign-week')"
        >
          {{ autoAssignLoading ? 'Assigning...' : 'Auto Assign' }}
        </button>
        <div class="flex items-center gap-2">
          <button
          class="flex h-9 w-9 items-center justify-center rounded-full border border-[#ACBAC4] bg-white text-lg leading-none text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
          aria-label="Previous week"
          @click="emit('navigate-prev')"
        >
          &lt;
        </button>
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full border border-[#ACBAC4] bg-white text-lg leading-none text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
          aria-label="Next week"
          @click="emit('navigate-next')"
        >
          &gt;
        </button>
        </div>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="day in weekDays"
          :key="day.toISOString()"
          class="min-h-[560px] rounded border bg-white p-1.5 dark:border-white/10 dark:bg-[#1C2333] xl:min-h-[680px]"
          :class="isToday(day) ? 'border-blue-400' : 'border-[#ACBAC4]'"
        >
          <div class="mb-2 border-b border-[#ACBAC4] pb-2 dark:border-white/10">
            <div class="text-[11px] font-semibold uppercase tracking-wide text-gray-600 dark:text-slate-500">
              {{ day.toLocaleDateString('en-CA', { weekday: 'short' }) }}
            </div>
            <div
              class="text-sm font-semibold"
              :class="isToday(day) ? 'text-blue-700 dark:text-sky-300' : 'text-gray-700 dark:text-slate-300'"
            >
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
              :checked="bulkSelection.includes(event.id)"
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
            class="flex h-12 items-center rounded border border-[#ACBAC4] bg-gray-50 px-2 text-xs font-medium text-gray-600 dark:border-white/10 dark:bg-[#1A2231] dark:text-slate-400 xl:h-14"
          >
            {{ slot.label }}
          </div>
        </div>
        <div class="space-y-2">
          <div
            v-for="slot in daySlots"
            :key="`day-slot-${slot.key}`"
            class="min-h-12 rounded border border-[#ACBAC4] bg-white p-1.5 dark:border-white/10 dark:bg-[#1C2333] xl:min-h-14"
          >
            <div class="space-y-1">
              <CalendarEventCard
                v-for="event in eventsForSlot(selectedDate, slot.minuteOfDay)"
                :key="event.id"
                :event="event"
                :selected="selectedEvent?.id === event.id"
                :conflict="Boolean(conflicts[event.id])"
                :checked="bulkSelection.includes(event.id)"
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
