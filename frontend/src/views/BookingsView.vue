<script setup>
import { computed, onMounted, ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import { cancelBooking, createBooking, getBookings, rescheduleBooking } from '../services/api'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const createError = ref('')
const createSuccess = ref('')
const searchText = ref('')
const bookings = ref([])
const actionState = ref({ id: null, type: '' })

const createDefaultForm = () => ({
  bookingId: '',
  customerId: '',
  tourId: '',
  date: '',
  adultTickets: 0,
  childTickets: 0,
})

const form = ref(createDefaultForm())

const filteredBookings = computed(() => {
  const text = searchText.value.trim().toLowerCase()
  if (!text) return bookings.value

  return bookings.value.filter((booking) => {
    const searchable = [
      booking.booking_id,
      booking.id,
      booking.customer_id,
      booking.customerId,
      booking.tour_id,
      booking.tourId,
      booking.date,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return searchable.includes(text)
  })
})

function normalizeDate(value) {
  if (!value) return '-'
  const raw = String(value).trim()
  const dateOnlyMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/)

  // Build date-only values in local time to avoid UTC day shift issues.
  const d = dateOnlyMatch
    ? new Date(Number(dateOnlyMatch[1]), Number(dateOnlyMatch[2]) - 1, Number(dateOnlyMatch[3]))
    : new Date(raw)

  if (Number.isNaN(d.getTime())) return 'Invalid date'
  return d.toLocaleDateString('en-US', { month: 'long', day: '2-digit', year: 'numeric' })
}

function getBookingId(booking) {
  return booking.booking_id || booking.id || '-'
}

function getCustomerId(booking) {
  return booking.customer_id || booking.customerId || '-'
}

function getTourId(booking) {
  return booking.tour_id || booking.tourId || '-'
}

function getStatus(booking) {
  return booking.status || '-'
}

function isCancelledStatus(booking) {
  return String(getStatus(booking)).trim().toLowerCase() === 'cancelled'
}

function getRowKey(booking, index) {
  const id = booking.booking_id || booking.id
  if (id) return String(id)

  const customerId = booking.customer_id || booking.customerId || 'unknown-customer'
  const tourId = booking.tour_id || booking.tourId || 'unknown-tour'
  const date = booking.date || 'unknown-date'
  return `${customerId}-${tourId}-${date}-${index}`
}

function formatApiDate(dateValue) {
  if (!dateValue) return ''
  const raw = String(dateValue).trim()
  const dateOnlyMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (dateOnlyMatch) return raw

  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return String(dateValue).slice(0, 10)
  return d.toISOString().slice(0, 10)
}

function isIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const [year, month, day] = value.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.getFullYear() === year && d.getMonth() === month - 1 && d.getDate() === day
}

