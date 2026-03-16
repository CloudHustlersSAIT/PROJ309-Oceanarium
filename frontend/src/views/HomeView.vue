<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSchedules, getStats } from '../services/api'
import { useAuth } from '../contexts/authContext'
import AppSidebar from '../components/AppSidebar.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import { formatScheduleTimeForDisplay, formatStatusLabel } from '../utils/reservation'

const router = useRouter()
const { user } = useAuth()

const allDayScheduleRows = ref([])
const alerts = ref([])
const recentActivity = ref([])
const scheduleModalOpen = ref(false)
const scheduleLoadWarning = ref('')
const scheduleSectionLoading = ref(true)

const greetingByTimeOfDay = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good Morning'
  if (hour < 18) return 'Good Afternoon'
  return 'Good Evening'
})

const emailFirstName = computed(() => {
  const email = String(user.value?.email || '')
    .trim()
    .toLowerCase()
  if (!email || !email.includes('@')) return ''

  const localPart = email.split('@')[0] || ''
  const firstToken = localPart.split(/[._-]+/).find(Boolean) || ''
  if (!firstToken) return ''

  return firstToken.charAt(0).toUpperCase() + firstToken.slice(1)
})

const homeGreeting = computed(() => {
  return emailFirstName.value
    ? `${greetingByTimeOfDay.value}, ${emailFirstName.value}`
    : greetingByTimeOfDay.value
})

const visibleScheduleRows = computed(() => allDayScheduleRows.value.slice(0, 5))
const hasMoreSchedules = computed(() => allDayScheduleRows.value.length > 5)

