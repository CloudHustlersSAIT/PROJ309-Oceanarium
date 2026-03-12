<script setup>
import { computed, onMounted, ref } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import CancelButton from '../components/CancelButton.vue'
import { cancelBooking, createBooking, getBookings, getSchedules, rescheduleBooking } from '../services/api'
import {
  formatScheduleDateTimeForDisplay,
  formatStatusLabel,
  mapLanguageCodeToName,
  sanitizeNumericInput,
} from '../utils/reservation'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const createError = ref('')
const createSuccess = ref('')
const searchText = ref('')
const reservations = ref([])
const actionState = ref({ id: null, type: '' })
const availableSchedules = ref([])
const schedulesLoading = ref(false)
const schedulesError = ref('')
const showCreatePopup = ref(false)

const CUSTOMER_ID_MAX_LENGTH = 4
const SHORT_NUMERIC_MAX_LENGTH = 2

const createDefaultForm = () => ({
  customerId: '',
  selectedScheduleId: '',
  adultTickets: '',
  childTickets: '',
})

const form = ref(createDefaultForm())

const totalTicketCount = computed(() => {
  return (Number(form.value.adultTickets) || 0) + (Number(form.value.childTickets) || 0)
})

const selectedCreateSchedule = computed(() => {
  const selectedId = Number(form.value.selectedScheduleId)
  if (!Number.isInteger(selectedId) || selectedId <= 0) return null
  return availableSchedules.value.find((schedule) => Number(schedule?.id) === selectedId) || null
})

