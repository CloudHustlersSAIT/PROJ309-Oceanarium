<script setup>
// TASK 3.2: Integrate calendar with backend APIs
// This component binds backend tour data to the frontend calendar
// Backend endpoint: GET /tours returns array of tour objects with id, tour, guide, date, time, participants

import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import { getTours } from '../services/api' // API service that fetches tours from backend

const router = useRouter()

// Reactive state for calendar data binding
const tours = ref([]) // Stores tour data fetched from backend API
const loading = ref(false) // Loading state during API call
const error = ref(null) // Error state if API call fails

// Helper function to extract and format date from tour object
// API returns tours with flexible date field names (date, datetime, start_time, etc.)
// This function handles multiple field name variations for robustness
// CALENDAR DATE FORMAT: MM/DD/YYYY (Month/Day/Year)
function formatDateKey(tour) {
  const dateFields = ['date', 'datetime', 'start_time', 'start', 'start_date', 'time']
  const raw = dateFields.map((f) => tour[f]).find(Boolean)
  if (!raw) return 'Undated'

  const d = new Date(raw)
  if (isNaN(d)) return String(raw)
  
  // Format: MM/DD/YYYY (pad month and day with leading zeros)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const year = d.getFullYear()
  return `${month}/${day}/${year}`
}

// Computed property: Groups tours by date from backend API response
// Binding backend data to calendar view: transforms flat array into date-grouped object
// This enables rendering of tours organized by date as per project specification
const groupedTours = computed(() => {
  const groups = {}
  tours.value.forEach((t) => {
    const key = formatDateKey(t)
    if (!groups[key]) groups[key] = []
    groups[key].push(t)
  })

  // Sort groups by date (keep 'Undated' last)
  return Object.fromEntries(
    Object.entries(groups).sort((a, b) => {
      if (a[0] === 'Undated') return 1
      if (b[0] === 'Undated') return -1
      return new Date(a[0]) - new Date(b[0])
    }),
  )
})

// Lifecycle hook: Fetch tour data from backend API on component mount
// This satisfies Task 3.2 requirement: "Bind backend tour data to the frontend calendar component"
// API call: GET /tours -> returns array of tour objects with fields: id, tour, guide, date, time, participants
onMounted(async () => {
  loading.value = true
  try {
    // Fetch tours from backend API via getTours() service
    tours.value = await getTours()
    // Data binding complete: tours are now available for computed property grouping and rendering
  } catch (e) {
    // Handle API errors (connection failure, server error, etc.)
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <!-- Responsive layout: overflow-x-hidden prevents horizontal scroll on all viewports -->
  <div class="flex min-h-screen bg-gray-50 overflow-x-hidden">
    <Sidebar />

    <!-- Main: responsive padding and top space for mobile menu button when Sidebar is drawer -->
    <main class="flex-1 min-w-0 px-4 py-6 pt-14 sm:pt-10 sm:px-6 sm:py-10 md:pt-10">
      <div class="max-w-4xl mx-auto w-full">
        <!-- Responsive typography: readable on mobile and desktop -->
        <h1 class="text-xl font-semibold mb-4 sm:text-2xl text-gray-800">Calendar — Tours</h1>

        <!-- Data binding states: render loading, error, or tours from API -->
        <div v-if="loading" class="text-gray-600 text-sm sm:text-base py-4">Loading tours...</div>
        <div v-else-if="error" class="text-red-600 text-sm sm:text-base py-4 wrap-break-word">Error: {{ error }}</div>
        <div v-else>
          <div v-if="Object.keys(groupedTours).length === 0" class="text-gray-600 text-sm sm:text-base py-4">
            No tours found.
          </div>

          <!-- TASK 3.2 Implementation: Render backend API data grouped by date -->
          <!-- Responsive: date groups and tour cards adapt to screen size -->
          <div v-for="(items, date) in groupedTours" :key="date" class="mb-6">
            <h2 class="text-base font-medium text-blue-700 mb-2 sm:text-lg">{{ date }}</h2>

            <!-- List: responsive padding and spacing; no overflow on small screens -->
            <ul class="bg-white rounded-lg shadow-sm p-3 space-y-3 sm:p-4">
              <li
                v-for="item in items"
                :key="item.id || item.tour || item.title"
                class="flex flex-col gap-1 sm:flex-row sm:justify-between sm:items-start sm:gap-4 min-w-0"
              >
                <div class="min-w-0 flex-1">
                  <!-- Tour name: truncate on overflow for consistency -->
                  <div class="font-semibold text-gray-800 truncate" :title="item.tour || item.title || 'Untitled Tour'">
                    {{ item.tour || item.title || 'Untitled Tour' }}
                  </div>
                  <div class="text-sm text-gray-600 truncate">
                    Guide: {{ item.guide || item.guide_name || item.guideName || '—' }}
                  </div>
                </div>

                <div class="text-sm text-gray-500 sm:text-right shrink-0">
                  <div>{{ item.time || item.start_time || item.datetime || '' }}</div>
                  <div class="text-xs text-gray-400">ID: {{ item.id || '—' }}</div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