function getTodayIsoDate() {
  const now = new Date()
  const year = String(now.getFullYear())
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getTodayUtcIsoDate() {
  const now = new Date()
  const year = String(now.getUTCFullYear())
  const month = String(now.getUTCMonth() + 1).padStart(2, '0')
  const day = String(now.getUTCDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getStatusTone(status) {
  const normalized = String(status || '')
    .trim()
    .toLowerCase()
  if (normalized === 'cancelled' || normalized === 'overbooked') {
    return 'bg-red-50 text-red-700 border-red-200 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
  }
  if (normalized === 'delay' || normalized === 'delayed') {
    return 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
  }
  return 'bg-green-50 text-green-700 border-green-200 dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300'
}

function buildScheduleRowsFromApi(schedules) {
  return schedules.map((schedule, index) => ({
    id: schedule?.id ?? `schedule-${index}`,
    time: formatScheduleTimeForDisplay(schedule?.event_start_datetime, { style: 'us' }),
    guide: schedule?.guide_name || 'Unassigned',
    tour: schedule?.tour_name || `Tour ${schedule?.tour_id ?? '-'}`,
    status: formatStatusLabel(schedule?.status, 'Scheduled'),
    tone: getStatusTone(schedule?.status),
  }))
}

function isActiveScheduleStatus(status) {
  const normalized = String(status || '')
    .trim()
    .toLowerCase()
  return normalized !== 'cancelled' && normalized !== 'completed'
}

function sortByStartDateTimeAsc(a, b) {
  const aRaw = String(a?.event_start_datetime || '').trim()
  const bRaw = String(b?.event_start_datetime || '').trim()

  const aMatch = aRaw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/)
  const bMatch = bRaw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/)

  if (aMatch && bMatch) {
    const aKey = `${aMatch[1]}${aMatch[2]}${aMatch[3]}${aMatch[4]}${aMatch[5]}`
    const bKey = `${bMatch[1]}${bMatch[2]}${bMatch[3]}${bMatch[4]}${bMatch[5]}`
    if (aKey !== bKey) return aKey.localeCompare(bKey)
  }

  const aId = Number(a?.id)
  const bId = Number(b?.id)
  if (Number.isInteger(aId) && Number.isInteger(bId)) return aId - bId

  return String(a?.tour_name || '').localeCompare(String(b?.tour_name || ''))
}

async function loadHomeData() {
  scheduleSectionLoading.value = true
  try {
    const localToday = getTodayIsoDate()
    const utcToday = getTodayUtcIsoDate()
    scheduleLoadWarning.value = ''

    const [statsResult, schedulesResult] = await Promise.allSettled([
      getStats(),
      getSchedules({ startDate: localToday, endDate: localToday }),
    ])

    let todaySchedules =
      schedulesResult.status === 'fulfilled' && Array.isArray(schedulesResult.value)
        ? schedulesResult.value
        : null

    // Around midnight in different timezones, a UTC-based date may reflect the intended "today" on the server.
    if (Array.isArray(todaySchedules) && todaySchedules.length === 0 && utcToday !== localToday) {
      try {
        const utcSchedules = await getSchedules({ startDate: utcToday, endDate: utcToday })
        if (Array.isArray(utcSchedules) && utcSchedules.length > 0) {
          todaySchedules = utcSchedules
        }
      } catch {
        // Keep primary result; warning handling below will inform user on schedule API failures.
      }
    }

    const schedulesForCard = Array.isArray(todaySchedules)
      ? todaySchedules
          .filter((schedule) => isActiveScheduleStatus(schedule?.status))
          .sort(sortByStartDateTimeAsc)
      : null

    if (Array.isArray(schedulesForCard)) {
      allDayScheduleRows.value = buildScheduleRowsFromApi(schedulesForCard)
    } else {
      allDayScheduleRows.value = []
    }

    const statsResponse = statsResult.status === 'fulfilled' ? statsResult.value : null
    const totalEventsToday = Array.isArray(todaySchedules) ? todaySchedules.length : 'Unavailable'
    if (statsResponse) {
      const toursToday = Number(statsResponse?.toursToday) || 0
      const customersToday = Number(statsResponse?.customersToday) || 0
      const cancellations = Number(statsResponse?.cancellations) || 0

      const computedAlerts = []
      if (Array.isArray(todaySchedules) && todaySchedules.length === 0) {
        computedAlerts.push('No tours scheduled for today')
      }
      if (cancellations > 0) computedAlerts.push(`${cancellations} cancellation(s) recorded today`)

      const delayedCount = Array.isArray(todaySchedules)
        ? todaySchedules.filter((schedule) => {
            const status = String(schedule?.status || '')
              .trim()
              .toLowerCase()
            return status === 'delay' || status === 'delayed'
          }).length
        : 0

      if (delayedCount > 0) computedAlerts.push(`${delayedCount} schedule(s) delayed`)
      if (computedAlerts.length === 0) computedAlerts.push('No critical alerts at the moment')

      alerts.value = computedAlerts
      recentActivity.value = [
        { metric: 'Total Events', value: totalEventsToday },
        { metric: 'Reservations', value: toursToday },
        { metric: 'Tickets Assigned', value: customersToday },
        { metric: 'Cancellations', value: cancellations },
      ]
    } else {
      alerts.value = ['Live stats unavailable right now']
      recentActivity.value = [
        { metric: 'Total Events', value: totalEventsToday },
        { metric: 'Status', value: 'Unavailable' },
      ]
    }

    if (statsResult.status === 'rejected' || schedulesResult.status === 'rejected') {
      console.error('Home data partial load failed', {
        statsError: statsResult.status === 'rejected' ? statsResult.reason : null,
        schedulesError: schedulesResult.status === 'rejected' ? schedulesResult.reason : null,
      })

      if (schedulesResult.status === 'rejected') {
        scheduleLoadWarning.value = "Unable to load today's schedules right now."
      }
    }
  } finally {
    scheduleSectionLoading.value = false
  }
}

function goToBookings() {
  router.push({ name: 'bookings' })
}

function goToCalendar() {
  router.push({ name: 'calendar' })
}

function goToDashboard() {
  router.push({ name: 'dashboard' })
}

function goToNotifications() {
  router.push({ name: 'notifications' })
}

function openScheduleModal() {
  scheduleModalOpen.value = true
}

function closeScheduleModal() {
  scheduleModalOpen.value = false
}

onMounted(loadHomeData)
</script>

<template>
  <div class="flex min-h-screen overflow-x-hidden bg-[#F3F5F8] dark:bg-[#0F1117]">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 xl:p-8">
      <header class="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">{{ homeGreeting }}</h1>
          <p class="mt-1 text-base text-slate-600 dark:text-slate-400">Today's Operations Overview</p>
        </div>

        <ThemeToggle icon-only />
      </header>

      <section class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-5 items-start">
        <article
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30 lg:col-span-2 2xl:col-span-1"
        >
          <h2 class="mb-2 text-xl font-semibold text-slate-800 dark:text-slate-100">Today's Schedule</h2>
          <p v-if="scheduleLoadWarning" class="mb-2 text-xs text-amber-700 dark:text-amber-300">
            {{ scheduleLoadWarning }}
          </p>
          <ul class="mt-2 space-y-2">
            <li
              v-for="row in visibleScheduleRows"
              :key="row.id"
              class="flex flex-col items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-[#1A2231] sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {{ row.time }} - Guide: {{ row.guide }}
                </p>
                <p class="text-sm text-slate-600 dark:text-slate-400">{{ row.tour }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs font-semibold" :class="row.tone">{{
                row.status
              }}</span>
            </li>
            <li
              v-if="scheduleSectionLoading"
              class="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm text-slate-600 dark:border-white/15 dark:bg-[#1A2231] dark:text-slate-400"
            >
              Loading today's schedule...
            </li>
            <li
              v-else-if="!visibleScheduleRows.length"
              class="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm text-slate-600 dark:border-white/15 dark:bg-[#1A2231] dark:text-slate-400"
            >
              No schedules for today.
            </li>
          </ul>
          <button
            v-if="hasMoreSchedules"
            type="button"
            class="mt-3 rounded text-xs font-semibold text-blue-600 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 dark:text-sky-300 dark:hover:text-sky-200"
            @click="openScheduleModal"
          >
            View More
          </button>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
          <h2 class="mb-2 text-xl font-semibold text-slate-800 dark:text-slate-100">Alerts</h2>
          <ul class="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
            <li v-for="alert in alerts" :key="alert" class="flex items-center gap-2">
              <span
                class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-yellow-100 text-yellow-600 dark:bg-yellow-950/60 dark:text-yellow-300"
                >!</span
              >
              <span>{{ alert }}</span>
            </li>
            <li v-if="!alerts.length" class="text-slate-600 dark:text-slate-400">No alerts available.</li>
          </ul>
          <button
            type="button"
            class="mt-3 rounded text-xs font-semibold text-blue-600 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 dark:text-sky-300 dark:hover:text-sky-200"
            @click="goToNotifications"
          >
            View Details
          </button>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
          <h2 class="mb-2 text-xl font-semibold text-slate-800 dark:text-slate-100">Today's Activity</h2>
          <ul class="mt-2 space-y-2">
            <li
              v-for="item in recentActivity"
              :key="`${item.metric}-${item.value}`"
              class="border-b border-slate-200 pb-2 last:border-b-0 last:pb-0 dark:border-white/10"
            >
              <span class="text-xs uppercase tracking-wide text-gray-500 dark:text-slate-500">{{ item.metric }}</span>
              <span class="ml-2 text-sm font-semibold text-slate-800 dark:text-slate-100">{{ item.value }}</span>
            </li>
            <li v-if="!recentActivity.length" class="text-sm text-slate-600 dark:text-slate-400">
              No recent activity available.
            </li>
          </ul>
        </article>
      </section>

      <section class="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
        <h2 class="mb-2 text-xl font-semibold text-slate-800 dark:text-slate-100">Quick Actions</h2>
        <div class="mt-2 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2">
          <button
            type="button"
            class="w-full py-2 rounded-lg bg-yellow-400 text-black font-semibold shadow hover:bg-yellow-500 transition"
            @click="goToBookings"
          >
            + Add Booking
          </button>
          <button
            type="button"
            class="w-full py-2 rounded-lg bg-blue-600 text-white font-semibold shadow hover:bg-blue-700 transition"
            @click="goToCalendar"
          >
            Reschedule Tour
          </button>
          <button
            type="button"
            class="w-full py-2 rounded-lg bg-green-600 text-white font-semibold shadow hover:bg-green-700 transition sm:col-span-2 xl:col-span-1"
            @click="goToDashboard"
          >
            View Guides
          </button>
        </div>
      </section>

      <div
        v-if="scheduleModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4"
        @click.self="closeScheduleModal"
      >
        <section
          class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
        >
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-100">All Schedules for Today</h3>
            <button
              type="button"
              class="rounded px-2 py-1 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/5"
              @click="closeScheduleModal"
            >
              Close
            </button>
          </div>

          <ul class="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
            <li
              v-for="row in allDayScheduleRows"
              :key="`modal-${row.id}`"
              class="flex flex-col items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-[#1A2231] sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {{ row.time }} - Guide: {{ row.guide }}
                </p>
                <p class="text-sm text-slate-600 dark:text-slate-400">{{ row.tour }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs font-semibold" :class="row.tone">{{
                row.status
              }}</span>
            </li>
          </ul>
        </section>
      </div>
    </main>
  </div>
</template>
