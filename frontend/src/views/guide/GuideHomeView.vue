<template>
  <div class="app-page-wrap pt-1">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-col gap-1">
        <h1 class="app-title">Welcome, Guide</h1>
        <p class="app-subtitle">Here's your next scheduled tour.</p>
      </div>

      <div class="mt-4 min-h-[112px] rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4 dark:border-sky-800/60 dark:bg-sky-950/50">
        <div v-if="loading" class="text-sm text-black/60 dark:text-slate-400">Loading dashboard...</div>
        <div v-else-if="error" class="text-sm font-medium text-[#B91C1C]">{{ error }}</div>
        <div v-else class="flex flex-wrap items-center justify-between gap-2">
          <div class="space-y-0.5">
            <p class="app-body-title leading-tight">
              {{ nextEvent.title }}
            </p>
            <p class="app-body-meta leading-tight">
              {{ nextEvent.date }} • {{ nextEvent.time }} • {{ nextEvent.language }}
            </p>
            <p class="app-body-meta leading-tight">Guests: {{ nextEvent.guests }}</p>
          </div>

          <span
            class="inline-flex items-center self-center rounded-full bg-white px-4 py-1.5 text-sm font-semibold text-[#0077B6] ring-1 ring-[#00B4D8]/30 dark:bg-white/10 dark:text-sky-200 dark:ring-sky-700/40"
          >
            Next Up
          </span>
        </div>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-3">
        <RouterLink
          to="/guide/schedule"
          class="inline-flex min-h-12 items-center justify-center rounded-lg px-5 py-3 text-lg font-medium transition hover:-translate-y-0.5"
          :class="tabClass('/guide/schedule')"
        >
          <span>My Schedule</span>
        </RouterLink>

        <RouterLink
          to="/guide/requests"
          class="inline-flex min-h-12 items-center justify-center rounded-lg px-5 py-3 text-lg font-medium transition hover:-translate-y-0.5"
          :class="tabClass('/guide/requests')"
        >
          <span>Swap Requests</span>
        </RouterLink>

        <RouterLink
          to="/guide/notifications"
          class="inline-flex min-h-12 items-center justify-center rounded-lg px-5 py-3 text-lg font-medium transition hover:-translate-y-0.5"
          :class="tabClass('/guide/notifications')"
        >
          <span>Notifications</span>
        </RouterLink>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <div class="app-surface-card p-5">
        <p class="app-subtitle">This Week</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C] dark:text-slate-100">{{ stats.weekTours }}</p>
        <p class="app-subtitle">tours assigned</p>
      </div>

      <div class="app-surface-card p-5">
        <p class="app-subtitle">Pending Requests</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C] dark:text-slate-100">{{ stats.pendingRequests }}</p>
        <p class="app-subtitle">need action</p>

        <div v-if="stats.pendingRequests > 0" class="mt-3">
          <span
            class="inline-flex rounded-full bg-[#E63946]/10 px-3 py-1 text-xs font-semibold text-[#E63946]"
          >
            Action Required
          </span>
        </div>
      </div>

      <div class="app-surface-card p-5">
        <p class="app-subtitle">Avg Rating</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C] dark:text-slate-100">{{ stats.avgRating }}</p>
        <p class="app-subtitle">last 30 days</p>

        <div class="mt-3">
          <span
            class="inline-flex rounded-full bg-[#2A9D8F]/10 px-3 py-1 text-xs font-semibold text-[#2A9D8F]"
          >
            Good Standing
          </span>
        </div>
      </div>
    </section>

    <section class="app-surface-card app-section-padding">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-[#1C1C1C] dark:text-slate-100">Today</h2>
        <RouterLink
          to="/guide/schedule"
          class="text-sm font-semibold text-[#0077B6] hover:text-[#0097E7]"
        >
          View full schedule ->
        </RouterLink>
      </div>

      <div class="mt-4 space-y-3">
        <div v-if="loading" class="text-sm text-black/60 dark:text-slate-400">Loading today's schedule...</div>
        <div v-else-if="!todayEvents.length" class="text-sm text-black/60 dark:text-slate-400">No tours scheduled for today.</div>

        <div
          v-for="e in todayEvents"
          :key="e.id"
          class="flex items-center justify-between gap-4 rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4 dark:border-sky-800/60 dark:bg-sky-950/40"
        >
          <div class="flex items-center gap-3">
            <div class="h-3 w-3 shrink-0 rounded-full bg-[#00B4D8]"></div>
            <div>
              <p class="app-body-title">{{ e.title }}</p>
              <p class="app-subtitle">{{ e.time }} • {{ e.language }}</p>
            </div>
          </div>

          <span
            class="inline-flex items-center rounded-full border border-[#7DB8CC] bg-white/70 px-3 py-1 text-sm font-semibold text-black dark:border-sky-700/50 dark:bg-white/10 dark:text-slate-200"
          >
            {{ e.status }}
          </span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { useAuth } from '@/contexts/authContext'
import { getGuideDashboard } from '@/services/api'

const route = useRoute()
const { profile, ensureAuthReady } = useAuth()

const loading = ref(false)
const error = ref('')
const dashboard = ref(null)

const currentGuideId = computed(() => Number(profile.value?.guide_id ?? 0) || null)

function tabClass(path) {
  const active = route.path === path
  return active
    ? 'border border-[#0077B6] bg-[#0077B6] text-white shadow-[0_8px_18px_rgba(0,119,182,0.24)]'
    : 'border border-[#0077B6] bg-[#0077B6] text-white shadow-[0_6px_14px_rgba(0,119,182,0.2)] hover:bg-[#0097E7] hover:border-[#0097E7] hover:shadow-[0_10px_20px_rgba(0,119,182,0.28)]'
}

function formatDateLabel(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No upcoming tour'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTimeLabel(startValue, endValue) {
  const startDate = new Date(startValue)
  const endDate = new Date(endValue)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return '-'

  const startLabel = startDate.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
  const endLabel = endDate.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })

  return `${startLabel} - ${endLabel}`
}

