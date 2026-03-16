<template>
  <div class="space-y-6">
    <section class="rounded-2xl border border-black/10 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-[#1C1C1C] dark:text-slate-100">My Profile</h1>
          <p class="text-sm text-black/60 dark:text-slate-400">View and update your guide languages and availability.</p>
        </div>

        <div class="flex items-center gap-2">
          <span
            class="inline-flex items-center rounded-full bg-[#CAF0F8] px-3 py-1 text-xs font-semibold text-[#0077B6] ring-1 ring-[#00B4D8]/40"
          >
            Role: Guide
          </span>
          <span
            class="inline-flex items-center rounded-full bg-[#2A9D8F]/10 px-3 py-1 text-xs font-semibold text-[#2A9D8F]"
          >
            Status: Active
          </span>
        </div>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-black/10 bg-white p-6 shadow-sm md:col-span-1 dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
        <div class="flex items-center gap-3">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#CAF0F8] ring-1 ring-[#00B4D8]/40"
          >
            <span class="font-bold text-[#0077B6]">
              {{ initials }}
            </span>
          </div>
          <div class="leading-tight">
            <p class="text-sm text-black/60 dark:text-slate-400">Signed in as</p>
            <p class="text-base font-semibold text-[#1C1C1C] dark:text-slate-100">
              {{ displayName }}
            </p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <p class="text-sm text-black dark:text-slate-300">Email</p>
            <p class="break-all text-base font-semibold text-[#1C1C1C] dark:text-slate-100">
              {{ displayEmail }}
            </p>
          </div>

          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <p class="text-sm text-black dark:text-slate-300">Guide ID</p>
            <p class="text-base font-semibold text-[#1C1C1C] dark:text-slate-100">
              {{ currentGuideId || 'Unavailable' }}
            </p>
          </div>

          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <label class="block text-sm text-black dark:text-slate-300" for="guide-phone">Phone Number</label>
            <input
              id="guide-phone"
              :value="phoneNumber"
              type="text"
              inputmode="numeric"
              pattern="[0-9]*"
              maxlength="10"
              class="mt-2 w-full rounded-xl border border-black/10 bg-white px-4 py-3 text-base font-semibold text-[#1C1C1C] outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
              placeholder="e.g. 4035550123"
              @input="onPhoneInput"
            />
            <p v-if="phoneInputError" class="mt-2 text-sm font-medium text-[#B91C1C]">
              {{ phoneInputError }}
            </p>
          </div>
        </div>

        <div class="mt-5">
          <button
            type="button"
            class="w-full rounded-xl border border-[#0077B6] px-4 py-3 text-sm font-semibold text-[#0077B6] transition hover:bg-[#CAF0F8]"
            @click="resetToDefaults"
          >
            Reset to last saved
          </button>
        </div>
      </div>

      <div class="rounded-2xl border border-black/10 bg-white p-6 shadow-sm md:col-span-2 dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/30">
        <div
          v-if="!currentGuideId"
          class="rounded-xl border border-[#E63946]/25 bg-[#FFF5F5] p-4 text-sm font-medium text-[#B91C1C]"
        >
          Guide profile is not available.
        </div>

        <template v-else>
          <h2 class="text-lg font-semibold text-[#1C1C1C] dark:text-slate-100">Preferences</h2>
          <p class="text-sm text-black/60 dark:text-slate-400">These settings help admins schedule you better.</p>

          <div v-if="loading" class="mt-5 text-sm text-black/60">Loading profile...</div>
          <div
            v-else-if="loadError"
            class="mt-5 rounded-xl border border-[#E63946]/25 bg-[#FFF5F5] p-4 text-sm font-medium text-[#B91C1C]"
          >
            {{ loadError }}
          </div>

          <div v-else class="mt-5 space-y-6">
            <div class="rounded-2xl border border-black/10 p-5 dark:border-white/10 dark:bg-white/[0.02]">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-[#1C1C1C] dark:text-slate-100">Languages</h3>
                  <p class="text-sm text-black/60 dark:text-slate-400">Choose the languages you can support during tours.</p>
                </div>
                <span class="inline-flex items-center rounded-full bg-[#CAF0F8] px-3 py-1 text-xs font-semibold text-[#0077B6]">
                  {{ selectedLanguageIds.length }} selected
                </span>
              </div>

              <div class="mt-4 flex flex-wrap gap-2">
                <button
                  v-for="language in languageOptions"
                  :key="language.id"
                  type="button"
                  class="rounded-full border px-4 py-2 text-sm font-semibold transition"
                  :class="chipClass(selectedLanguageIds, language.id)"
                  @click="toggleChip(selectedLanguageIds, language.id)"
                >
                  {{ language.name }} ({{ String(language.code || '').toUpperCase() }})
                </button>
              </div>

            </div>

            <div class="rounded-2xl border border-black/10 p-5 dark:border-white/10 dark:bg-white/[0.02]">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-[#1C1C1C] dark:text-slate-100">Availability</h3>
                  <p class="text-sm text-black/60 dark:text-slate-400">Maintain the time windows when you are usually available.</p>
                </div>
              </div>

              <div class="mt-4 space-y-3">
                <div
                  v-for="slot in availability.slots"
                  :key="slot.key"
                  class="rounded-xl border border-black/10 bg-[#FAFCFE] p-4 dark:border-white/10 dark:bg-[#1A2231]"
                >
                  <div class="grid gap-3 md:grid-cols-[1.1fr_1fr_1fr] md:items-end">
                    <div class="space-y-2">
                      <label class="block text-sm font-semibold text-[#1C1C1C] dark:text-slate-100">Day</label>
                      <div
                        class="w-full rounded-xl border border-black/10 bg-white px-4 py-3 text-sm font-semibold text-[#1C1C1C] dark:border-white/10 dark:bg-[#1C2333] dark:text-slate-100"
                      >
                        {{ slot.day }}
                      </div>
                    </div>

                    <div class="space-y-2">
                      <label class="block text-sm font-semibold text-[#1C1C1C] dark:text-slate-100">Start</label>
                      <input
                        v-model="slot.start"
                        type="time"
                        class="w-full rounded-xl border border-black/10 bg-white px-4 py-3 text-sm outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                      />
                    </div>

                    <div class="space-y-2">
                      <label class="block text-sm font-semibold text-[#1C1C1C] dark:text-slate-100">End</label>
                      <input
                        v-model="slot.end"
                        type="time"
                        class="w-full rounded-xl border border-black/10 bg-white px-4 py-3 text-sm outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6] dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                      />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="flex items-center gap-3 pt-2">
              <CancelButton @cancel="resetToDefaults" />
              <SaveButton
                button-type="button"
                label="Save Changes"
                loading-label="Saving..."
                :loading="saving"
                :disabled="saving"
                @click="saveProfile"
              />
            </div>

            <p
              v-if="toast"
              class="text-sm font-semibold"
              :class="toastType === 'success' ? 'text-[#2A9D8F]' : 'text-[#E63946]'"
            >
              {{ toast }}
            </p>
          </div>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useAuth } from '@/contexts/authContext'
import CancelButton from '@/components/CancelButton.vue'
import SaveButton from '@/components/SaveButton.vue'
import {
  getGuideAvailability,
  getGuideLanguages,
  getLanguages,
  getGuides,
  updateGuide,
  updateGuideAvailability,
  updateGuideLanguages,
} from '@/services/api'

const { user, profile, ensureAuthReady } = useAuth()

const currentGuideId = computed(() => Number(profile.value?.guide_id ?? 0) || null)
const displayEmail = computed(() => profile.value?.email || user.value?.email || 'unknown')
const displayName = computed(() => {
  const first = String(profile.value?.first_name || '').trim()
  const last = String(profile.value?.last_name || '').trim()
  const full = [first, last].filter(Boolean).join(' ').trim()
  if (full) return full
  const email = displayEmail.value || ''
  return email ? email.split('@')[0] : 'Guide'
})
const initials = computed(() => {
  const name = displayName.value || 'G'
  const parts = name
    .replace(/[^a-zA-Z0-9 ]/g, ' ')
    .trim()
    .split(/\s+/)
  const first = parts[0]?.[0] || 'G'
  const second = parts[1]?.[0] || ''
  return (first + second).toUpperCase()
})
const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const languageOptions = ref([])
const selectedLanguageIds = ref([])
const phoneNumber = ref('')
const phoneInputError = ref('')
const availability = reactive({
  timezone: '',
  slots: [],
})
const savedState = ref({
  phone: '',
  languageIds: [],
  availability: { timezone: '', slots: [] },
})

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const toast = ref('')
const toastType = ref('success')

function chipClass(arr, value) {
  const active = arr.includes(value)
  return active
    ? 'border-[#00B4D8]/40 bg-[#CAF0F8] text-[#0077B6] dark:border-sky-700/40 dark:bg-sky-950/50 dark:text-sky-200'
    : 'border-black/10 bg-white text-black/70 hover:bg-[#CAF0F8]/60 dark:border-white/10 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5'
}

function toggleChip(arr, value) {
  const idx = arr.indexOf(value)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(value)
}

function mergeSlots(slots = []) {
  const byDay = new Map(
    slots.map((slot) => [
      String(slot.day || '').trim().toLowerCase(),
      {
        start: String(slot.start || '').trim(),
        end: String(slot.end || '').trim(),
      },
    ]),
  )

  return days.map((day, index) => {
    const existing = byDay.get(day.toLowerCase())
    return {
      key: `slot-${day}-${index}`,
      day,
      start: existing?.start || '',
      end: existing?.end || '',
    }
  })
}

function normalizeErrorMessage(error, fallbackMessage) {
  const message = String(error?.message || '').trim()
  const lowered = message.toLowerCase()

  if (message.includes('503') || lowered.includes('database unavailable')) {
    return 'Service unavailable. Please try again later.'
  }
  if (message.includes('404') || lowered.includes('guide not found') || lowered.includes('profile not found')) {
    return 'Profile not found.'
  }
  return message || fallbackMessage
}

function setToast(message, type = 'success') {
  toast.value = message
  toastType.value = type
  window.clearTimeout(setToast.timeoutId)
  setToast.timeoutId = window.setTimeout(() => {
    toast.value = ''
  }, 2500)
}

setToast.timeoutId = null

function syncSavedState(languageIds, availabilityState) {
  savedState.value = {
    phone: phoneNumber.value,
    languageIds: [...languageIds],
    availability: {
      timezone: availabilityState.timezone || '',
      slots: availabilityState.slots.map((slot) => ({
        day: slot.day,
        start: slot.start,
        end: slot.end,
      })),
    },
  }
}

function applySavedState() {
  phoneNumber.value = savedState.value.phone || ''
  selectedLanguageIds.value = [...savedState.value.languageIds]
  availability.timezone = ''
  availability.slots = mergeSlots(savedState.value.availability.slots)
}

function onPhoneInput(event) {
  const rawValue = String(event?.target?.value || '')
  const digitsOnly = rawValue.replace(/\D/g, '')
  const sanitizedValue = digitsOnly.slice(0, 10)
  const hadInvalidCharacters = rawValue !== sanitizedValue
  const exceededMaxLength = digitsOnly.length > 10

  phoneNumber.value = sanitizedValue
  phoneInputError.value = hadInvalidCharacters
    ? 'Only numbers can be entered in this field.'
    : exceededMaxLength
      ? 'Phone number cannot be longer than 10 digits.'
      : ''

  if (hadInvalidCharacters) {
    window.alert('Only numbers can be entered in the phone number field.')
  } else if (exceededMaxLength) {
    window.alert('Phone number cannot be longer than 10 digits.')
  }
}

function resetToDefaults() {
  applySavedState()
  setToast('Reset to last saved settings.')
}

async function loadProfile() {
  toast.value = ''
  loadError.value = ''

  if (!currentGuideId.value) {
    loading.value = false
    return
  }

  loading.value = true

  try {
    const [guidesResponse, availabilityResponse, guideLanguagesResponse, languagesResponse] = await Promise.all([
      getGuides(),
      getGuideAvailability(currentGuideId.value),
      getGuideLanguages(currentGuideId.value),
      getLanguages(),
    ])

    const currentGuide = (Array.isArray(guidesResponse) ? guidesResponse : []).find(
      (guide) => Number(guide?.id) === currentGuideId.value,
    )
    phoneNumber.value = String(currentGuide?.phone || '').replace(/\D/g, '')
    languageOptions.value = Array.isArray(languagesResponse) ? languagesResponse : []
    const languageIds = (guideLanguagesResponse?.languages || [])
      .map((language) => Number(language?.id))
      .filter((id) => Number.isInteger(id) && id > 0)

    const availabilityState = {
      timezone: '',
      slots: Array.isArray(availabilityResponse?.slots) ? availabilityResponse.slots : [],
    }

    syncSavedState(languageIds, availabilityState)
    applySavedState()
  } catch (error) {
    loadError.value = normalizeErrorMessage(error, 'Failed to load guide profile.')
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true

  try {
    const normalizedSlots = availability.slots
      .map((slot) => ({
        day: String(slot.day || '').trim(),
        start: String(slot.start || '').trim(),
        end: String(slot.end || '').trim(),
      }))
      .filter((slot) => slot.start || slot.end)

    const invalidSlot = normalizedSlots.find((slot) => !slot.start || !slot.end || slot.end <= slot.start)
    if (invalidSlot) {
      setToast('Each filled day needs a start time and an end time after the start.', 'error')
      return
    }

    await Promise.all([
      updateGuide(currentGuideId.value, {
        phone: phoneNumber.value,
      }),
      updateGuideLanguages(currentGuideId.value, { language_ids: selectedLanguageIds.value }),
      updateGuideAvailability(currentGuideId.value, {
        slots: normalizedSlots,
      }),
    ])

    syncSavedState(selectedLanguageIds.value, {
      timezone: '',
      slots: normalizedSlots,
    })
    availability.slots = mergeSlots(normalizedSlots)
    setToast('Profile saved successfully.')
  } catch (error) {
    setToast(normalizeErrorMessage(error, 'Failed to save profile.'), 'error')
  } finally {
    saving.value = false
  }
}

ensureAuthReady().finally(() => {
  loadProfile()
})
</script>
