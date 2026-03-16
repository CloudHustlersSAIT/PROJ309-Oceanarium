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
  <div class="space-y-3 rounded-xl border border-blue-500 bg-white p-4 shadow-md dark:border-sky-700/40 dark:bg-[#161B27] dark:shadow-black/30">
    <h3 class="text-sm font-semibold text-gray-700 dark:text-slate-100">Filters</h3>

    <input
      v-model="local.search"
      type="text"
      placeholder="Search events"
      class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500"
    />

    <select
      v-model="local.statuses"
      multiple
      class="min-h-[90px] w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
    >
      <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
    </select>

    <select
      v-model="local.eventTypes"
      multiple
      class="min-h-[90px] w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
    >
      <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
    </select>

    <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-300">
      <input v-model="local.conflictsOnly" type="checkbox" />
      Show conflicts only
    </label>
  </div>
</template>