async function loadBookings() {
  loading.value = true
  error.value = ''
  try {
    const data = await getBookings()
    bookings.value = Array.isArray(data) ? data : []
  } catch (err) {
    bookings.value = []
    error.value = err?.message || 'Failed to load bookings'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = createDefaultForm()
}

async function handleCreateBooking() {
  createError.value = ''
  createSuccess.value = ''

  if (!form.value.customerId.trim() || !form.value.tourId || !form.value.date) {
    createError.value = 'Customer ID, Tour ID, and date are required.'
    return
  }

  const parsedTourId = Number(form.value.tourId)
  if (!Number.isInteger(parsedTourId) || parsedTourId <= 0) {
    createError.value = 'Tour ID must be a valid positive number.'
    return
  }

  const totalTickets = Number(form.value.adultTickets) + Number(form.value.childTickets)
  if (totalTickets <= 0) {
    createError.value = 'At least one ticket is required.'
    return
  }

  saving.value = true
  try {
    await createBooking({
      customer_id: form.value.customerId.trim(),
      tour_id: parsedTourId,
      date: form.value.date,
      adult_tickets: Number(form.value.adultTickets) || 0,
      child_tickets: Number(form.value.childTickets) || 0,
    })

    createSuccess.value = 'Booking created successfully.'
    resetForm()
    await loadBookings()
  } catch (err) {
    createError.value = err?.message || 'Failed to create booking.'
  } finally {
    saving.value = false
  }
}

async function handleCancelBooking(booking) {
  const bookingId = getBookingId(booking)
  if (!bookingId || bookingId === '-') return

  const confirmed = window.confirm(`Cancel booking ${bookingId}?`)
  if (!confirmed) return

  actionState.value = { id: bookingId, type: 'cancel' }
  try {
    await cancelBooking(bookingId)
    await loadBookings()
  } catch (err) {
    error.value = err?.message || 'Failed to cancel booking'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

async function handleRescheduleBooking(booking) {
  const bookingId = getBookingId(booking)
  if (!bookingId || bookingId === '-') return

  const userInput = window.prompt('New date (YYYY-MM-DD):', formatApiDate(booking.date))
  if (!userInput) return

  const newDate = userInput.trim()
  if (!isIsoDate(newDate)) {
    error.value = 'Date must use YYYY-MM-DD format.'
    return
  }

  actionState.value = { id: bookingId, type: 'reschedule' }
  try {
    await rescheduleBooking(bookingId, newDate)
    await loadBookings()
  } catch (err) {
    error.value = err?.message || 'Failed to reschedule booking'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

onMounted(loadBookings)
</script>

<template>
  <div class="flex min-h-screen bg-gray-100 overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6">
      <div class="flex items-center justify-between gap-4 mb-5">
        <h1 class="text-4xl font-medium text-gray-800">Bookings</h1>
        <div class="w-full max-w-[430px] relative">
          <input
            v-model="searchText"
            type="text"
            placeholder="Search bookings"
            class="w-full rounded-xl border border-gray-400 bg-white py-2.5 px-4 text-sm"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[minmax(700px,1fr)_320px] gap-6">
        <section class="bg-white border border-gray-300 rounded-lg overflow-hidden">
          <div v-if="loading" class="p-4 text-sm text-gray-500">Loading bookings...</div>
          <div v-else-if="error" class="p-4 text-sm text-red-600">
            <div>{{ error }}</div>
            <button type="button" class="mt-2 rounded border border-red-300 px-3 py-1 text-xs" @click="loadBookings">
              Retry
            </button>
          </div>
          <div v-else-if="filteredBookings.length === 0" class="p-4 text-sm text-gray-500">No bookings found.</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[860px] text-sm">
              <thead class="bg-gray-50 text-gray-800 border-b border-gray-200">
                <tr>
                  <th class="text-left font-semibold px-5 py-3">Booking ID</th>
                  <th class="text-left font-semibold px-5 py-3">Date</th>
                  <th class="text-left font-semibold px-5 py-3">Customer ID</th>
                  <th class="text-left font-semibold px-5 py-3">Tour ID</th>
                  <th class="text-left font-semibold px-5 py-3">Status</th>
                  <th class="text-left font-semibold px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(booking, index) in filteredBookings"
                  :key="getRowKey(booking, index)"
                  class="border-b border-gray-200 hover:bg-gray-50"
                >
                  <td class="px-5 py-4 text-gray-700">{{ getBookingId(booking) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ normalizeDate(booking.date) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ getCustomerId(booking) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ getTourId(booking) }}</td>
                  <td class="px-5 py-4 text-gray-700 capitalize">{{ getStatus(booking) }}</td>
                  <td class="px-5 py-4">
                    <div class="flex flex-wrap gap-2">
                      <button
                        type="button"
                        class="rounded border border-blue-300 px-2 py-1 text-xs text-blue-700"
                        :disabled="actionState.id === getBookingId(booking)"
                        @click="handleRescheduleBooking(booking)"
                      >
                        {{ actionState.id === getBookingId(booking) && actionState.type === 'reschedule' ? 'Saving...' : 'Reschedule' }}
                      </button>
                      <button
                        type="button"
                        class="rounded border border-red-300 px-2 py-1 text-xs text-red-700"
                        :disabled="actionState.id === getBookingId(booking) || isCancelledStatus(booking)"
                        @click="handleCancelBooking(booking)"
                      >
                        {{ actionState.id === getBookingId(booking) && actionState.type === 'cancel' ? 'Cancelling...' : 'Cancel' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="bg-gray-100 border border-gray-400 rounded-lg p-4 h-fit">
          <h2 class="text-2xl font-medium text-gray-700 mb-4">Add New Booking</h2>

          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-700 mb-1">Booking ID</label>
              <input
                v-model="form.bookingId"
                type="text"
                placeholder="BKG-513321"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Customer ID</label>
              <input
                v-model="form.customerId"
                type="text"
                placeholder="Enter ID"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Tour ID</label>
              <input
                v-model="form.tourId"
                type="number"
                min="1"
                placeholder="Enter ID"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Date</label>
              <input
                v-model="form.date"
                type="date"
                lang="en-US"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Adult Tickets</label>
              <input
                v-model.number="form.adultTickets"
                type="number"
                min="0"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Child Tickets</label>
              <input
                v-model.number="form.childTickets"
                type="number"
                min="0"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              />
            </div>

            <p v-if="createError" class="text-xs text-red-600">{{ createError }}</p>
            <p v-if="createSuccess" class="text-xs text-green-700">{{ createSuccess }}</p>

            <div class="pt-2 flex gap-3">
              <button
                type="button"
                class="flex-1 rounded bg-cyan-500 hover:bg-cyan-600 text-gray-900 py-2 text-sm font-medium disabled:opacity-60"
                :disabled="saving"
                @click="handleCreateBooking"
              >
                {{ saving ? 'Creating...' : 'Create' }}
              </button>
              <button
                type="button"
                class="flex-1 rounded border border-gray-500 bg-white py-2 text-sm font-medium text-gray-700"
                @click="resetForm"
              >
                Cancel
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
