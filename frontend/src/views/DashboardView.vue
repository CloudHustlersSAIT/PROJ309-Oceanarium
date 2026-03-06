<script setup>
import { computed, ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const selectedRange = ref('All Time')
const selectedDate = ref('2026-03-05')

const kpiCards = [
  { label: 'Total Tours Conducted', value: '8,567', trend: '+6.4%' },
  { label: 'Total Visitors Served', value: '51,402', trend: '+11.2%' },
  { label: 'Avg Occupancy Rate', value: '87%', trend: '+1.9%' },
  { label: 'Avg Guide Rating', value: '4.6', trend: '+0.2' },
]

const toursPerYear = [
  { label: '2021', value: 1640 },
  { label: '2022', value: 1500 },
  { label: '2023', value: 1800 },
  { label: '2024', value: 1690 },
  { label: '2025', value: 1220 },
]

const visitorsPerTour = [
  { label: 'Shark Diving', value: 1380 },
  { label: 'Dolphin Feeding', value: 1510 },
  { label: 'Coral Exploration', value: 1580 },
  { label: 'Deep Sea', value: 1400 },
  { label: 'Molluscs', value: 1750 },
]

const bookingsVsCancellations = [
  { month: 'Jan', bookings: 3400, cancellations: 140 },
  { month: 'Feb', bookings: 3200, cancellations: 110 },
  { month: 'Mar', bookings: 3600, cancellations: 130 },
  { month: 'Apr', bookings: 3500, cancellations: 120 },
  { month: 'May', bookings: 3800, cancellations: 155 },
]

const topGuides = [
  { name: 'Ana Costa', tours: 216, rating: 4.9 },
  { name: 'Hermes Costello', tours: 204, rating: 4.8 },
  { name: 'David Martinez', tours: 192, rating: 4.7 },
  { name: 'Liam Brown', tours: 186, rating: 4.7 },
]

const activityLog = [
  'Daily sync completed without conflicts.',
  'Occupancy crossed 85% in Dolphin Feeding.',
  '2 guides reassigned after afternoon cancellation.',
  'Average tour rating increased this week.',
]

const maxToursPerYear = computed(() => Math.max(...toursPerYear.map((item) => item.value), 1))
const maxVisitorsPerTour = computed(() => Math.max(...visitorsPerTour.map((item) => item.value), 1))
const maxBookings = computed(() => Math.max(...bookingsVsCancellations.map((item) => item.bookings), 1))
const maxCancellations = computed(() => Math.max(...bookingsVsCancellations.map((item) => item.cancellations), 1))

function percentage(value, max) {
  return `${Math.max(8, Math.round((value / max) * 100))}%`
}
</script>

<template>
  <div class="flex min-h-screen bg-[#F8FAFC] overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 class="text-3xl md:text-4xl font-semibold text-gray-900">Oceanarium Dashboard</h1>
          <p class="mt-1 text-sm text-gray-500">Prototype analytics workspace for operations visibility.</p>
        </div>

        <div class="flex flex-wrap gap-2">
          <input
            v-model="selectedDate"
            type="date"
            class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
          />
          <select
            v-model="selectedRange"
            class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm"
          >
            <option>All Time</option>
            <option>This Month</option>
            <option>This Week</option>
            <option>This Day</option>
          </select>
        </div>
      </section>

      <section class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-5">
        <article
          v-for="card in kpiCards"
          :key="card.label"
          class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
        >
          <p class="text-xs font-medium tracking-wide text-gray-500 uppercase">{{ card.label }}</p>
          <p class="mt-2 text-3xl font-semibold text-gray-900">{{ card.value }}</p>
          <p class="mt-1 text-sm text-emerald-600">{{ card.trend }} vs previous period</p>
        </article>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-5">
        <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Total Tours Per Year</h2>
          <div class="space-y-3">
            <div
              v-for="item in toursPerYear"
              :key="item.label"
              class="grid grid-cols-[42px_1fr_56px] items-center gap-3"
            >
              <span class="text-xs text-gray-600">{{ item.label }}</span>
              <div class="h-3 rounded bg-gray-100 overflow-hidden">
                <div class="h-full rounded bg-[#0EA5E9]" :style="{ width: percentage(item.value, maxToursPerYear) }" />
              </div>
              <span class="text-xs text-gray-700 text-right">{{ item.value }}</span>
            </div>
          </div>
        </article>

        <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Visitors Per Tour</h2>
          <div class="space-y-3">
            <div
              v-for="item in visitorsPerTour"
              :key="item.label"
              class="grid grid-cols-[140px_1fr_52px] items-center gap-3"
            >
              <span class="text-xs text-gray-600 truncate" :title="item.label">{{ item.label }}</span>
              <div class="h-3 rounded bg-gray-100 overflow-hidden">
                <div class="h-full rounded bg-[#2563EB]" :style="{ width: percentage(item.value, maxVisitorsPerTour) }" />
              </div>
              <span class="text-xs text-gray-700 text-right">{{ item.value }}</span>
            </div>
          </div>
        </article>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-[1.3fr_1fr] gap-4">
        <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">Bookings vs Cancellations</h2>

          <div class="space-y-3">
            <div
              v-for="row in bookingsVsCancellations"
              :key="row.month"
              class="grid grid-cols-[34px_1fr_1fr] items-center gap-3"
            >
              <span class="text-xs text-gray-600">{{ row.month }}</span>

              <div class="flex items-center gap-2">
                <span class="h-2.5 rounded bg-[#0284C7]" :style="{ width: percentage(row.bookings, maxBookings) }" />
                <span class="text-xs text-gray-700">{{ row.bookings }}</span>
              </div>

              <div class="flex items-center gap-2">
                <span class="h-2.5 rounded bg-[#F97316]" :style="{ width: percentage(row.cancellations, maxCancellations) }" />
                <span class="text-xs text-gray-700">{{ row.cancellations }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4 flex gap-6 text-xs text-gray-600">
            <div class="flex items-center gap-2"><span class="h-2.5 w-4 rounded bg-[#0284C7]" /> Bookings</div>
            <div class="flex items-center gap-2"><span class="h-2.5 w-4 rounded bg-[#F97316]" /> Cancellations</div>
          </div>
        </article>

        <aside class="space-y-4">
          <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h2 class="text-lg font-semibold text-gray-900 mb-3">Top Rated Guides</h2>
            <ul class="divide-y divide-gray-100">
              <li
                v-for="guide in topGuides"
                :key="guide.name"
                class="py-2 grid grid-cols-[1fr_auto_auto] items-center gap-3"
              >
                <span class="text-sm text-gray-700">{{ guide.name }}</span>
                <span class="text-xs text-gray-500">{{ guide.tours }} tours</span>
                <span class="text-sm font-medium text-amber-500">{{ guide.rating }} ★</span>
              </li>
            </ul>
          </article>

          <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h2 class="text-lg font-semibold text-gray-900 mb-3">Recent Activity</h2>
            <ul class="space-y-2">
              <li
                v-for="item in activityLog"
                :key="item"
                class="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-sm text-gray-700"
              >
                {{ item }}
              </li>
            </ul>
          </article>
        </aside>
      </section>
    </main>
  </div>
</template>
