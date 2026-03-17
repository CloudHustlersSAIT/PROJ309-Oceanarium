<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import CancelButton from './CancelButton.vue'
import SaveButton from './SaveButton.vue'
import { getEligibleGuides, getGuideLanguages, manualAssignGuide } from '../services/api'

const props = defineProps({
  scheduleId: {
    type: Number,
    default: null,
  },
  visible: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['close', 'assigned'])

const requestToken = ref(0)
const loadingCandidates = ref(false)
const submitting = ref(false)
const eligibleGuides = ref([])
const eligibleGuideReasons = ref([])
const selectedGuideId = ref('')
const reason = ref('')
const error = ref('')
const guideLanguageCache = ref({})

const canSubmit = computed(() => {
  const guideId = Number(selectedGuideId.value)
  return Number.isInteger(guideId) && guideId > 0 && !submitting.value
})

function formatReasonCode(reasonCode) {
  const normalized = String(reasonCode || '').trim()
  if (!normalized) return 'No reason provided'
  return normalized
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function mapGuideLanguageResponse(response) {
  const languages = Array.isArray(response?.languages) ? response.languages : []
  const labels = languages
    .map((item) => String(item?.name || item?.code || '').trim())
    .filter(Boolean)

  return labels.length > 0 ? labels.join(', ') : 'Not mapped'
}

function withCachedGuideLanguages(guideRows) {
  const rows = Array.isArray(guideRows) ? guideRows : []
  return rows.map((guide) => {
    const guideId = Number(guide?.id)
    const cachedLanguage = guideLanguageCache.value[String(guideId)]
    return {
      ...guide,
      languageLabel: cachedLanguage || guide.languageLabel || 'Loading...',
    }
  })
}

async function enrichEligibleGuideLanguages(token, scheduleId) {
  if (!props.visible || eligibleGuides.value.length === 0) return
  if (requestToken.value !== token) return
  if (props.scheduleId !== scheduleId) return

  const uniqueGuideIds = Array.from(
    new Set(
      eligibleGuides.value
        .map((guide) => Number(guide?.id))
        .filter((guideId) => Number.isInteger(guideId) && guideId > 0),
    ),
  )

  const missingGuideIds = uniqueGuideIds.filter(
    (guideId) => !guideLanguageCache.value[String(guideId)],
  )

  if (missingGuideIds.length > 0) {
    const results = await Promise.allSettled(
      missingGuideIds.map((guideId) => getGuideLanguages(guideId)),
    )

    const nextCache = { ...guideLanguageCache.value }
    for (let index = 0; index < missingGuideIds.length; index += 1) {
      const guideId = missingGuideIds[index]
      const result = results[index]
      if (result.status === 'fulfilled') {
        nextCache[String(guideId)] = mapGuideLanguageResponse(result.value)
      } else {
        nextCache[String(guideId)] = 'Not mapped'
      }
    }

    guideLanguageCache.value = nextCache
  }

  if (!props.visible) return
  if (requestToken.value !== token) return
  if (props.scheduleId !== scheduleId) return

  eligibleGuides.value = withCachedGuideLanguages(eligibleGuides.value)
}

function resetState() {
  requestToken.value += 1
  selectedGuideId.value = ''
  reason.value = ''
  error.value = ''
  eligibleGuides.value = []
  eligibleGuideReasons.value = []
}

function handleClose() {
  resetState()
  emit('close')
}

async function fetchEligibleGuides() {
  const scheduleId = props.scheduleId
  if (!scheduleId) {
    error.value = 'No schedule selected for manual assignment.'
    return
  }

  const token = requestToken.value + 1
  requestToken.value = token

  selectedGuideId.value = ''
  reason.value = ''
  error.value = ''
  eligibleGuides.value = []
  eligibleGuideReasons.value = []
  loadingCandidates.value = true

  try {
    const eligibleResponse = await getEligibleGuides(scheduleId)

    if (requestToken.value !== token || !props.visible) return
    if (props.scheduleId !== scheduleId) return

    eligibleGuides.value = Array.isArray(eligibleResponse?.eligible_guides)
      ? eligibleResponse.eligible_guides.map((guide) => ({ ...guide, languageLabel: 'Loading...' }))
      : []

    eligibleGuideReasons.value = Array.isArray(eligibleResponse?.reasons)
      ? eligibleResponse.reasons
      : []

    if (eligibleGuides.value.length === 1) {
      selectedGuideId.value = String(eligibleGuides.value[0].id)
    }
  } catch (err) {
    if (requestToken.value === token) {
      error.value = err?.message || 'Failed to load eligible guides.'
    }
  } finally {
    if (requestToken.value === token) {
      loadingCandidates.value = false
    }
  }

  void enrichEligibleGuideLanguages(token, scheduleId)
}

async function handleSubmit() {
  const scheduleId = props.scheduleId
  if (!scheduleId) {
    error.value = 'No schedule selected for manual assignment.'
    return
  }

  const guideId = Number(selectedGuideId.value)
  if (!Number.isInteger(guideId) || guideId <= 0) {
    error.value = 'Select a guide before confirming manual assignment.'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const response = await manualAssignGuide(scheduleId, guideId, reason.value)

    emit('assigned', {
      scheduleId,
      guideId: response.guide_id,
      guideName: response.guide_name,
      warnings: Array.isArray(response?.warnings) ? response.warnings.filter(Boolean) : [],
    })

    resetState()
  } catch (err) {
    error.value = err?.message || 'Failed to assign selected guide manually.'
  } finally {
    submitting.value = false
  }
}

function handleKeydown(event) {
  if (event.key === 'Escape' && props.visible) {
    event.preventDefault()
    handleClose()
  }
}

watch(
  () => props.visible,
  (isVisible) => {
    if (isVisible) {
      fetchEligibleGuides()
    }
  },
)

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 bg-black/40" @click.self="handleClose">
    <div
      class="absolute left-1/2 top-1/2 w-[92%] max-w-140 -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[#ACBAC4] bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
    >
      <div class="flex items-center justify-between gap-3">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-slate-100">Manual Assign Guide</h3>
        <button
          type="button"
          class="text-xl leading-none text-red-300 hover:text-red-500 dark:text-slate-500 dark:hover:text-slate-200"
          aria-label="Close manual assign popup"
          @click="handleClose"
        >
          ×
        </button>
      </div>

      <p class="mt-1 text-xs text-gray-500 dark:text-slate-500">Schedule ID: {{ scheduleId }}</p>

      <div
        v-if="error"
        class="mt-3 rounded border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300"
      >
        {{ error }}
      </div>

      <div v-if="loadingCandidates" class="mt-4 text-sm text-gray-600 dark:text-slate-400">
        Loading eligible guides...
      </div>

      <div v-else class="mt-4 space-y-3">
        <div
          v-if="eligibleGuideReasons.length > 0"
          class="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
        >
          <p class="font-semibold">No fully eligible guides found.</p>
          <p v-for="r in eligibleGuideReasons" :key="r">Reason: {{ formatReasonCode(r) }}</p>
        </div>

        <div class="max-h-56 space-y-2 overflow-y-auto pr-1">
          <label
            v-for="guide in eligibleGuides"
            :key="guide.id"
            class="flex cursor-pointer items-start gap-3 rounded border border-[#ACBAC4] px-3 py-2 hover:bg-gray-50 dark:border-white/10 dark:bg-[#1C2333] dark:hover:bg-white/5"
          >
            <input
              v-model="selectedGuideId"
              type="radio"
              name="manual-assign-guide"
              :value="String(guide.id)"
              class="mt-0.5"
            />
            <div class="text-sm text-gray-700 dark:text-slate-300">
              <p class="font-semibold">
                {{ guide.first_name }} {{ guide.last_name }} (ID {{ guide.id }})
              </p>
              <p class="text-xs text-gray-500 dark:text-slate-500">
                Rating: {{ guide.guide_rating ?? 'N/A' }} · Same-day assignments:
                {{ guide.same_day_assignments }} · Languages: {{ guide.languageLabel }}
              </p>
            </div>
          </label>
          <p v-if="eligibleGuides.length === 0" class="text-sm text-gray-600 dark:text-slate-400">
            No eligible guide candidates returned by backend preview.
          </p>
        </div>

        <div>
          <label
            class="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-500"
            >Reason (optional)</label
          >
          <textarea
            v-model="reason"
            rows="3"
            class="w-full rounded border border-[#ACBAC4] bg-white px-3 py-2 text-sm text-gray-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500"
            placeholder="Example: Customer requested specific guide"
          />
        </div>
      </div>

      <div class="mt-5 flex items-center justify-end gap-2">
        <CancelButton @cancel="handleClose" />
        <SaveButton
          label="Assign"
          loading-label="Assigning..."
          :loading="submitting"
          :disabled="!canSubmit"
          @save="handleSubmit"
        />
      </div>
    </div>
  </div>
</template>
