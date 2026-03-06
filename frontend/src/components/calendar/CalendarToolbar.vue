<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentView: { type: String, required: true },
  selectedDate: { type: Date, required: true },
})

const emit = defineEmits(['change-view', 'export'])

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
    const endLabel = end.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })
    return `${startLabel} - ${endLabel}`
  }

  return props.selectedDate.toLocaleDateString('en-CA', {
    month: 'long',
    year: 'numeric',
  })
})
</script>

<template>
  <section class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500">
    <div class="grid grid-cols-1 gap-3 xl:grid-cols-[1fr_auto_1fr] xl:items-center">
      <div class="xl:justify-self-start">
        <h1 class="text-3xl font-bold text-gray-800">Calendar</h1>
      </div>

      <div class="text-3xl font-bold text-gray-800 text-center">{{ dateRange }}</div>

      <div class="xl:justify-self-end" />
    </div>

    <div class="mt-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
      <div class="flex items-center gap-2 flex-wrap">
        <button
          class="px-3 py-1.5 rounded border"
          :class="currentView === 'month' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-[#ACBAC4]'"
          @click="emit('change-view', 'month')"
        >
          Month
        </button>
        <button
          class="px-3 py-1.5 rounded border"
          :class="currentView === 'week' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-[#ACBAC4]'"
          @click="emit('change-view', 'week')"
        >
          Week
        </button>
        <button
          class="px-3 py-1.5 rounded border"
          :class="currentView === 'day' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-[#ACBAC4]'"
          @click="emit('change-view', 'day')"
        >
          Day
        </button>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <button
          class="px-3 py-1.5 rounded border bg-white text-gray-700 border-[#ACBAC4] hover:bg-gray-50"
          @click="emit('export')"
        >
          Export
        </button>
      </div>
    </div>
  </section>
</template>

