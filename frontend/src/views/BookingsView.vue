<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import { cancelBooking, createBooking, getBookings, rescheduleBooking } from '../services/api'
import { LANGUAGE_OPTIONS } from '../constants/languages'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const createError = ref('')
const createSuccess = ref('')
const searchText = ref('')
const reservations = ref([])
const actionState = ref({ id: null, type: '' })

const ID_MAX_LENGTH = 6
const SHORT_NUMERIC_MAX_LENGTH = 2

const createDefaultForm = () => ({
  reservationId: '',
  customerId: '',
  tourId: '',
  language: 'English',
  date: '',
  startTime: '09:00',
  endTime: '10:00',
  adultTickets: '',
  childTickets: '',
})

const timeOptions = Array.from({ length: 15 }, (_, i) => {
  const minutes = (9 * 60) + i * 30
  const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
  const mm = String(minutes % 60).padStart(2, '0')
  const value = `${hh}:${mm}`
  const label = new Date(`2000-01-01T${value}:00`).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
  return { value, label }
})

const startTimeOptions = computed(() => timeOptions.slice(0, -1))
const endTimeOptions = computed(() => timeOptions.filter((option) => option.value > form.value.startTime))

const form = ref(createDefaultForm())

const totalTicketCount = computed(() => {
  return (Number(form.value.adultTickets) || 0) + (Number(form.value.childTickets) || 0)
})

