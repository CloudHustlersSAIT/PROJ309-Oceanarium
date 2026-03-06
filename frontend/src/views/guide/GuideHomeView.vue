<template>
  <div class="app-page-wrap pt-1">
    <!-- Hero Card -->
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-col gap-1">
        <h1 class="app-title">Welcome, Guide</h1>
        <p class="app-subtitle">Here's your next scheduled tour.</p>
      </div>

      <div class="notification-card-unread mt-4 min-h-[112px] p-4">
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
      <div class="mt-5 flex flex-wrap gap-2 rounded-xl border border-black/10 bg-white p-1">
        <RouterLink
          to="/guide/schedule"
          class="app-action-btn rounded-lg"
          :class="tabClass('/guide/schedule')"
        >
          My Schedule
        </RouterLink>

        <RouterLink
          to="/guide/requests"
          class="app-action-btn rounded-lg"
          :class="tabClass('/guide/requests')"
        >
          Swap Requests
        </RouterLink>

        <RouterLink
          to="/guide/notifications"
          class="app-action-btn rounded-lg"
          :class="tabClass('/guide/notifications')"
        >
          Notifications
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
          <span class="inline-flex rounded-full bg-[#E63946]/10 px-3 py-1 text-xs font-semibold text-[#E63946]">
            Action Required
          </span>
        </div>
      </div>

      <div class="app-surface-card p-5">
        <p class="app-subtitle">Avg Rating</p>
        <p class="mt-2 text-3xl font-semibold text-[#1C1C1C]">{{ stats.avgRating }}</p>
        <p class="app-subtitle">last 30 days</p>

        <div class="mt-3">
          <span class="inline-flex rounded-full bg-[#2A9D8F]/10 px-3 py-1 text-xs font-semibold text-[#2A9D8F]">
            Good Standing
          </span>
        </div>
      </div>
    </section>

    <!-- Quick List -->
    <section class="app-surface-card app-section-padding">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-[#1C1C1C]">Today</h2>
        <RouterLink to="/guide/schedule" class="text-sm font-semibold text-[#0077B6] hover:text-[#0097E7]">
          View full schedule ->
        </RouterLink>
      </div>

      <div class="mt-4 space-y-3">
        <div
          v-for="e in todayEvents"
          :key="e.id"
          class="notification-card flex items-start justify-between gap-4 p-4"
        >
          <div class="flex gap-3">
            <div class="mt-1 h-3 w-3 rounded-full bg-[#00B4D8]"></div>
            <div>
              <p class="app-body-title">{{ e.title }}</p>
              <p class="app-subtitle">{{ e.time }} • {{ e.language }}</p>
            </div>
          </div>

          <span class="text-xs font-semibold text-black/60">{{ e.status }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRoute } from "vue-router";

const route = useRoute();

function tabClass(path) {
  const active = route.path === path;
  return active
    ? "bg-[#CAF0F8] text-[#1C1C1C] ring-1 ring-[#00B4D8]/30 shadow-sm"
    : "border border-black/15 text-[#1C1C1C] hover:text-[#005A8A] hover:bg-[#CAF0F8]/40";
}

const nextEvent = {
  title: "Dolphin Feeding Experience",
  date: "Feb 18, 2026",
  time: "2:00 PM - 3:00 PM",
  language: "English",
  guests: 18,
};

const stats = {
  weekTours: 6,
  pendingRequests: 2,
  avgRating: 4.7,
};

const todayEvents = [
  { id: 1, title: "Dolphin Feeding Experience", time: "2:00-3:00 PM", language: "EN", status: "Scheduled" },
  { id: 2, title: "Reef Discovery", time: "4:00-5:00 PM", language: "FR", status: "Scheduled" },
];
</script>


