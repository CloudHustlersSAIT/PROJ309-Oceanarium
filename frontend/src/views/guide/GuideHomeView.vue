<template>
  <div class="app-page-wrap pt-1">
    <!-- Hero Card -->
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-col gap-1">
        <h1 class="app-title">Welcome, Guide</h1>
        <p class="app-subtitle">Here's your next scheduled tour.</p>
      </div>

      <div class="mt-4 min-h-[112px] rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4">
        <div class="flex flex-wrap items-center justify-between gap-2">
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
            class="inline-flex items-center rounded-full bg-white px-2.5 py-0.5 text-xs font-semibold text-[#0077B6] ring-1 ring-[#00B4D8]/30"
          >
            Next Up
          </span>
        </div>
      </div>

      <!-- Actions -->
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

    <!-- Stats -->
    <section class="grid gap-4 md:grid-cols-3">
      <div class="app-surface-card p-5">
        <p class="app-subtitle">This Week</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C]">{{ stats.weekTours }}</p>
        <p class="app-subtitle">tours assigned</p>
      </div>

      <div class="app-surface-card p-5">
        <p class="app-subtitle">Pending Requests</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C]">{{ stats.pendingRequests }}</p>
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
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C]">{{ stats.avgRating }}</p>
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

    <!-- Quick List -->
    <section class="app-surface-card app-section-padding">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-[#1C1C1C]">Today</h2>
        <RouterLink
          to="/guide/schedule"
          class="text-sm font-semibold text-[#0077B6] hover:text-[#0097E7]"
        >
          View full schedule ->
        </RouterLink>
      </div>

      <div class="mt-4 space-y-3">
        <div
          v-for="e in todayEvents"
          :key="e.id"
          class="flex items-center justify-between gap-4 rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4"
        >
          <div class="flex items-center gap-3">
            <div class="h-3 w-3 shrink-0 rounded-full bg-[#00B4D8]"></div>
            <div>
              <p class="app-body-title">{{ e.title }}</p>
              <p class="app-subtitle">{{ e.time }} • {{ e.language }}</p>
            </div>
          </div>

          <span
            class="inline-flex items-center rounded-full border border-[#7DB8CC] bg-white/70 px-3 py-1 text-sm font-semibold text-black"
          >
            {{ e.status }}
          </span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

function tabClass(path) {
  const active = route.path === path
  return active
    ? 'border border-[#0077B6] bg-[#0077B6] text-white shadow-[0_8px_18px_rgba(0,119,182,0.24)]'
    : 'border border-[#0077B6] bg-[#0077B6] text-white shadow-[0_6px_14px_rgba(0,119,182,0.2)] hover:bg-[#0097E7] hover:border-[#0097E7] hover:shadow-[0_10px_20px_rgba(0,119,182,0.28)]'
}

const nextEvent = {
  title: 'Dolphin Feeding Experience',
  date: 'Feb 18, 2026',
  time: '2:00 PM - 3:00 PM',
  language: 'English',
  guests: 18,
}

const stats = {
  weekTours: 6,
  pendingRequests: 2,
  avgRating: 4.7,
}

const todayEvents = [
  {
    id: 1,
    title: 'Dolphin Feeding Experience',
    time: '2:00-3:00 PM',
    language: 'EN',
    status: 'Scheduled',
  },
  { id: 2, title: 'Reef Discovery', time: '4:00-5:00 PM', language: 'FR', status: 'Scheduled' },
]
</script>