const filteredReservations = computed(() => {
  const text = searchText.value.trim().toLowerCase()
  if (!text) return reservations.value

  return reservations.value.filter((reservation) => {
    const searchable = [
      getReservationDisplayId(reservation),
      getReservationId(reservation),
      reservation.booking_id,
      reservation.id,
      reservation.clorian_reservation_id,
      reservation.customer_id,
      reservation.customerId,
      reservation.tour_id,
      reservation.tourId,
      getReservationDate(reservation),
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

function getReservationId(reservation) {
  return reservation.id ?? reservation.booking_id ?? reservation.bookingId ?? null
}

function getReservationDisplayId(reservation) {
  return reservation.clorian_reservation_id || reservation.booking_id || reservation.bookingId || reservation.id || '-'
}

function getCustomerId(reservation) {
  return reservation.customer_id || reservation.customerId || '-'
}

function getTourId(reservation) {
  return reservation.tour_id || reservation.tourId || '-'
}

function getStatus(reservation) {
  return reservation.status || '-'
}

function getReservationDate(reservation) {
  return reservation.date || reservation.event_start_datetime || reservation.eventStartDatetime || ''
}

function isCancelledStatus(reservation) {
  return String(getStatus(reservation)).trim().toLowerCase() === 'cancelled'
}

function getRowKey(reservation, index) {
  const id = getReservationId(reservation)
  if (id) return String(id)

  const customerId = reservation.customer_id || reservation.customerId || 'unknown-customer'
  const tourId = reservation.tour_id || reservation.tourId || 'unknown-tour'
  const date = getReservationDate(reservation) || 'unknown-date'
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

async function loadReservations() {
  loading.value = true
  error.value = ''
  try {
    const data = await getBookings()
    reservations.value = Array.isArray(data) ? data : []
  } catch (err) {
    reservations.value = []
    error.value = err?.message || 'Failed to load reservations'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = createDefaultForm()
}

function sanitizeNumericId(value, maxLength = ID_MAX_LENGTH) {
  return String(value ?? '')
    .replace(/\D/g, '')
    .slice(0, maxLength)
}

function handleNumericBeforeInput(event) {
  // Block non-digits before they reach the field.
  if (event?.data && /\D/.test(event.data)) {
    event.preventDefault()
  }
}

function handleNumericPaste(event, setter, maxLength = ID_MAX_LENGTH) {
  const pastedText = event?.clipboardData?.getData('text') ?? ''
  const sanitized = sanitizeNumericId(pastedText, maxLength)
  event.preventDefault()
  setter(sanitized)
}

function setNumericField(event, field, maxLength = ID_MAX_LENGTH) {
  const digitsOnly = sanitizeNumericId(event?.target?.value, maxLength)
  if (event?.target) event.target.value = digitsOnly
  form.value[field] = digitsOnly
}

function handleReservationIdInput(event) {
  setNumericField(event, 'reservationId', ID_MAX_LENGTH)
}

function handleCustomerIdInput(event) {
  setNumericField(event, 'customerId', ID_MAX_LENGTH)
}

function handleTourIdInput(event) {
  setNumericField(event, 'tourId', SHORT_NUMERIC_MAX_LENGTH)
}

function handleAdultTicketsInput(event) {
  setNumericField(event, 'adultTickets', SHORT_NUMERIC_MAX_LENGTH)
}

function handleChildTicketsInput(event) {
  setNumericField(event, 'childTickets', SHORT_NUMERIC_MAX_LENGTH)
}

async function handleCreateReservation() {
  createError.value = ''
  createSuccess.value = ''

  // Defensive validation before submit.
  form.value.reservationId = sanitizeNumericId(form.value.reservationId, ID_MAX_LENGTH)
  form.value.customerId = sanitizeNumericId(form.value.customerId, ID_MAX_LENGTH)
  form.value.tourId = sanitizeNumericId(form.value.tourId, SHORT_NUMERIC_MAX_LENGTH)
  form.value.adultTickets = sanitizeNumericId(form.value.adultTickets, SHORT_NUMERIC_MAX_LENGTH)
  form.value.childTickets = sanitizeNumericId(form.value.childTickets, SHORT_NUMERIC_MAX_LENGTH)

  if (!form.value.customerId.trim() || !form.value.tourId || !form.value.date) {
    createError.value = 'Customer ID, Tour ID, and date are required.'
    return
  }

  if (!form.value.startTime || !form.value.endTime) {
    createError.value = 'Start time and End time are required.'
    return
  }

  if (form.value.endTime <= form.value.startTime) {
    createError.value = 'End time must be after Start time.'
    return
  }

  if (!/^\d{1,6}$/.test(form.value.customerId)) {
    createError.value = 'Customer ID must contain only numbers (up to 6 digits).'
    return
  }

  if (!/^\d{1,2}$/.test(form.value.tourId)) {
    createError.value = 'Tour ID must contain only numbers (up to 2 digits).'
    return
  }

  if (!/^\d{0,2}$/.test(form.value.adultTickets) || !/^\d{0,2}$/.test(form.value.childTickets)) {
    createError.value = 'Adult and Child Tickets must contain only numbers (up to 2 digits).'
    return
  }

  const parsedTourId = Number(form.value.tourId)
  if (!Number.isInteger(parsedTourId) || parsedTourId <= 0) {
    createError.value = 'Tour ID must be a valid positive number.'
    return
  }

  if (totalTicketCount.value <= 0) {
    createError.value = 'At least one ticket is required.'
    return
  }

  saving.value = true
  try {
    await createBooking({
      customer_id: form.value.customerId.trim(),
      tour_id: parsedTourId,
      language: form.value.language,
      date: form.value.date,
      start_time: `${form.value.startTime}:00`,
      end_time: `${form.value.endTime}:00`,
      adult_tickets: Number(form.value.adultTickets) || 0,
      child_tickets: Number(form.value.childTickets) || 0,
    })

    createSuccess.value = 'Reservation created successfully.'
    resetForm()
    await loadReservations()
  } catch (err) {
    createError.value = err?.message || 'Failed to create reservation.'
  } finally {
    saving.value = false
  }
}

watch(
  () => form.value.startTime,
  () => {
    if (!endTimeOptions.value.length) {
      form.value.endTime = form.value.startTime
      return
    }

    if (!endTimeOptions.value.some((option) => option.value === form.value.endTime)) {
      form.value.endTime = endTimeOptions.value[0].value
    }
  },
)

async function handleCancelReservation(reservation) {
  const reservationId = getReservationId(reservation)
  if (!reservationId) return
  const reservationIdLabel = getReservationDisplayId(reservation)

  const confirmed = window.confirm(`Cancel reservation ${reservationIdLabel}?`)
  if (!confirmed) return

  actionState.value = { id: reservationId, type: 'cancel' }
  try {
    await cancelBooking(reservationId)
    await loadReservations()
  } catch (err) {
    error.value = err?.message || 'Failed to cancel reservation'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

async function handleRescheduleReservation(reservation) {
  const reservationId = getReservationId(reservation)
  if (!reservationId) return

  const userInput = window.prompt('New date (YYYY-MM-DD):', formatApiDate(getReservationDate(reservation)))
  if (!userInput) return

  const newDate = userInput.trim()
  if (!isIsoDate(newDate)) {
    error.value = 'Date must use YYYY-MM-DD format.'
    return
  }

  actionState.value = { id: reservationId, type: 'reschedule' }
  try {
    await rescheduleBooking(reservationId, newDate)
    await loadReservations()
  } catch (err) {
    error.value = err?.message || 'Failed to reschedule reservation'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

onMounted(loadReservations)
</script>

<template>
  <div class="flex min-h-screen bg-gray-100 overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6">
      <div class="flex items-center justify-between gap-4 mb-5">
        <h1 class="text-4xl font-medium text-gray-800">Reservation</h1>
        <div class="w-full max-w-[430px] relative">
          <input
            v-model="searchText"
            type="text"
            placeholder="Search reservations"
            class="w-full rounded-xl border border-gray-400 bg-white py-2.5 px-4 text-sm"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[minmax(700px,1fr)_320px] gap-6">
        <section class="bg-white border border-gray-300 rounded-lg overflow-hidden">
          <div v-if="loading" class="p-4 text-sm text-gray-500">Loading reservations...</div>
          <div v-else-if="error" class="p-4 text-sm text-red-600">
            <div>{{ error }}</div>
            <button type="button" class="mt-2 rounded border border-red-300 px-3 py-1 text-xs" @click="loadReservations">
              Retry
            </button>
          </div>
          <div v-else-if="filteredReservations.length === 0" class="p-4 text-sm text-gray-500">No reservations found.</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[860px] text-sm">
              <thead class="bg-gray-50 text-gray-800 border-b border-gray-200">
                <tr>
                  <th class="text-left font-semibold px-5 py-3">Reservation ID</th>
                  <th class="text-left font-semibold px-5 py-3">Date</th>
                  <th class="text-left font-semibold px-5 py-3">Customer ID</th>
                  <th class="text-left font-semibold px-5 py-3">Tour ID</th>
                  <th class="text-left font-semibold px-5 py-3">Language</th>
                  <th class="text-left font-semibold px-5 py-3">Status</th>
                  <th class="text-left font-semibold px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(reservation, index) in filteredReservations"
                  :key="getRowKey(reservation, index)"
                  class="border-b border-gray-200 hover:bg-gray-50"
                >
                  <td class="px-5 py-4 text-gray-700">{{ getReservationDisplayId(reservation) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ normalizeDate(getReservationDate(reservation)) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ getCustomerId(reservation) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ getTourId(reservation) }}</td>
                  <td class="px-5 py-4 text-gray-700">{{ reservation.language || '-' }}</td>
                  <td class="px-5 py-4 text-gray-700 capitalize">{{ getStatus(reservation) }}</td>
                  <td class="px-5 py-4">
                    <div class="flex flex-wrap gap-2">
                      <button
                        type="button"
                        class="rounded border border-blue-300 px-2 py-1 text-xs text-blue-700"
                        :disabled="actionState.id === getReservationId(reservation)"
                        @click="handleRescheduleReservation(reservation)"
                      >
                        {{ actionState.id === getReservationId(reservation) && actionState.type === 'reschedule' ? 'Saving...' : 'Reschedule' }}
                      </button>
                      <button
                        type="button"
                        class="rounded border border-red-300 px-2 py-1 text-xs text-red-700"
                        :disabled="actionState.id === getReservationId(reservation) || isCancelledStatus(reservation)"
                        @click="handleCancelReservation(reservation)"
                      >
                        {{ actionState.id === getReservationId(reservation) && actionState.type === 'cancel' ? 'Cancelling...' : 'Cancel' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="bg-gray-100 border border-gray-400 rounded-none p-4 h-fit">
          <h2 class="text-2xl font-medium text-gray-700 mb-4">Add New Reservation</h2>

          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-700 mb-1">Reservation ID</label>
              <div class="flex items-stretch rounded border border-gray-400 bg-white overflow-hidden">
                <span class="inline-flex items-center border-r border-gray-300 bg-gray-100 px-3 text-sm text-gray-700">RSV-</span>
                <input
                  :value="form.reservationId"
                  type="text"
                  inputmode="numeric"
                  :maxlength="ID_MAX_LENGTH"
                  pattern="[0-9]*"
                  autocomplete="off"
                  placeholder="000000"
                  class="w-full px-3 py-2 text-sm outline-none"
                  @beforeinput="handleNumericBeforeInput"
                  @paste="(event) => handleNumericPaste(event, (value) => (form.reservationId = value))"
                  @input="handleReservationIdInput"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Customer ID</label>
              <div class="flex items-stretch rounded border border-gray-400 bg-white overflow-hidden">
                <span class="inline-flex items-center border-r border-gray-300 bg-gray-100 px-3 text-sm text-gray-700">CUST-</span>
                <input
                  :value="form.customerId"
                  type="text"
                  inputmode="numeric"
                  :maxlength="ID_MAX_LENGTH"
                  pattern="[0-9]*"
                  autocomplete="off"
                  placeholder="000000"
                  class="w-full px-3 py-2 text-sm outline-none"
                  @beforeinput="handleNumericBeforeInput"
                  @paste="(event) => handleNumericPaste(event, (value) => (form.customerId = value))"
                  @input="handleCustomerIdInput"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Tour ID</label>
              <input
                :value="form.tourId"
                type="text"
                inputmode="numeric"
                :maxlength="SHORT_NUMERIC_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="00"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
                @beforeinput="handleNumericBeforeInput"
                @paste="(event) => handleNumericPaste(event, (value) => (form.tourId = value), SHORT_NUMERIC_MAX_LENGTH)"
                @input="handleTourIdInput"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Language</label>
              <select
                v-model="form.language"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
              >
                <option v-for="language in LANGUAGE_OPTIONS" :key="language" :value="language">
                  {{ language }}
                </option>
              </select>
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
              <label class="block text-sm text-gray-700 mb-1">Start time</label>
              <select v-model="form.startTime" class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm">
                <option v-for="option in startTimeOptions" :key="`start-${option.value}`" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">End time</label>
              <select v-model="form.endTime" class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm">
                <option v-for="option in endTimeOptions" :key="`end-${option.value}`" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Adult Tickets</label>
              <input
                :value="form.adultTickets"
                type="text"
                inputmode="numeric"
                :maxlength="SHORT_NUMERIC_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="00"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
                @beforeinput="handleNumericBeforeInput"
                @paste="(event) => handleNumericPaste(event, (value) => (form.adultTickets = value), SHORT_NUMERIC_MAX_LENGTH)"
                @input="handleAdultTicketsInput"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Child Tickets</label>
              <input
                :value="form.childTickets"
                type="text"
                inputmode="numeric"
                :maxlength="SHORT_NUMERIC_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="00"
                class="w-full rounded border border-gray-400 bg-white px-3 py-2 text-sm"
                @beforeinput="handleNumericBeforeInput"
                @paste="(event) => handleNumericPaste(event, (value) => (form.childTickets = value), SHORT_NUMERIC_MAX_LENGTH)"
                @input="handleChildTicketsInput"
              />
            </div>

            <div>
              <label class="block text-sm text-gray-700 mb-1">Total Tickets</label>
              <input
                :value="totalTicketCount"
                type="text"
                readonly
                class="w-full rounded border border-gray-400 bg-gray-100 px-3 py-2 text-sm text-gray-700"
              />
            </div>

            <p v-if="createError" class="text-xs text-red-600">{{ createError }}</p>
            <p v-if="createSuccess" class="text-xs text-green-700">{{ createSuccess }}</p>

            <div class="pt-2 flex gap-3">
              <button
                type="button"
                class="flex-1 rounded bg-cyan-500 hover:bg-cyan-600 text-gray-900 py-2 text-sm font-medium disabled:opacity-60"
                :disabled="saving"
                @click="handleCreateReservation"
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