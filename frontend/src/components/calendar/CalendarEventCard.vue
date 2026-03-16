<script setup>
import { formatLocalTimeLowerAmPm } from '../../utils/reservation'

defineProps({
  event: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  conflict: { type: Boolean, default: false },
  checked: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'toggle-bulk'])

function formatTime(dateLike) {
  return formatLocalTimeLowerAmPm(dateLike)
}

function isUnassignedStatus(status) {
  const normalized = String(status || '').trim().toLowerCase()
  return normalized === 'unassigned' || normalized === 'unassignable'
}
</script>

<template>
  <div
    class="rounded-md border px-2 py-1.5 text-xs cursor-pointer transition-all"
    :class="[
      conflict
        ? 'border-red-400 bg-red-50'
        : isUnassignedStatus(event.status)
          ? 'border-amber-400 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40'
          : 'border-blue-200 bg-blue-50 dark:border-sky-700/40 dark:bg-sky-950/35',
      selected ? 'ring-2 ring-blue-500 shadow-sm' : 'hover:shadow-sm',
    ]"
    :title="`${event.title} • ${formatTime(event.start)}-${formatTime(event.end)} • ${event.resourceName}`"
    @click.stop="emit('select', event)"
  >
    <div class="flex items-start justify-between gap-1">
      <div class="truncate font-semibold leading-tight text-gray-800 dark:text-slate-100">{{ event.title }}</div>
      <input
        type="checkbox"
        :checked="checked"
        @click.stop
        @change="emit('toggle-bulk', event.id)"
      />
    </div>

    <div class="mt-1 text-[11px] leading-tight text-gray-600 dark:text-slate-400">
      {{ formatTime(event.start) }} - {{ formatTime(event.end) }}
    </div>
    <div class="mt-0.5 truncate text-[10px] text-gray-500 dark:text-slate-500">
      Status: {{ String(event.status || 'Unknown').toUpperCase() }}
    </div>

    <div
      v-if="isUnassignedStatus(event.status)"
      class="mt-1 inline-flex rounded border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800 dark:border-amber-700 dark:bg-amber-950/55 dark:text-amber-300"
    >
      {{ String(event.status || 'UNASSIGNED').toUpperCase() }}
    </div>

    <div
      v-if="conflict"
      class="mt-1 text-[10px] font-semibold uppercase tracking-wide text-red-700 dark:text-red-300"
    >
      Conflict detected
    </div>
  </div>
</template>
