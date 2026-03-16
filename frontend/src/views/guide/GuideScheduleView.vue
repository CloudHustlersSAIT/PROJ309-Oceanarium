<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-3 sm:items-center">
        <div>
          <h1 class="app-title">My Schedule</h1>
          <p class="app-subtitle">Weekly overview of assigned tours</p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button
            class="app-action-btn border border-black/10 text-[#1C1C1C] hover:bg-[#CAF0F8]/50 dark:border-white/10 dark:text-slate-200 dark:hover:bg-white/5"
            :disabled="loading"
            @click="prevWeek"
          >
            &lt;- Prev
          </button>

          <span
            class="app-action-btn inline-flex items-center border border-[#0077B6]/20 bg-[#EAF6FD] text-[#005A8A] dark:border-sky-700/40 dark:bg-sky-950/50 dark:text-sky-200"
          >
            {{ weekLabel }}
          </span>

          <button
            class="app-action-btn border border-black/10 text-[#1C1C1C] hover:bg-[#CAF0F8]/50 dark:border-white/10 dark:text-slate-200 dark:hover:bg-white/5"
            :disabled="loading"
            @click="nextWeek"
          >
            Next ->
          </button>
        </div>
      </div>

      <div class="mt-5 space-y-3">
        <div v-if="loading" class="text-sm text-black/60 dark:text-slate-400">Loading schedule...</div>
        <div v-else-if="error" class="text-sm font-medium text-[#B91C1C]">{{ error }}</div>

        <div v-for="event in events" :key="event.id" class="notification-card p-3.5 sm:p-4">
          <div class="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="app-body-title">
                {{ event.title }}
              </p>
              <p class="app-body-meta">
                {{ event.date }} • {{ event.time }} • {{ event.language }}
              </p>
            </div>

            <span
              class="px-3 py-1 text-xs rounded-full bg-[#00B4D8]/10 text-[#0077B6] font-semibold"
            >
              {{ event.status }}
            </span>
          </div>
        </div>

        <div v-if="!loading && !error && events.length === 0" class="text-sm text-black/60 dark:text-slate-400">
          No tours scheduled for this week.
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useAuth } from '@/contexts/authContext'
import { getSchedules } from '@/services/api'

const { profile, ensureAuthReady } = useAuth()

const weekOffset = ref(0)
const events = ref([])
const loading = ref(false)
const error = ref('')

const currentGuideId = computed(() => Number(profile.value?.guide_id ?? 0) || null)

function getWeekRange(offset = 0) {
  const now = new Date()
  const reference = new Date(now)
  reference.setHours(0, 0, 0, 0)
  reference.setDate(reference.getDate() + offset * 7)

  const day = reference.getDay()
  const mondayShift = day === 0 ? -6 : 1 - day
  const start = new Date(reference)
  start.setDate(reference.getDate() + mondayShift)

  const end = new Date(start)
  end.setDate(start.getDate() + 6)

  return { start, end }
}

function formatIsoDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatLanguage(code) {
  const normalized = String(code || '').trim().toLowerCase()
  const labels = { en: 'EN', fr: 'FR', es: 'ES', pt: 'PT', zh: 'ZH' }
  return labels[normalized] || String(code || '-').toUpperCase()
}

function formatStatus(status) {
  return String(status || 'Scheduled')
    .trim()
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function normalizeScheduleEvent(schedule) {
  const start = new Date(schedule?.event_start_datetime)
  const end = new Date(schedule?.event_end_datetime)

  return {
    id: Number(schedule?.id),
    title: String(schedule?.tour_name || `Schedule ${schedule?.id ?? ''}`).trim(),
    date: Number.isNaN(start.getTime())
      ? '-'
      : start.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }),
    time:
      Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())
        ? '-'
        : `${start.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}-${end.toLocaleTimeString(undefined, {
            hour: 'numeric',
            minute: '2-digit',
          })}`,
    language: formatLanguage(schedule?.language_code),
    status: formatStatus(schedule?.status),
    startMs: Number.isNaN(start.getTime()) ? Number.POSITIVE_INFINITY : start.getTime(),
  }
}

const weekRange = computed(() => getWeekRange(weekOffset.value))

const weekLabel = computed(() => {
  const { start, end } = weekRange.value
  const startLabel = start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  const endLabel = end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  return `${startLabel} - ${endLabel}`
})

async function loadSchedule() {
  if (!currentGuideId.value) {
    events.value = []
    error.value = 'Guide profile is not available.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const { start, end } = weekRange.value
    const schedules = await getSchedules({
      startDate: formatIsoDate(start),
      endDate: formatIsoDate(end),
      guideId: currentGuideId.value,
    })

    events.value = (Array.isArray(schedules) ? schedules : [])
      .map(normalizeScheduleEvent)
      .sort((left, right) => left.startMs - right.startMs)
  } catch (loadError) {
    events.value = []
    error.value = loadError?.message || 'Failed to load guide schedule.'
  } finally {
    loading.value = false
  }
}

function prevWeek() {
  weekOffset.value--
}

function nextWeek() {
  weekOffset.value++
}

watch(weekOffset, () => {
  loadSchedule()
})

watch(currentGuideId, () => {
  loadSchedule()
})

onMounted(async () => {
  await ensureAuthReady()
  await loadSchedule()
})
</script>
