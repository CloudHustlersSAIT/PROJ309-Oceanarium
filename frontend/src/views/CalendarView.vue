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
  if (!raw) return 'Sem data'

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

  // Sort groups by date (keep 'Sem data' last)
  return Object.fromEntries(
    Object.entries(groups).sort((a, b) => {
      if (a[0] === 'Sem data') return 1
      if (b[0] === 'Sem data') return -1
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
  <div class="flex min-h-screen bg-gray-50">
    <Sidebar />

    <main class="flex-1 px-6 py-10">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-2xl font-semibold mb-4">Calendar — Tours</h1>

        <!-- Data binding states: render loading, error, or tours from API -->
        <div v-if="loading" class="text-gray-600">Loading tours...</div>
        <div v-else-if="error" class="text-red-600">Error: {{ error }}</div>
        <div v-else>
          <div v-if="Object.keys(groupedTours).length === 0" class="text-gray-600">
            No tours found.
          </div>

          <!-- TASK 3.2 Implementation: Render backend API data grouped by date -->
          <!-- groupedTours is computed from tours array fetched via GET /tours API -->
          <!-- Each iteration renders all tours for a specific date -->
          <div v-for="(items, date) in groupedTours" :key="date" class="mb-6">
            <h2 class="text-lg font-medium text-blue-700 mb-2">{{ date }}</h2>

            <!-- List each tour with backend data binding: tour name, guide, time, ID -->
            <ul class="bg-white rounded-lg shadow-sm p-4 space-y-3">
              <li v-for="item in items" :key="item.id || item.tour || item.title" class="flex justify-between items-start">
                <div>
                  <!-- Data binding: Backend API returns 'tour' field (tour name) -->
                  <div class="font-semibold text-gray-800">{{ item.tour || item.title || 'Untitled Tour' }}</div>
                  <!-- Data binding: Backend API returns 'guide' field (guide name) -->
                  <div class="text-sm text-gray-600">Guide: {{ item.guide || item.guide_name || item.guideName || '—' }}</div>
                </div>

                <div class="text-sm text-gray-500 text-right">
                  <!-- Data binding: Backend API returns 'time' field (tour time) -->
                  <div>{{ item.time || item.start_time || item.datetime || '' }}</div>
                  <!-- Data binding: Backend API returns 'id' field (unique tour identifier) -->
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
