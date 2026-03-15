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
          ? 'border-amber-400 bg-amber-50'
          : 'border-blue-200 bg-blue-50',
      selected ? 'ring-2 ring-blue-500 shadow-sm' : 'hover:shadow-sm',
    ]"
    :title="`${event.title} • ${formatTime(event.start)}-${formatTime(event.end)} • ${event.resourceName}`"
    @click.stop="emit('select', event)"
  >
    <div class="flex items-start justify-between gap-1">
      <div class="font-semibold text-gray-800 truncate leading-tight">{{ event.title }}</div>
      <input
        type="checkbox"
        :checked="checked"
        @click.stop
        @change="emit('toggle-bulk', event.id)"
      />
    </div>

    <div class="text-[11px] text-gray-600 mt-1 leading-tight">
      {{ formatTime(event.start) }} - {{ formatTime(event.end) }}
    </div>
    <div class="text-[10px] text-gray-500 truncate mt-0.5">
      Status: {{ String(event.status || 'Unknown').toUpperCase() }}
    </div>

    <div
      v-if="isUnassignedStatus(event.status)"
      class="mt-1 inline-flex rounded border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800"
    >
      {{ String(event.status || 'UNASSIGNED').toUpperCase() }}
    </div>

    <div
      v-if="conflict"
      class="mt-1 text-[10px] font-semibold text-red-700 uppercase tracking-wide"
    >
      Conflict detected
    </div>
  </div>
</template>
