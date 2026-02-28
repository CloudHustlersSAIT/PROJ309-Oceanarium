<script setup>
const props = defineProps({
  event: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  conflict: { type: Boolean, default: false },
  bulkMode: { type: Boolean, default: false },
  checked: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'toggle-bulk'])

function formatTime(dateLike) {
  return new Date(dateLike).toLocaleTimeString('en-CA', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZone: 'America/Toronto',
  })
}
</script>

<template>
  <div
    class="rounded-md border px-2 py-1.5 text-xs cursor-pointer transition-all"
    :class="[
      conflict ? 'border-red-400 bg-red-50' : 'border-blue-200 bg-blue-50',
      selected ? 'ring-2 ring-blue-500 shadow-sm' : 'hover:shadow-sm',
    ]"
    :title="`${event.title} • ${formatTime(event.start)}-${formatTime(event.end)} • ${event.resourceName}`"
    @click="emit('select', event)"
  >
    <div class="flex items-start justify-between gap-1">
      <div class="font-semibold text-gray-800 truncate leading-tight">{{ event.title }}</div>
      <input v-if="bulkMode" type="checkbox" :checked="checked" @click.stop @change="emit('toggle-bulk', event.id)" />
    </div>

    <div class="text-[11px] text-gray-600 mt-1 leading-tight">{{ formatTime(event.start) }} - {{ formatTime(event.end) }}</div>
    <div class="text-[10px] text-gray-500 truncate mt-0.5">{{ event.resourceName }}</div>

    <div v-if="conflict" class="mt-1 text-[10px] font-semibold text-red-700 uppercase tracking-wide">Conflict detected</div>
  </div>
</template>
