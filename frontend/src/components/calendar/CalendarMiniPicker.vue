<script setup>
import { computed } from 'vue'

const props = defineProps({
  selectedDate: { type: Date, required: true },
})

const emit = defineEmits(['select-date'])

const monthLabel = computed(() =>
  props.selectedDate.toLocaleDateString('en-CA', { month: 'long', year: 'numeric' }),
)

const monthDays = computed(() => {
  const first = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth(), 1)
  const last = new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth() + 1, 0)

  const days = []
  for (let i = 0; i < first.getDay(); i += 1) days.push(null)
  for (let d = 1; d <= last.getDate(); d += 1) {
    days.push(new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth(), d))
  }
  return days
})

function sameDate(a, b) {
  return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">{{ monthLabel }}</h3>
    <div class="grid grid-cols-7 gap-1 text-xs">
      <div v-for="day in ['S', 'M', 'T', 'W', 'T', 'F', 'S']" :key="day" class="text-center text-gray-400">{{ day }}</div>
      <button
        v-for="(day, index) in monthDays"
        :key="index"
        class="h-7 rounded"
        :class="day
          ? sameDate(day, selectedDate)
            ? 'bg-blue-600 text-white'
            : 'hover:bg-blue-100 text-gray-700'
          : 'cursor-default'"
        :disabled="!day"
        @click="day && emit('select-date', day)"
      >
        {{ day ? day.getDate() : '' }}
      </button>
    </div>
  </div>
</template>

