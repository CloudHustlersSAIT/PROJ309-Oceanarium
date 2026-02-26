<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import { getBookings, cancelBooking, rescheduleBooking } from '../services/api'

const bookings = ref([])
const loading = ref(false)
const error = ref(null)
const activeFilter = ref('all')
const filterDate = ref('')
const openMenuId = ref(null)
const rescheduleTarget = ref(null)
const rescheduleDate = ref('')

function toggleMenu(bookingId) {
  openMenuId.value = openMenuId.value === bookingId ? null : bookingId
}

function closeMenu() {
  openMenuId.value = null
}

function onWindowClick() {
  closeMenu()
}

const filters = [
  { key: 'all', label: 'All' },
  { key: 'unassigned', label: 'Unassigned' },
  { key: 'assigned', label: 'Assigned' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
]

const filteredBookings = computed(() => {
  let result = bookings.value
  if (activeFilter.value !== 'all') {
    result = result.filter((b) => b.status === activeFilter.value)
  }
  if (filterDate.value) {
    result = result.filter((b) => b.date === filterDate.value)
  }
  return result
})

const statusCounts = computed(() => {
  const counts = {
    all: bookings.value.length,
    unassigned: 0,
    assigned: 0,
    completed: 0,
    cancelled: 0,
  }
  bookings.value.forEach((b) => {
    if (counts[b.status] !== undefined) counts[b.status]++
  })
  return counts
})

async function loadBookings() {
  loading.value = true
  error.value = null
  try {
    bookings.value = await getBookings()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function handleComplete(bookingId) {
  closeMenu()
  alert('Complete action not yet implemented for versioned bookings')
}

async function handleCancel(bookingId) {
  closeMenu()
  try {
    await cancelBooking(bookingId)
    await loadBookings()
  } catch (e) {
    alert('Failed to cancel booking')
  }
}

function openReschedule(booking) {
  closeMenu()
  rescheduleTarget.value = booking
  rescheduleDate.value = booking.date
}

function closeReschedule() {
  rescheduleTarget.value = null
  rescheduleDate.value = ''
}

async function handleReschedule() {
  if (!rescheduleTarget.value || !rescheduleDate.value) return
  try {
    await rescheduleBooking(rescheduleTarget.value.booking_id, rescheduleDate.value)
    closeReschedule()
    await loadBookings()
  } catch (e) {
    alert('Failed to reschedule booking')
  }
}

function statusColor(status) {
  switch (status) {
    case 'unassigned':
      return 'bg-yellow-100 text-yellow-800'
    case 'assigned':
      return 'bg-blue-100 text-blue-800'
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'cancelled':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function filterButtonClass(key) {
  if (activeFilter.value === key) return 'bg-[#0077B6] text-white shadow-md'
  return 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
}

let pollInterval = null

onMounted(() => {
  loadBookings()
  pollInterval = setInterval(loadBookings, 10000)
  window.addEventListener('click', onWindowClick)
})

onBeforeUnmount(() => {
  clearInterval(pollInterval)
  window.removeEventListener('click', onWindowClick)
})
</script>

<template>
  <div class="flex min-h-screen bg-gray-50 overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 px-4 py-6 pt-14 sm:pt-10 sm:px-6 sm:py-10 md:pt-10">
      <div class="max-w-5xl mx-auto w-full">
        <h1 class="text-xl font-semibold mb-6 sm:text-2xl text-gray-800">Bookings</h1>

        <!-- Filters -->
        <div class="flex flex-wrap items-center gap-2 mb-6">
          <button
            v-for="f in filters"
            :key="f.key"
            :class="filterButtonClass(f.key)"
            class="px-4 py-2 rounded-full text-sm font-medium transition"
            @click="activeFilter = f.key"
          >
            {{ f.label }}
            <span class="ml-1 opacity-70">({{ statusCounts[f.key] }})</span>
          </button>
          <input
            type="date"
            v-model="filterDate"
            class="ml-auto px-3 py-2 rounded-full text-sm border border-gray-200 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-[#0077B6]"
          />
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-gray-600 text-sm sm:text-base py-4">
          Loading bookings...
        </div>

        <!-- Error -->
        <div v-else-if="error" class="text-red-600 text-sm sm:text-base py-4">
          Error: {{ error }}
        </div>

        <!-- Empty state -->
        <div
          v-else-if="filteredBookings.length === 0"
          class="text-gray-500 text-sm sm:text-base py-8 text-center"
        >
          No {{ activeFilter === 'all' ? '' : activeFilter }} bookings found.
        </div>

        <!-- Bookings table -->
        <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-visible">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-[#0077B6] text-white text-left">
                <th class="py-3 px-4">ID</th>
                <th class="py-3 px-4">Customer</th>
                <th class="py-3 px-4">Tour</th>
                <th class="py-3 px-4">Guide</th>
                <th class="py-3 px-4">Date</th>
                <th class="py-3 px-4">Time</th>
                <th class="py-3 px-4 text-center">Tickets</th>
                <th class="py-3 px-4">Status</th>
                <th class="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="b in filteredBookings"
                :key="b.booking_id"
                class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td class="py-3 px-4 font-medium text-gray-700">#{{ b.booking_id }}</td>
                <td class="py-3 px-4 text-gray-600">
                  {{ b.customer_name || '—' }}
                </td>
                <td class="py-3 px-4 text-gray-600">{{ b.tour_name || '—' }}</td>
                <td class="py-3 px-4 text-gray-600">{{ b.guide_name || '—' }}</td>
                <td class="py-3 px-4 text-gray-600">{{ b.date }}</td>
                <td class="py-3 px-4 text-gray-600 whitespace-nowrap">
                  <template v-if="b.start_time && b.end_time">
                    {{ b.start_time }}–{{ b.end_time }}
                  </template>
                  <template v-else>—</template>
                </td>
                <td class="py-3 px-4 text-center text-gray-600">
                  {{ b.adult_tickets }} adult{{ b.adult_tickets !== 1 ? 's' : '' }},
                  {{ b.child_tickets }} child{{ b.child_tickets !== 1 ? 'ren' : '' }}
                </td>
                <td class="py-3 px-4">
                  <span
                    :class="statusColor(b.status)"
                    class="px-2.5 py-1 rounded-full text-xs font-semibold capitalize"
                  >
                    {{ b.status }}
                  </span>
                </td>
                <td class="py-3 px-4 text-center">
                  <div class="relative inline-block">
                    <button
                      v-if="b.status !== 'cancelled' && b.status !== 'completed'"
                      class="p-1.5 rounded-full hover:bg-gray-200 transition text-gray-500"
                      @click.stop="toggleMenu(b.booking_id)"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <circle cx="10" cy="4" r="1.5" />
                        <circle cx="10" cy="10" r="1.5" />
                        <circle cx="10" cy="16" r="1.5" />
                      </svg>
                    </button>
                    <span
                      v-if="b.status === 'cancelled' || b.status === 'completed'"
                      class="text-xs text-gray-400 italic"
                      >No actions</span
                    >
                    <div
                      v-if="openMenuId === b.booking_id"
                      class="absolute right-0 mt-1 w-36 bg-white rounded-lg shadow-lg border border-gray-100 z-20 py-1"
                    >
                      <button
                        v-if="b.status === 'assigned'"
                        class="w-full text-left px-4 py-2 text-sm text-green-600 hover:bg-gray-50 transition"
                        @click="handleComplete(b.booking_id)"
                      >
                        Complete
                      </button>
                      <button
                        v-if="b.status === 'unassigned' || b.status === 'assigned'"
                        class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition"
                        @click="openReschedule(b)"
                      >
                        Reschedule
                      </button>
                      <button
                        v-if="b.status === 'unassigned' || b.status === 'assigned'"
                        class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 transition"
                        @click="handleCancel(b.booking_id)"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Reschedule Modal -->
        <div
          v-if="rescheduleTarget"
          class="fixed inset-0 flex items-center justify-center z-50 bg-black/30"
          @click.self="closeReschedule"
        >
          <div class="bg-white rounded-xl shadow-xl p-6 w-96">
            <h3 class="text-xl font-bold mb-4">
              Reschedule Booking #{{ rescheduleTarget.booking_id }}
            </h3>
            <label class="block text-sm font-medium text-gray-700 mb-1">New date</label>
            <input type="date" v-model="rescheduleDate" class="w-full border p-2 mb-4 rounded" />
            <div class="flex justify-end gap-3">
              <button
                class="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500"
                @click="closeReschedule"
              >
                Cancel
              </button>
              <button
                class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                @click="handleReschedule"
              >
                Reschedule
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
