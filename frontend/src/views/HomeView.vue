<script setup>
import Sidebar from '../components/Sidebar.vue'

const scheduleRows = [
  { time: '08:00', guide: 'Ana Costa', tour: 'Shark Diving', status: 'Confirmed', tone: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
  { time: '10:00', guide: 'Hermes Costello', tour: 'Dolphin Feeding', status: 'Confirmed', tone: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
  { time: '10:00', guide: 'Ann A. Kim', tour: 'Deep Sea Experience', status: 'Confirmed', tone: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
  { time: '11:00', guide: 'Chen Wei', tour: 'Molluscs', status: 'Delay', tone: 'text-amber-700 border-amber-200 bg-amber-50' },
  { time: '11:00', guide: 'Liam Brown', tour: 'History of the Ocean', status: 'Confirmed', tone: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
  { time: '13:00', guide: 'Ana Costa', tour: 'Coral Exploration', status: 'Confirmed', tone: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
  { time: '14:00', guide: 'Walter White', tour: 'Dolphin Feeding', status: 'Overbooked', tone: 'text-rose-700 border-rose-200 bg-rose-50' },
]

const alerts = [
  'Tour Dolphin Feeding is over capacity',
  'Guide David Martinez is delayed',
  '2 pending reschedules',
]

const recentActivity = [
  { time: 'Today at 13:00', text: 'Ana Costa reached 4.9' },
  { time: 'Today at 09:00', text: 'Tour for Molluscs flagged for review' },
  { time: 'Yesterday at 18:00', text: 'Tour for Whales marked delayed' },
]
</script>

<template>
  <div class="flex min-h-screen bg-[#F3F5F8] overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-6 lg:p-8">
      <header class="mb-6">
        <h1 class="text-2xl font-bold text-slate-800">Good Evening, Rogério</h1>
        <p class="mt-1 text-base text-slate-600">Today's Operations Overview</p>
      </header>

      <section class="grid grid-cols-1 xl:grid-cols-[1.2fr_0.95fr_0.85fr] gap-5 items-start">
        <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="text-xl font-semibold text-slate-800">Today's schedule</h2>
          <ul class="mt-4 space-y-3">
            <li
              v-for="row in scheduleRows"
              :key="`${row.time}-${row.guide}-${row.tour}`"
              class="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
            >
              <div>
                <p class="text-sm font-semibold text-slate-800">{{ row.time }} - Guide {{ row.guide }}</p>
                <p class="text-sm text-slate-600">{{ row.tour }}</p>
              </div>
              <span class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="row.tone">{{ row.status }}</span>
            </li>
          </ul>
        </article>

        <div class="space-y-5">

          <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="text-xl font-semibold text-slate-800">Alerts</h2>
            <ul class="mt-4 space-y-3 text-sm text-slate-700">
              <li v-for="alert in alerts" :key="alert" class="flex items-start gap-2">
                <span class="mt-0.5 text-amber-500">▲</span>
                <span>{{ alert }}</span>
              </li>
            </ul>
            <button type="button" class="mt-4 text-blue-600 text-sm font-semibold">View Details</button>
          </article>
        </div>

        <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="text-xl font-semibold text-slate-800">Recent Activity</h2>
          <ul class="mt-4 space-y-4">
            <li v-for="item in recentActivity" :key="`${item.time}-${item.text}`" class="border-b border-slate-200 pb-3 last:border-b-0 last:pb-0">
              <p class="text-sm text-slate-500">{{ item.time }}</p>
              <p class="text-base text-slate-800">{{ item.text }}</p>
            </li>
          </ul>
        </article>
      </section>

      <section class="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="text-xl font-semibold text-slate-800">Quick Actions</h2>
        <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <button type="button" class="rounded-xl bg-[#FFC400] px-4 py-2 text-base font-semibold text-white">+ Add Booking</button>
          <button type="button" class="rounded-xl bg-[#1261FF] px-4 py-2 text-base font-semibold text-white">Reschedule Tour</button>
          <button type="button" class="rounded-xl bg-[#08B65A] px-4 py-2 text-base font-semibold text-white">View Guides</button>
        </div>
      </section>
    </main>
  </div>
</template>
