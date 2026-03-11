<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  event: { type: Object, default: null },
  resources: { type: Array, required: true },
})

const emit = defineEmits(['save', 'duplicate', 'delete'])

const form = reactive({
  id: '',
  title: '',
  startDate: '',
  startHour: '09',
  startMinute: '00',
  startPeriod: 'AM',
  endDate: '',
  endHour: '10',
  endMinute: '00',
  endPeriod: 'AM',
  resourceId: '',
  status: 'scheduled',
  type: 'tour',
  priority: 'medium',
  notes: '',
})

const hourOptions = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
const minuteOptions = ['00', '15', '30', '45']
const periodOptions = ['AM', 'PM']

function toFormParts(dateLike) {
  const d = new Date(dateLike)
  const date = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const hour24 = d.getHours()
  const hour12 = hour24 % 12 || 12
  const minute = Math.round(d.getMinutes() / 15) * 15
  const normalizedMinute = minute === 60 ? 45 : minute

  return {
    date,
    hour: String(hour12).padStart(2, '0'),
    minute: String(normalizedMinute).padStart(2, '0'),
    period: hour24 >= 12 ? 'PM' : 'AM',
  }
}

function toIsoFromParts(date, hour, minute, period) {
  const [year, month, day] = date.split('-').map(Number)
  const rawHour = Number(hour)
  let hour24 = rawHour % 12
  if (period === 'PM') hour24 += 12

  const local = new Date(year, month - 1, day, hour24, Number(minute), 0, 0)
  return local.toISOString()
}

watch(
  () => props.event,
  (value) => {
    if (!value) return
    const start = toFormParts(value.start)
    const end = toFormParts(value.end)

    form.id = value.id
    form.title = value.title
    form.startDate = start.date
    form.startHour = start.hour
    form.startMinute = start.minute
    form.startPeriod = start.period
    form.endDate = end.date
    form.endHour = end.hour
    form.endMinute = end.minute
    form.endPeriod = end.period
    form.resourceId = value.resourceId
    form.status = value.status
    form.type = value.type
    form.priority = value.priority
    form.notes = value.notes || ''
  },
  { immediate: true },
)

function save() {
  emit('save', {
    ...props.event,
    ...form,
    start: toIsoFromParts(form.startDate, form.startHour, form.startMinute, form.startPeriod),
    end: toIsoFromParts(form.endDate, form.endHour, form.endMinute, form.endPeriod),
  })
}
</script>

<template>
  <aside class="bg-white rounded-xl shadow-md p-4 border-1 border-blue-500 h-full">
    <h3 class="text-lg font-semibold text-gray-800 mb-3">Event Details</h3>

    <div v-if="!event" class="text-sm text-gray-500">Select an event to edit details.</div>

    <div v-else class="space-y-3">
      <input
        v-model="form.title"
        class="w-full border border-[#ACBAC4] rounded px-3 py-2 text-sm"
        placeholder="Title"
      />

      <div class="grid grid-cols-1 gap-3">
        <div>
          <label class="text-xs text-gray-600 block mb-1">Start</label>
          <div class="grid grid-cols-[1fr_72px_72px_72px] gap-2">
            <input
              v-model="form.startDate"
              type="date"
              class="border border-[#ACBAC4] rounded px-3 py-2 text-sm"
            />
            <select
              v-model="form.startHour"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option v-for="hour in hourOptions" :key="`start-hour-${hour}`" :value="hour">
                {{ hour }}
              </option>
            </select>
            <select
              v-model="form.startMinute"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option
                v-for="minute in minuteOptions"
                :key="`start-minute-${minute}`"
                :value="minute"
              >
                {{ minute }}
              </option>
            </select>
            <select
              v-model="form.startPeriod"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option
                v-for="period in periodOptions"
                :key="`start-period-${period}`"
                :value="period"
              >
                {{ period.toLowerCase() }}
              </option>
            </select>
          </div>
        </div>

        <div>
          <label class="text-xs text-gray-600 block mb-1">End</label>
          <div class="grid grid-cols-[1fr_72px_72px_72px] gap-2">
            <input
              v-model="form.endDate"
              type="date"
              class="border border-[#ACBAC4] rounded px-3 py-2 text-sm"
            />
            <select
              v-model="form.endHour"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option v-for="hour in hourOptions" :key="`end-hour-${hour}`" :value="hour">
                {{ hour }}
              </option>
            </select>
            <select
              v-model="form.endMinute"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option v-for="minute in minuteOptions" :key="`end-minute-${minute}`" :value="minute">
                {{ minute }}
              </option>
            </select>
            <select
              v-model="form.endPeriod"
              class="border border-[#ACBAC4] rounded px-2 py-2 text-sm"
            >
              <option v-for="period in periodOptions" :key="`end-period-${period}`" :value="period">
                {{ period.toLowerCase() }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <select
        v-model="form.resourceId"
        class="w-full border border-[#ACBAC4] rounded px-3 py-2 text-sm"
      >
        <option v-for="resource in resources" :key="resource.id" :value="resource.id">
          {{ resource.name }}
        </option>
      </select>

      <div class="grid grid-cols-2 gap-2">
        <select v-model="form.status" class="border border-[#ACBAC4] rounded px-3 py-2 text-sm">
          <option value="scheduled">scheduled</option>
          <option value="confirmed">confirmed</option>
          <option value="pending">pending</option>
          <option value="cancelled">cancelled</option>
        </select>
        <select v-model="form.priority" class="border border-[#ACBAC4] rounded px-3 py-2 text-sm">
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </div>

      <textarea
        v-model="form.notes"
        rows="4"
        class="w-full border border-[#ACBAC4] rounded px-3 py-2 text-sm"
        placeholder="Notes"
      />

      <div class="flex items-center gap-2 pt-2">
        <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded" @click="save">
          Save
        </button>
        <button
          class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
          @click="emit('duplicate', event.id)"
        >
          Duplicate
        </button>
        <button
          class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
          @click="emit('delete', event.id)"
        >
          Delete
        </button>
      </div>
    </div>
  </aside>
</template>
