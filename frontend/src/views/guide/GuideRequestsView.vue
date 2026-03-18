<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <h1 class="app-title">Swap Requests</h1>
      <p class="app-subtitle">Send a swap request or accept and reject incoming swaps</p>

      <div
        class="mt-5 rounded-2xl border border-[#A9CDD9] bg-[#CAF0F8] p-4 dark:border-sky-800/60 dark:bg-sky-950/45"
      >
        <div class="mb-4 grid gap-3 md:grid-cols-2">
          <div
            class="rounded-2xl border border-[#7DB8CC]/60 bg-white/55 px-4 py-3 dark:border-sky-700/40 dark:bg-white/8"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[#0077B6]">Step 1</p>
            <p class="mt-1 text-sm font-semibold text-[#1C1C1C] dark:text-slate-100">
              Choose one of your assigned schedules
            </p>
          </div>
          <div
            class="rounded-2xl border border-[#7DB8CC]/60 bg-white/55 px-4 py-3 dark:border-sky-700/40 dark:bg-white/8"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[#0077B6]">Step 2</p>
            <p class="mt-1 text-sm font-semibold text-[#1C1C1C] dark:text-slate-100">
              Pick an available guide for that schedule
            </p>
          </div>
        </div>

        <div class="grid gap-3 lg:grid-cols-[1fr_1fr_auto]">
          <div>
            <label class="mb-2 block text-sm font-semibold text-[#1C1C1C] dark:text-slate-100"
              >My Schedule</label
            >
            <select
              v-model="selectedScheduleId"
              class="w-full rounded-xl border border-[#7DB8CC] bg-white px-4 py-3 text-sm text-[#1C1C1C] outline-none transition focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
              :disabled="submitting || !mySchedules.length"
            >
              <option value="">
                {{ mySchedules.length ? 'Choose your schedule' : 'No assigned schedules' }}
              </option>
              <option
                v-for="schedule in mySchedules"
                :key="schedule.id"
                :value="String(schedule.id)"
              >
                {{ schedule.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-[#1C1C1C] dark:text-slate-100"
              >Available Guide</label
            >
            <select
              v-model="selectedGuideId"
              class="w-full rounded-xl border border-[#7DB8CC] bg-white px-4 py-3 text-sm text-[#1C1C1C] outline-none transition focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
              :disabled="
                !selectedScheduleId || !availableGuides.length || submitting || candidatesLoading
              "
            >
              <option value="">
                {{
                  candidatesLoading
                    ? 'Loading guides...'
                    : availableGuides.length
                      ? 'Choose an available guide'
                      : 'No available guides'
                }}
              </option>
              <option v-for="guide in availableGuides" :key="guide.id" :value="String(guide.id)">
                {{ guide.name }}
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

        <p v-if="candidatesError" class="mt-3 text-sm font-medium text-[#B91C1C]">
          {{ candidatesError }}
        </p>
        <p v-if="!swapApiAvailable" class="mt-3 text-sm text-black/65 dark:text-slate-400">
          Swap request API is not available in this branch yet. Guide and schedule data still load
          normally.
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

        <div v-if="requestsLoading" class="text-sm text-black/60 dark:text-slate-400">
          Loading swap requests...
        </div>
        <div
          v-else-if="requestsError && swapApiAvailable"
          class="text-sm font-medium text-[#B91C1C]"
        >
          {{ requestsError }}
        </div>
        <div v-else-if="requests.length === 0" class="text-sm text-black/60 dark:text-slate-400">
          No pending requests.
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useAuth } from '@/contexts/authContext'
import { useToast } from '@/composables/useToast'
import {
  acceptGuideSwapRequest,
  createGuideSwapRequest,
  getGuideSwapCandidates,
  getGuideSwapRequests,
  getSchedules,
  rejectGuideSwapRequest,
} from '@/services/api'

const { profile, ensureAuthReady } = useAuth()
const { addToast } = useToast()

const guides = ref([])
const schedules = ref([])
const requests = ref([])
const selectedGuideId = ref('')
const selectedScheduleId = ref('')
const formError = ref('')
const candidatesError = ref('')
const requestsError = ref('')
const requestsLoading = ref(false)
const submitting = ref(false)
const candidatesLoading = ref(false)
const loadingActionId = ref(null)
const swapApiAvailable = ref(true)

const currentGuideId = computed(() => Number(profile.value?.guide_id ?? 0) || null)

const mySchedules = computed(() =>
  schedules.value.filter(
    (schedule) => Number(schedule.guideId) === Number(currentGuideId.value || 0),
  ),
)

const availableGuides = computed(() => guides.value)

const canSubmitSwapRequest = computed(() =>
  Boolean(
    swapApiAvailable.value &&
      currentGuideId.value &&
      selectedGuideId.value &&
      selectedScheduleId.value &&
      !submitting.value,
  ),
)

function buildGuideName(guide) {
  const firstName = String(guide?.first_name || guide?.firstName || '').trim()
  const lastName = String(guide?.last_name || guide?.lastName || '').trim()
  const fullName = [firstName, lastName].filter(Boolean).join(' ').trim()
  const rating = Number(guide?.guide_rating ?? guide?.guideRating)
  const ratingLabel = Number.isFinite(rating) ? ` • ${rating.toFixed(1)}★` : ''
  return `${fullName || String(guide?.full_name || guide?.name || guide?.email || `Guide ${guide?.id ?? ''}`).trim()}${ratingLabel}`
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
  const schedulesResponse = await getSchedules()

  schedules.value = (Array.isArray(schedulesResponse) ? schedulesResponse : [])
    .map(normalizeSchedule)
    .filter((schedule) => Number.isInteger(schedule.id) && schedule.id > 0 && schedule.guideId)
}

async function loadAvailableGuides() {
  const normalizedScheduleId = Number(selectedScheduleId.value)
  selectedGuideId.value = ''
  guides.value = []
  candidatesError.value = ''

  if (!normalizedScheduleId) return

  candidatesLoading.value = true

  try {
    const response = await getGuideSwapCandidates(normalizedScheduleId)
    swapApiAvailable.value = true
    guides.value = (Array.isArray(response) ? response : [])
      .map((guide) => ({
        id: Number(guide?.id ?? guide?.guide_id),
        name: buildGuideName(guide),
      }))
      .filter((guide) => Number.isInteger(guide.id) && guide.id > 0)
  } catch (error) {
    candidatesError.value = formatSwapApiError(error, 'Failed to load available guides.')
  } finally {
    candidatesLoading.value = false
  }
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
    const selectedGuide = availableGuides.value.find(
      (guide) => guide.id === Number(selectedGuideId.value),
    )
    const selectedSchedule = mySchedules.value.find(
      (schedule) => schedule.id === Number(selectedScheduleId.value),
    )

    await createGuideSwapRequest(
      selectedScheduleId.value,
      selectedGuideId.value,
      currentGuideId.value,
    )
    selectedGuideId.value = ''
    selectedScheduleId.value = ''
    guides.value = []
    addToast(
      selectedGuide && selectedSchedule
        ? `Swap request sent to ${selectedGuide.name} for ${selectedSchedule.title}.`
        : 'Swap request sent.',
      { type: 'success', title: 'Swap Request Sent' },
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
    await acceptGuideSwapRequest(swapRequestId, currentGuideId.value)
    addToast('The swap request has been accepted. Your schedule has been updated.', {
      type: 'success',
      title: 'Swap Accepted',
    })
    await loadRequests()
  } catch (error) {
    addToast(formatSwapApiError(error, 'Failed to accept swap request.'), {
      type: 'error',
      title: 'Swap Failed',
    })
  } finally {
    loadingActionId.value = null
  }
}

async function reject(swapRequestId) {
  loadingActionId.value = swapRequestId
  try {
    await rejectGuideSwapRequest(swapRequestId, currentGuideId.value)
    addToast('The swap request has been declined.', { type: 'success', title: 'Swap Rejected' })
    await loadRequests()
  } catch (error) {
    addToast(formatSwapApiError(error, 'Failed to reject swap request.'), {
      type: 'error',
      title: 'Rejection Failed',
    })
  } finally {
    loadingActionId.value = null
  }
}

watch(selectedScheduleId, () => {
  loadAvailableGuides()
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