const filteredReservations = computed(() => {
  const text = searchText.value.trim().toLowerCase()
  const baseReservations = !text
    ? reservations.value
    : reservations.value.filter((reservation) => {
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

  return [...baseReservations].sort(compareReservationsByNearestDate)
})

const knownCustomerIds = computed(() => {
  const ids = new Set()

  for (const reservation of reservations.value) {
    const rawId = reservation?.customer_id ?? reservation?.customerId
    const normalized = String(rawId ?? '').trim()
    if (/^\d+$/.test(normalized)) ids.add(normalized)
  }

  return Array.from(ids).sort((a, b) => Number(a) - Number(b))
})

function formatShortDate(value) {
  if (!value) return '-'
  const raw = String(value).trim()
  const dateOnlyMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/)

  const d = dateOnlyMatch
    ? new Date(Number(dateOnlyMatch[1]), Number(dateOnlyMatch[2]) - 1, Number(dateOnlyMatch[3]))
    : new Date(raw)

  if (Number.isNaN(d.getTime())) return 'Invalid date'

  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  return `${month}/${day}/${year}`
}

function getReservationId(reservation) {
  return reservation.id ?? reservation.booking_id ?? reservation.bookingId ?? null
}

function getReservationDisplayId(reservation) {
  return (
    reservation.clorian_reservation_id ||
    reservation.booking_id ||
    reservation.bookingId ||
    reservation.id ||
    '-'
  )
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
  return (
    reservation.date || reservation.event_start_datetime || reservation.eventStartDatetime || ''
  )
}

function parseReservationDateMs(reservation) {
  const raw = String(getReservationDate(reservation) || '').trim()
  if (!raw) return Number.NEGATIVE_INFINITY

  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return Number.NEGATIVE_INFINITY
  return parsed.getTime()
}

function compareReservationsByNearestDate(a, b) {
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)
  const todayStartMs = todayStart.getTime()
  const aDate = parseReservationDateMs(a)
  const bDate = parseReservationDateMs(b)

  const aValid = Number.isFinite(aDate)
  const bValid = Number.isFinite(bDate)
  if (!aValid && !bValid) {
    const aId = Number(getReservationId(a))
    const bId = Number(getReservationId(b))
    if (Number.isInteger(aId) && Number.isInteger(bId)) return bId - aId
    return String(getReservationDisplayId(b)).localeCompare(String(getReservationDisplayId(a)))
  }
  if (!aValid) return 1
  if (!bValid) return -1

  const aIsFutureOrToday = aDate >= todayStartMs
  const bIsFutureOrToday = bDate >= todayStartMs

  // Upcoming reservations first; within upcoming, nearest date first.
  if (aIsFutureOrToday && !bIsFutureOrToday) return -1
  if (!aIsFutureOrToday && bIsFutureOrToday) return 1

  if (aIsFutureOrToday && bIsFutureOrToday) {
    const byUpcoming = aDate - bDate
    if (byUpcoming !== 0) return byUpcoming
  } else {
    // For past reservations, keep most recent first.
    const byPast = bDate - aDate
    if (byPast !== 0) return byPast
  }

  const aId = Number(getReservationId(a))
  const bId = Number(getReservationId(b))
  if (Number.isInteger(aId) && Number.isInteger(bId)) return bId - aId

  return String(getReservationDisplayId(b)).localeCompare(String(getReservationDisplayId(a)))
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

function formatDatePart(dateLike) {
  return [
    String(dateLike.getFullYear()).padStart(4, '0'),
    String(dateLike.getMonth() + 1).padStart(2, '0'),
    String(dateLike.getDate()).padStart(2, '0'),
  ].join('-')
}

function formatTimePart(dateLike) {
  return [
    String(dateLike.getHours()).padStart(2, '0'),
    String(dateLike.getMinutes()).padStart(2, '0'),
  ].join(':')
}

function mapLanguageToCode(language) {
  const normalized = String(language || '')
    .trim()
    .toLowerCase()
  if (normalized === 'english') return 'en'
  if (normalized === 'portuguese') return 'pt'
  if (normalized === 'spanish') return 'es'
  if (normalized === 'french') return 'fr'
  if (normalized === 'chinese') return 'zh'
  return ''
}

function getReservationLanguage(reservation) {
  return (
    reservation?.language ||
    mapLanguageCodeToName(reservation?.language_code) ||
    mapLanguageCodeToName(reservation?.languageCode) ||
    'English'
  )
}

function formatScheduleDateTime(rawValue) {
  return formatScheduleDateTimeForDisplay(rawValue)
}

function scheduleMatchesStartDateTime(schedule, date, time) {
  const raw = String(schedule?.event_start_datetime || '').trim()
  if (!raw) return false

  // Direct string match against ISO prefix when API returns YYYY-MM-DDTHH:mm...
  if (raw.startsWith(`${date}T${time}`)) return true

  // Fallback to local-time comparison for timezone-normalized payloads.
  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return false

  return formatDatePart(parsed) === date && formatTimePart(parsed) === time
}

function scheduleMatchesEndTime(schedule, date, endTime) {
  const raw = String(schedule?.event_end_datetime || '').trim()
  if (!raw) return false

  if (raw.startsWith(`${date}T${endTime}`)) return true

  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return false

  return formatDatePart(parsed) === date && formatTimePart(parsed) === endTime
}

async function resolveScheduleIdByCriteria(tourId, date, startTime, endTime, language) {
  const languageCode = mapLanguageToCode(language)
  const schedules = await getSchedules({ startDate: date, endDate: date })
  const candidates = (Array.isArray(schedules) ? schedules : [])
    .filter((schedule) => Number(schedule?.tour_id) === Number(tourId))
    .filter((schedule) => scheduleMatchesStartDateTime(schedule, date, startTime))
    .filter((schedule) => {
      if (!languageCode) return true
      if (!schedule?.language_code) return true
      return String(schedule.language_code).trim().toLowerCase() === languageCode
    })

  if (candidates.length === 0) return null
  if (candidates.length === 1) return candidates[0]?.id ?? null

  const exactEndMatches = candidates.filter((schedule) =>
    scheduleMatchesEndTime(schedule, date, endTime),
  )

  if (exactEndMatches.length === 1) return exactEndMatches[0]?.id ?? null
  return null
}

function buildScheduleOptionLabel(schedule) {
  const guideName = schedule?.guide_name || 'Unassigned Guide'
  const tourName = String(schedule?.tour_name || '').trim() || `Tour ${schedule?.tour_id ?? '-'}`
  const dateTime = formatScheduleDateTime(schedule?.event_start_datetime)
  const language = String(schedule?.language_code || '-').trim().toLowerCase() || '-'
  const reservationCount = Number(schedule?.reservation_count ?? 0)
  return `${tourName} | ${dateTime} | ${guideName} | ${language} | reservations: ${reservationCount}`
}

async function loadCreateSchedules() {
  schedulesLoading.value = true
  schedulesError.value = ''

  try {
    const today = getTodayIsoDate()
    let schedules = await getSchedules({ startDate: today, status: 'scheduled' })

    if (!Array.isArray(schedules) || schedules.length === 0) {
      schedules = await getSchedules({ startDate: today })
    }

    const nextSchedules = (Array.isArray(schedules) ? schedules : []).filter((schedule) => {
      const status = String(schedule?.status || '')
        .trim()
        .toLowerCase()
      return status !== 'cancelled' && status !== 'completed'
    })

    availableSchedules.value = nextSchedules
    const selectedId = Number(form.value.selectedScheduleId)
    if (!nextSchedules.some((schedule) => Number(schedule?.id) === selectedId)) {
      form.value.selectedScheduleId = nextSchedules.length === 1 ? String(nextSchedules[0]?.id) : ''
    }
  } catch (err) {
    availableSchedules.value = []
    form.value.selectedScheduleId = ''
    schedulesError.value = err?.message || 'Failed to load schedules.'
  } finally {
    schedulesLoading.value = false
  }
}

function inferReservationLanguage(reservation) {
  return getReservationLanguage(reservation)
}

function inferReservationStartTime(reservation) {
  const raw = String(
    reservation?.event_start_datetime || reservation?.eventStartDatetime || '',
  ).trim()
  if (!raw) return '09:00'

  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return '09:00'
  return formatTimePart(parsed)
}

function inferReservationEndTime(reservation) {
  const raw = String(reservation?.event_end_datetime || reservation?.eventEndDatetime || '').trim()
  if (raw) {
    const parsed = new Date(raw)
    if (!Number.isNaN(parsed.getTime())) return formatTimePart(parsed)
  }

  const startTime = inferReservationStartTime(reservation)
  const [h, m] = startTime.split(':').map(Number)
  const base = new Date(2000, 0, 1, h, m, 0, 0)
  base.setMinutes(base.getMinutes() + 60)
  return formatTimePart(base)
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

function openCreatePopup() {
  createError.value = ''
  createSuccess.value = ''
  showCreatePopup.value = true
}

function closeCreatePopup() {
  showCreatePopup.value = false
}

function getTodayIsoDate() {
  const now = new Date()
  const year = String(now.getFullYear())
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function handleNumericBeforeInput(event) {
  // Block non-digits before they reach the field.
  if (event?.data && /\D/.test(event.data)) {
    event.preventDefault()
  }
}

function handleNumericPaste(event, setter, maxLength = CUSTOMER_ID_MAX_LENGTH) {
  const pastedText = event?.clipboardData?.getData('text') ?? ''
  const sanitized = sanitizeNumericInput(pastedText, maxLength)
  event.preventDefault()
  setter(sanitized)
}

function setNumericField(event, field, maxLength = CUSTOMER_ID_MAX_LENGTH) {
  const digitsOnly = sanitizeNumericInput(event?.target?.value, maxLength)
  if (event?.target) event.target.value = digitsOnly
  form.value[field] = digitsOnly
}

function handleCustomerIdInput(event) {
  setNumericField(event, 'customerId', CUSTOMER_ID_MAX_LENGTH)
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
  form.value.customerId = sanitizeNumericInput(form.value.customerId, CUSTOMER_ID_MAX_LENGTH)
  form.value.adultTickets = sanitizeNumericInput(form.value.adultTickets, SHORT_NUMERIC_MAX_LENGTH)
  form.value.childTickets = sanitizeNumericInput(form.value.childTickets, SHORT_NUMERIC_MAX_LENGTH)

  if (!form.value.customerId.trim()) {
    createError.value = 'Customer ID is required.'
    return
  }

  if (!/^\d{1,4}$/.test(form.value.customerId)) {
    createError.value = 'Customer ID must contain only numbers (up to 4 digits).'
    return
  }

  if (!/^\d{0,2}$/.test(form.value.adultTickets) || !/^\d{0,2}$/.test(form.value.childTickets)) {
    createError.value = 'Adult and Child Tickets must contain only numbers (up to 2 digits).'
    return
  }

  if (totalTicketCount.value <= 0) {
    createError.value = 'At least one ticket is required.'
    return
  }

  const selectedScheduleId = Number(form.value.selectedScheduleId)
  if (!Number.isInteger(selectedScheduleId) || selectedScheduleId <= 0) {
    createError.value = 'Please select a matching schedule before creating the reservation.'
    return
  }

  if (totalTicketCount.value > 10) {
    const confirmed = window.confirm(
      'This reservation has more than 10 tickets. Do you want to continue?',
    )
    if (!confirmed) return
  }

  saving.value = true
  try {
    await createBooking({
      customer_id: form.value.customerId.trim(),
      schedule_id: selectedScheduleId,
      adult_tickets: Number(form.value.adultTickets) || 0,
      child_tickets: Number(form.value.childTickets) || 0,
    })

    createSuccess.value = 'Reservation created successfully.'
    resetForm()
    await Promise.all([loadReservations(), loadCreateSchedules()])
    showCreatePopup.value = false
  } catch (err) {
    createError.value = err?.message || 'Failed to create reservation.'
  } finally {
    saving.value = false
  }
}

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

  const tourId = Number(getTourId(reservation))
  if (!Number.isInteger(tourId) || tourId <= 0) {
    error.value = 'Unable to identify Tour ID for this reservation.'
    return
  }

  const language = inferReservationLanguage(reservation)
  const startTime = inferReservationStartTime(reservation)
  const endTime = inferReservationEndTime(reservation)

  const userInput = window.prompt(
    'New date (YYYY-MM-DD):',
    formatApiDate(getReservationDate(reservation)),
  )
  if (!userInput) return

  const newDate = userInput.trim()
  if (!isIsoDate(newDate)) {
    error.value = 'Date must use YYYY-MM-DD format.'
    return
  }

  actionState.value = { id: reservationId, type: 'reschedule' }
  try {
    const newScheduleId = await resolveScheduleIdByCriteria(
      tourId,
      newDate,
      startTime,
      endTime,
      language,
    )
    if (!newScheduleId) {
      error.value =
        'No matching schedule was found for the selected date/time. Create the schedule first, then try again.'
      return
    }

    await rescheduleBooking(reservationId, { new_schedule_id: Number(newScheduleId) })
    await loadReservations()
  } catch (err) {
    error.value = err?.message || 'Failed to reschedule reservation'
  } finally {
    actionState.value = { id: null, type: '' }
  }
}

onMounted(async () => {
  await Promise.all([loadReservations(), loadCreateSchedules()])
})
</script>

<template>
  <div class="flex min-h-screen bg-gray-100 overflow-x-hidden">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6">
      <div class="flex items-center justify-between gap-4 mb-5">
        <h1 class="text-4xl font-medium text-gray-800">Reservation</h1>
        <div class="flex w-full max-w-[620px] items-center gap-3">
          <div class="relative flex-1">
            <input
              v-model="searchText"
              type="text"
              placeholder="Search reservations"
              class="w-full rounded-xl border border-gray-400 bg-white py-2.5 px-4 text-sm"
            />
          </div>
          <button
            type="button"
            class="rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-gray-900 hover:bg-cyan-600"
            @click="openCreatePopup"
          >
            + Create
          </button>
        </div>
      </div>

      <section class="bg-white border border-gray-300 rounded-lg overflow-hidden">
        <div v-if="loading" class="p-4 text-sm text-gray-500">Loading reservations...</div>
        <div v-else-if="error" class="p-4 text-sm text-red-600">
          <div>{{ error }}</div>
          <button type="button" class="mt-2 rounded border border-red-300 px-3 py-1 text-xs" @click="loadReservations">
            Retry
          </button>
        </div>
        <div v-else-if="filteredReservations.length === 0" class="p-4 text-sm text-gray-500">No reservations found.</div>
        <div v-else class="overflow-hidden">
          <table class="w-full table-fixed text-sm">
            <colgroup>
              <col class="w-[16%]" />
              <col class="w-[12%]" />
              <col class="w-[14%]" />
              <col class="w-[8%]" />
              <col class="w-[14%]" />
              <col class="w-[10%]" />
              <col class="w-[26%]" />
            </colgroup>
            <thead class="bg-gray-50 text-gray-800 border-b border-gray-200">
              <tr>
                <th class="px-5 py-3 text-left font-semibold">Reservation</th>
                <th class="px-5 py-3 text-center font-semibold">Date</th>
                <th class="px-5 py-3 text-center font-semibold">Customer</th>
                <th class="px-5 py-3 text-center font-semibold">Tour</th>
                <th class="px-5 py-3 text-center font-semibold">Language</th>
                <th class="px-5 py-3 text-center font-semibold">Status</th>
                <th class="px-5 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(reservation, index) in filteredReservations"
                :key="getRowKey(reservation, index)"
                class="border-b border-gray-200 hover:bg-gray-50"
              >
                <td class="px-5 py-4 text-left text-gray-700 wrap-break-word">{{ getReservationDisplayId(reservation) }}</td>
                <td class="px-5 py-4 text-center text-gray-700 whitespace-nowrap">{{ formatShortDate(getReservationDate(reservation)) }}</td>
                <td class="px-5 py-4 text-center text-gray-700 wrap-break-word">{{ getCustomerId(reservation) }}</td>
                <td class="px-5 py-4 text-center text-gray-700 whitespace-nowrap">{{ getTourId(reservation) }}</td>
                <td class="px-5 py-4 text-center text-gray-700 wrap-break-word">{{ getReservationLanguage(reservation) }}</td>
                <td class="px-5 py-4 text-center text-gray-700 whitespace-nowrap">{{ formatStatusLabel(getStatus(reservation), '-') }}</td>
                <td class="px-5 py-4 text-center">
                  <div class="flex flex-nowrap items-center justify-center gap-2 whitespace-nowrap">
                    <button
                      v-if="!isCancelledStatus(reservation)"
                      type="button"
                      class="rounded border border-blue-300 px-2 py-1 text-xs text-blue-700"
                      :disabled="actionState.id === getReservationId(reservation)"
                      @click="handleRescheduleReservation(reservation)"
                    >
                      {{ actionState.id === getReservationId(reservation) && actionState.type === 'reschedule' ? 'Saving...' : 'Reschedule' }}
                    </button>
                    <button
                      v-else
                      type="button"
                      class="rounded border border-gray-300 px-2 py-1 text-xs text-gray-400 cursor-not-allowed"
                      disabled
                      aria-disabled="true"
                    >
                      Reschedule
                    </button>
                    <CancelButton
                      v-if="!isCancelledStatus(reservation)"
                      class="px-2 py-1 text-xs"
                      :label="actionState.id === getReservationId(reservation) && actionState.type === 'cancel' ? 'Cancelling...' : 'Cancel'"
                      :disabled="actionState.id === getReservationId(reservation)"
                      @cancel="handleCancelReservation(reservation)"
                    />
                    <CancelButton
                      v-else
                      class="px-2 py-1 text-xs"
                      :label="'Cancel'"
                      :disabled="true"
                      aria-disabled="true"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div v-if="showCreatePopup" class="fixed inset-0 z-50 bg-black/40" @click.self="closeCreatePopup">
        <div class="absolute right-0 top-0 h-full w-full max-w-[420px] bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <div class="text-sm text-gray-300">Create</div>
            <button class="text-gray-300 hover:text-white text-xl leading-none" aria-label="Close create popup" @click="closeCreatePopup">×</button>
          </div>

          <div class="space-y-3">
            <div>
              <label class="text-gray-300 block mb-1">Customer ID</label>
              <input
                :value="form.customerId"
                type="text"
                inputmode="numeric"
                :maxlength="CUSTOMER_ID_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                list="customer-id-options"
                placeholder="Enter existing customer numeric ID"
                class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
                @beforeinput="handleNumericBeforeInput"
                @paste="
                  (event) =>
                    handleNumericPaste(
                      event,
                      (value) => (form.customerId = value),
                      CUSTOMER_ID_MAX_LENGTH,
                    )
                "
                @input="handleCustomerIdInput"
              />
              <datalist id="customer-id-options">
                <option
                  v-for="customerId in knownCustomerIds"
                  :key="`customer-${customerId}`"
                  :value="customerId"
                />
              </datalist>
              <p class="mt-1 text-xs text-gray-400">Use an existing customer ID from the customers table. Suggestions come from existing reservations.</p>
            </div>

            <div>
              <label class="mb-1 flex items-center gap-1 text-sm text-gray-300">
                <button
                  type="button"
                  class="inline-flex items-center rounded p-0.5 text-gray-300 hover:bg-[#2d2d2d] disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="schedulesLoading"
                  aria-label="Refresh schedules"
                  title="Refresh schedules"
                  @click="loadCreateSchedules"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    class="h-4 w-4"
                    :class="{ 'animate-spin': schedulesLoading }"
                    aria-hidden="true"
                  >
                    <path d="M21 2v6h-6" />
                    <path d="M3 12a9 9 0 0 1 15.3-6.3L21 8" />
                    <path d="M3 22v-6h6" />
                    <path d="M21 12a9 9 0 0 1-15.3 6.3L3 16" />
                  </svg>
                </button>
                <span>Schedule</span>
              </label>
              <select
                v-model="form.selectedScheduleId"
                class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm"
                :disabled="schedulesLoading || availableSchedules.length === 0"
              >
                <option value="">Select a schedule</option>
                <option
                  v-for="schedule in availableSchedules"
                  :key="`schedule-${schedule.id}`"
                  :value="String(schedule.id)"
                >
                  {{ buildScheduleOptionLabel(schedule) }}
                </option>
              </select>
              <p v-if="schedulesLoading" class="mt-1 text-xs text-gray-400">Loading available schedules...</p>
              <p v-else-if="schedulesError" class="mt-1 text-xs text-red-300">{{ schedulesError }}</p>
              <p v-else-if="!availableSchedules.length" class="mt-1 text-xs text-amber-300">
                No open schedules available. Create a schedule first.
              </p>
              <p v-else class="mt-1 text-xs text-gray-400">Pick the event schedule for this reservation.</p>
            </div>

            <div v-if="selectedCreateSchedule" class="rounded border border-[#ACBAC4] bg-[#2a2a2a] px-3 py-2 text-xs text-gray-200">
              <div><span class="font-medium">Tour:</span> {{ selectedCreateSchedule.tour_name || `Tour ${selectedCreateSchedule.tour_id}` }}</div>
              <div><span class="font-medium">Date & Time:</span> {{ formatScheduleDateTime(selectedCreateSchedule.event_start_datetime) }}</div>
              <div><span class="font-medium">Guide:</span> {{ selectedCreateSchedule.guide_name || 'Unassigned Guide' }}</div>
              <div><span class="font-medium">Language:</span> {{ String(selectedCreateSchedule.language_code || '-').trim().toLowerCase() || '-' }}</div>
              <div><span class="font-medium">Reservations:</span> {{ Number(selectedCreateSchedule.reservation_count ?? 0) }}</div>
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Adult Tickets</label>
              <input
                :value="form.adultTickets"
                type="text"
                inputmode="numeric"
                :maxlength="SHORT_NUMERIC_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="00"
                class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
                @beforeinput="handleNumericBeforeInput"
                @paste="
                  (event) =>
                    handleNumericPaste(
                      event,
                      (value) => (form.adultTickets = value),
                      SHORT_NUMERIC_MAX_LENGTH,
                    )
                "
                @input="handleAdultTicketsInput"
              />
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Child Tickets</label>
              <input
                :value="form.childTickets"
                type="text"
                inputmode="numeric"
                :maxlength="SHORT_NUMERIC_MAX_LENGTH"
                pattern="[0-9]*"
                autocomplete="off"
                placeholder="00"
                class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
                @beforeinput="handleNumericBeforeInput"
                @paste="
                  (event) =>
                    handleNumericPaste(
                      event,
                      (value) => (form.childTickets = value),
                      SHORT_NUMERIC_MAX_LENGTH,
                    )
                "
                @input="handleChildTicketsInput"
              />
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Total Tickets</label>
              <input
                :value="totalTicketCount"
                type="text"
                readonly
                class="w-full rounded border border-[#ACBAC4] bg-[#252525] px-3 py-2 text-sm text-gray-300"
              />
            </div>

            <p v-if="createError" class="text-xs text-red-300">{{ createError }}</p>
            <p v-if="createSuccess" class="text-xs text-green-300">{{ createSuccess }}</p>

            <div class="pt-2 flex items-center justify-end gap-2">
              <CancelButton @cancel="closeCreatePopup" />
              <button
                type="button"
                class="px-5 py-2 rounded text-white font-medium"
                :class="!saving ? 'bg-blue-500 hover:bg-blue-600' : 'bg-blue-500/40 cursor-not-allowed'"
                :disabled="saving"
                @click="handleCreateReservation"
              >
                {{ saving ? 'Creating...' : 'Create' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
