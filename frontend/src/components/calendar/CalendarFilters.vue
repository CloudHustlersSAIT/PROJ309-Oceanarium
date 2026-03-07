<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  filters: { type: Object, required: true },
  resources: { type: Array, required: true },
  statuses: { type: Array, required: true },
  eventTypes: { type: Array, required: true },
})

const emit = defineEmits(['update'])

const local = reactive({
  userIds: props.filters.userIds || [],
  teamIds: props.filters.teamIds || [],
  statuses: props.filters.statuses || [],
  eventTypes: props.filters.eventTypes || [],
  conflictsOnly: props.filters.conflictsOnly || false,
  search: props.filters.search || '',
})

watch(
  () => ({ ...local }),
  (value) => {
    emit('update', value)
  },
  { deep: true },
)
</script>

<template>
  <div class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500 space-y-3">
    <h3 class="text-sm font-semibold text-gray-700">Filters</h3>

    <input
      v-model="local.search"
      type="text"
      placeholder="Search events"
      class="w-full border border-gray-300 rounded px-3 py-2 text-sm"
    />

    <select v-model="local.statuses" multiple class="w-full border border-gray-300 rounded px-3 py-2 text-sm min-h-[90px]">
      <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
    </select>

    <select
      v-model="local.eventTypes"
      multiple
      class="w-full border border-gray-300 rounded px-3 py-2 text-sm min-h-[90px]"
    >
      <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
    </select>

    <label class="flex items-center gap-2 text-sm text-gray-700">
      <input v-model="local.conflictsOnly" type="checkbox" />
      Show conflicts only
    </label>
  </div>
</template>

