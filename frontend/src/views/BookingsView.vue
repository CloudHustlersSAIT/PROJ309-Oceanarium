<script setup>
// Import necessary modules
import { useRouter } from 'vue-router'
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
      getBookingDisplayId(booking),
      getReservationId(booking),
      booking.booking_id,
      booking.id,
      booking.clorian_reservation_id,
      booking.customer_id,
      booking.customerId,
      booking.tour_id,
      booking.tourId,
      getBookingDate(booking),
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

function getReservationId(booking) {
  return booking.id ?? booking.booking_id ?? booking.bookingId ?? null
}

function getBookingDisplayId(booking) {
  return booking.clorian_reservation_id || booking.booking_id || booking.bookingId || booking.id || '-'
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

function getBookingDate(booking) {
  return booking.date || booking.event_start_datetime || booking.eventStartDatetime || ''
}

function isCancelledStatus(booking) {
  return String(getStatus(booking)).trim().toLowerCase() === 'cancelled'
}

function getRowKey(booking, index) {
  const id = getReservationId(booking)
  if (id) return String(id)

  const customerId = booking.customer_id || booking.customerId || 'unknown-customer'
  const tourId = booking.tour_id || booking.tourId || 'unknown-tour'
  const date = getBookingDate(booking) || 'unknown-date'
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
  const reservationId = getReservationId(booking)
  if (!reservationId) return
  const bookingIdLabel = getBookingDisplayId(booking)

  const confirmed = window.confirm(`Cancel booking ${bookingIdLabel}?`)
  if (!confirmed) return

  actionState.value = { id: reservationId, type: 'cancel' }
  try {
    await cancelBooking(reservationId)
    await loadBookings()
  } catch (err) {
    error.value = err?.message || 'Failed to cancel booking'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

async function handleRescheduleBooking(booking) {
  const reservationId = getReservationId(booking)
  if (!reservationId) return

  const userInput = window.prompt('New date (YYYY-MM-DD):', formatApiDate(getBookingDate(booking)))
  if (!userInput) return

  const newDate = userInput.trim()
  if (!isIsoDate(newDate)) {
    error.value = 'Date must use YYYY-MM-DD format.'
    return
  }

  actionState.value = { id: reservationId, type: 'reschedule' }
  try {
    await rescheduleBooking(reservationId, newDate)
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

        <!-- Title -->
        <h1 class="text-2xl md:text-3xl font-semibold text-gray-800 mb-2">
          {{ pageTitle }}
        </h1>

        <!-- Subtitle -->
        <p class="text-sm md:text-base text-gray-500 mb-6">
          {{ pageDescription }}
        </p>

        <!-- Fun little ocean-themed line -->
        <p class="text-xs md:text-sm text-[#0077B6] font-medium mb-6">
          Our team is swimming as fast as they can to bring this experience to life. ðŸ¬
        </p>

        <!-- Actions -->
        <div class="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            class="px-5 py-2.5 rounded-full bg-[#0077B6] text-white text-sm font-medium hover:bg-[#0097e7] transition"
            @click="router.push('/home')"
          >
            Back to home
          </button>

          <button
            type="button"
            class="px-5 py-2.5 rounded-full border border-[#00B4D8] text-[#0077B6] text-sm font-medium bg-[#E0F7FF] hover:bg-[#CAF0F8] transition"
            @click="router.back()"
          >
            Go back
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