function formatLanguage(code) {
  const normalized = String(code || '').trim().toLowerCase()
  const labels = { en: 'English', fr: 'French', es: 'Spanish', pt: 'Portuguese', zh: 'Chinese' }
  return labels[normalized] || String(code || '-').toUpperCase()
}

function formatStatus(status) {
  return String(status || 'Scheduled')
    .trim()
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const nextEvent = computed(() => {
  const nextTour = dashboard.value?.next_tour
  if (!nextTour) {
    return {
      title: 'No upcoming tour',
      date: 'Check back later',
      time: '-',
      language: '-',
      guests: 0,
    }
  }

  return {
    title: String(nextTour?.tour_name || 'Upcoming tour').trim(),
    date: formatDateLabel(nextTour?.event_start_datetime),
    time: formatTimeLabel(nextTour?.event_start_datetime, nextTour?.event_end_datetime),
    language: formatLanguage(nextTour?.language_code),
    guests: Number(nextTour?.reservation_count ?? 0),
  }
})

const stats = computed(() => ({
  weekTours: Number(dashboard.value?.tours_this_week ?? 0),
  pendingRequests: Number(dashboard.value?.pending_requests ?? 0),
  avgRating: Number(dashboard.value?.rating ?? 0).toFixed(1),
}))

const todayEvents = computed(() => {
  const items = Array.isArray(dashboard.value?.today_schedule) ? dashboard.value.today_schedule : []

  return items.map((event) => ({
    id: Number(event?.id),
    title: String(event?.name || event?.tour_name || 'Scheduled Tour').trim(),
    time: formatTimeLabel(event?.event_start_datetime, event?.event_end_datetime),
    language: formatLanguage(event?.language_code),
    status: formatStatus(event?.status),
  }))
})

async function loadDashboard() {
  if (!currentGuideId.value) {
    dashboard.value = null
    error.value = 'Guide profile is not available.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    dashboard.value = await getGuideDashboard(currentGuideId.value)
  } catch (loadError) {
    dashboard.value = null
    error.value = loadError?.message || 'Failed to load guide dashboard.'
  } finally {
    loading.value = false
  }
}

watch(currentGuideId, () => {
  loadDashboard()
})

onMounted(async () => {
  await ensureAuthReady()
  await loadDashboard()
})
</script>
