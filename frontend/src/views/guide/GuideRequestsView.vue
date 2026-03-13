<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <h1 class="app-title">Swap Requests</h1>
      <p class="app-subtitle">Send a swap request or accept and reject incoming swaps</p>

      <div class="mt-5 rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4">
        <div class="grid gap-3 lg:grid-cols-[1fr_1fr_auto]">
          <div>
            <label class="mb-2 block text-sm font-semibold text-[#1C1C1C]">Select Guide</label>
            <select
              v-model="selectedGuideId"
              class="w-full rounded-xl border border-[#7DB8CC] bg-white px-4 py-3 text-sm text-[#1C1C1C] outline-none transition focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
            >
              <option value="">Choose a guide</option>
              <option v-for="guide in availableGuides" :key="guide.id" :value="String(guide.id)">
                {{ guide.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#1C1C1C]">Guide Schedule</label>
            <select
              v-model="selectedScheduleId"
              class="w-full rounded-xl border border-[#7DB8CC] bg-white px-4 py-3 text-sm text-[#1C1C1C] outline-none transition focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
              :disabled="!selectedGuideId || !targetGuideSchedules.length || submitting"
            >
              <option value="">Choose a schedule</option>
              <option v-for="schedule in targetGuideSchedules" :key="schedule.id" :value="String(schedule.id)">
                {{ schedule.label }}
              </option>
            </select>
          </div>

          <button
            class="app-action-btn min-h-12 self-end bg-[#0077B6] px-5 text-white hover:bg-[#0097E7] disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="!canSubmitSwapRequest"
            @click="submitSwapRequest"
          >
            {{ submitting ? 'Sending...' : 'Swap Request' }}
          </button>
        </div>

        <p v-if="!swapApiAvailable" class="mt-3 text-sm text-black/65">
          Swap request API is not available in this branch yet. Guide and schedule data still load normally.
        </p>
        <p v-if="formError" class="mt-3 text-sm font-medium text-[#B91C1C]">
          {{ formError }}
        </p>
      </div>

      <div class="mt-5 space-y-3">
        <div
          v-for="request in requests"
          :key="request.swapRequestId"
          class="notification-card p-3.5 sm:p-4"
        >
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="app-body-title">{{ request.title }}</p>
              <p class="app-body-meta">{{ request.date }} • {{ request.time }}</p>
              <p class="app-body-meta">Requested by {{ request.from }}</p>
            </div>

            <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
              <button
                class="app-action-btn bg-[#2A9D8F] text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="loadingActionId === request.swapRequestId"
                @click="accept(request.swapRequestId)"
              >
                {{ loadingActionId === request.swapRequestId ? 'Saving...' : 'Accept' }}
              </button>

              <button
                class="app-action-btn bg-[#E63946] text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="loadingActionId === request.swapRequestId"
                @click="reject(request.swapRequestId)"
              >
                {{ loadingActionId === request.swapRequestId ? 'Saving...' : 'Reject' }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="requestsLoading" class="text-sm text-black/60">Loading swap requests...</div>
        <div v-else-if="requestsError && swapApiAvailable" class="text-sm font-medium text-[#B91C1C]">
          {{ requestsError }}
        </div>
        <div v-else-if="requests.length === 0" class="text-sm text-black/60">No pending requests.</div>
      </div>

      <p v-if="toast" class="mt-4 text-sm font-semibold text-[#0077B6]">
        {{ toast }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useAuth } from '@/contexts/authContext'
import {
  acceptGuideSwapRequest,
  createGuideSwapRequest,
  getGuides,
  getGuideSwapRequests,
  getSchedules,
  rejectGuideSwapRequest,
} from '@/services/api'

const { profile, ensureAuthReady } = useAuth()

const guides = ref([])
const schedules = ref([])
const requests = ref([])
const selectedGuideId = ref('')
const selectedScheduleId = ref('')
const toast = ref('')
const formError = ref('')
const requestsError = ref('')
const requestsLoading = ref(false)
const submitting = ref(false)
const loadingActionId = ref(null)
const swapApiAvailable = ref(true)

const currentGuideId = computed(() => Number(profile.value?.guide_id ?? 0) || null)

const availableGuides = computed(() =>
  guides.value.filter((guide) => Number(guide.id) !== Number(currentGuideId.value || 0)),
)

const targetGuideSchedules = computed(() => {
  const selectedId = Number(selectedGuideId.value)
  if (!selectedId) return []

  return schedules.value.filter((schedule) => Number(schedule.guideId) === selectedId)
})

const canSubmitSwapRequest = computed(
  () =>
    Boolean(
      swapApiAvailable.value &&
        currentGuideId.value &&
        selectedGuideId.value &&
        selectedScheduleId.value &&
        !submitting.value,
    ),
)

function showToast(message) {
  toast.value = message
  window.clearTimeout(showToast.timeoutId)
  showToast.timeoutId = window.setTimeout(() => {
    toast.value = ''
  }, 2500)
}

showToast.timeoutId = null

function buildGuideName(guide) {
  const firstName = String(guide?.first_name || guide?.firstName || '').trim()
  const lastName = String(guide?.last_name || guide?.lastName || '').trim()
  const fullName = [firstName, lastName].filter(Boolean).join(' ').trim()
  return fullName || String(guide?.full_name || guide?.name || guide?.email || `Guide ${guide?.id ?? ''}`).trim()
}

function formatDateLabel(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTimeLabel(startValue, endValue) {
  const startDate = new Date(startValue)
  const endDate = new Date(endValue)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return '-'

  const startLabel = startDate.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
  const endLabel = endDate.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })

  return `${startLabel}-${endLabel}`
}

function normalizeSchedule(schedule) {
  const id = Number(schedule?.id ?? schedule?.schedule_id)
  const guideId = Number(schedule?.guide_id ?? schedule?.guideId ?? 0) || null
  const title = String(schedule?.tour_name || schedule?.title || `Schedule ${id}`).trim()
  const start = schedule?.event_start_datetime || schedule?.start
  const end = schedule?.event_end_datetime || schedule?.end

  return {
    id,
    guideId,
    title,
    start,
    end,
    label: `${title} • ${formatDateLabel(start)} • ${formatTimeLabel(start, end)}`,
  }
}

function normalizeSwapRequest(request) {
  const firstName = String(request?.requesting_guide_first_name || '').trim()
  const lastName = String(request?.requesting_guide_last_name || '').trim()
  const start = request?.event_start_datetime
  const end = request?.event_end_datetime

  return {
    swapRequestId: Number(request?.swap_request_id),
    scheduleId: Number(request?.schedule_id),
    title: String(request?.tour_name || `Schedule ${request?.schedule_id ?? ''}`).trim(),
    date: formatDateLabel(start),
    time: formatTimeLabel(start, end),
    from: [firstName, lastName].filter(Boolean).join(' ') || 'Unknown guide',
  }
}

function formatSwapApiError(error, fallbackMessage) {
  const message = String(error?.message || '').trim()
  if (message === 'Not Found' || error?.status === 404) {
    swapApiAvailable.value = false
    return 'Swap request backend is not available in this branch yet.'
  }
  return message || fallbackMessage
}

async function loadFormData() {
  const [guidesResponse, schedulesResponse] = await Promise.all([getGuides(), getSchedules()])

  guides.value = (Array.isArray(guidesResponse) ? guidesResponse : [])
    .map((guide) => ({
      id: Number(guide?.id ?? guide?.guide_id),
      name: buildGuideName(guide),
    }))
    .filter((guide) => Number.isInteger(guide.id) && guide.id > 0)

  schedules.value = (Array.isArray(schedulesResponse) ? schedulesResponse : [])
    .map(normalizeSchedule)
    .filter((schedule) => Number.isInteger(schedule.id) && schedule.id > 0 && schedule.guideId)
}

async function loadRequests() {
  if (!currentGuideId.value) {
    requests.value = []
    requestsError.value = 'Guide profile is not available.'
    return
  }

  requestsLoading.value = true
  requestsError.value = ''

  try {
    const response = await getGuideSwapRequests(currentGuideId.value)
    swapApiAvailable.value = true
    requests.value = (Array.isArray(response) ? response : []).map(normalizeSwapRequest)
  } catch (error) {
    requests.value = []
    requestsError.value = formatSwapApiError(error, 'Failed to load swap requests.')
  } finally {
    requestsLoading.value = false
  }
}

async function submitSwapRequest() {
  if (!canSubmitSwapRequest.value) return

  formError.value = ''
  submitting.value = true

  try {
    const selectedGuide = availableGuides.value.find((guide) => guide.id === Number(selectedGuideId.value))
    const selectedSchedule = targetGuideSchedules.value.find(
      (schedule) => schedule.id === Number(selectedScheduleId.value),
    )

    await createGuideSwapRequest(selectedScheduleId.value, currentGuideId.value)
    selectedGuideId.value = ''
    selectedScheduleId.value = ''
    showToast(
      selectedGuide && selectedSchedule
        ? `Swap request sent to ${selectedGuide.name} for ${selectedSchedule.title}.`
        : 'Swap request sent.',
    )
    await loadRequests()
  } catch (error) {
    formError.value = formatSwapApiError(error, 'Failed to send swap request.')
  } finally {
    submitting.value = false
  }
}

async function accept(swapRequestId) {
  loadingActionId.value = swapRequestId
  try {
    await acceptGuideSwapRequest(swapRequestId)
    showToast('Swap request accepted.')
    await loadRequests()
  } catch (error) {
    showToast(formatSwapApiError(error, 'Failed to accept swap request.'))
  } finally {
    loadingActionId.value = null
  }
}

async function reject(swapRequestId) {
  loadingActionId.value = swapRequestId
  try {
    await rejectGuideSwapRequest(swapRequestId)
    showToast('Swap request rejected.')
    await loadRequests()
  } catch (error) {
    showToast(formatSwapApiError(error, 'Failed to reject swap request.'))
  } finally {
    loadingActionId.value = null
  }
}

watch(selectedGuideId, () => {
  selectedScheduleId.value = ''
})

onMounted(async () => {
  try {
    await ensureAuthReady()
    await Promise.all([loadFormData(), loadRequests()])
  } catch (error) {
    requestsError.value = error?.message || 'Failed to load swap request data.'
  }
})
</script>
