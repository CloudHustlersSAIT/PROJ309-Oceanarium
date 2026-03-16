<script setup>
import { computed } from 'vue'
import PrimaryCreateButton from '../PrimaryCreateButton.vue'

const props = defineProps({
  currentView: { type: String, required: true },
  selectedDate: { type: Date, required: true },
})

const emit = defineEmits(['change-view', 'export', 'primary-create'])

const dateRange = computed(() => {
  if (props.currentView === 'day') {
    return props.selectedDate.toLocaleDateString('en-CA', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  if (props.currentView === 'week') {
    const start = new Date(props.selectedDate)
    start.setDate(start.getDate() - start.getDay())
    const end = new Date(start)
    end.setDate(end.getDate() + 6)

    const startLabel = start.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })
    const endLabel = end.toLocaleDateString('en-CA', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
    return `${startLabel} - ${endLabel}`
  }

  return props.selectedDate.toLocaleDateString('en-CA', {
    month: 'long',
    year: 'numeric',
  })
})
</script>

<template>
  <section class="rounded-xl border border-blue-500 bg-white p-4 shadow-md dark:border-sky-700/40 dark:bg-[#161B27] dark:shadow-black/30">
    <div class="grid grid-cols-1 gap-3 xl:grid-cols-[1fr_auto_1fr] xl:items-center">
      <div class="xl:justify-self-start">
        <h1 class="text-3xl font-bold text-gray-800 dark:text-slate-100">Calendar</h1>
      </div>

      <div class="text-center text-3xl font-bold text-gray-800 dark:text-slate-100">{{ dateRange }}</div>

      <div class="xl:justify-self-end">
        <PrimaryCreateButton @create="emit('primary-create')" />
      </div>
    </div>

    <div class="mt-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
      <div class="flex items-center gap-2 flex-wrap">
        <button
          class="px-3 py-1.5 rounded border"
          :class="
            currentView === 'month'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-[#ACBAC4] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300'
          "
          @click="emit('change-view', 'month')"
        >
          Month
        </button>
        <button
          class="px-3 py-1.5 rounded border"
          :class="
            currentView === 'week'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-[#ACBAC4] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300'
          "
          @click="emit('change-view', 'week')"
        >
          Week
        </button>
        <button
          class="px-3 py-1.5 rounded border"
          :class="
            currentView === 'day'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-[#ACBAC4] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300'
          "
          @click="emit('change-view', 'day')"
        >
          Day
        </button>
      </div>

      <div class="flex items-center gap-2 flex-wrap xl:justify-end">
        <button
          class="rounded border border-[#ACBAC4] bg-white px-3 py-1.5 text-gray-700 hover:bg-gray-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
          @click="emit('export')"
        >
          Export
        </button>
      </div>
    </div>
  </section>
</template>
