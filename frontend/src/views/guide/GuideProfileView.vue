<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="app-title">My Profile</h1>
          <p class="app-subtitle">View and update your guide languages and availability.</p>
        </div>

        <div class="flex items-center gap-2">
          <span class="app-badge-sky">
            Role: Guide
          </span>
          <span class="app-badge-success">
            Status: Active
          </span>
        </div>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <div class="app-surface-card app-section-padding md:col-span-1">
        <div class="flex items-center gap-3">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-light ring-1 ring-accent/40"
          >
            <span class="font-bold text-brand">
              {{ initials }}
            </span>
          </div>
          <div class="leading-tight">
            <p class="typo-muted">Signed in as</p>
            <p class="app-body-title text-base">
              {{ displayName }}
            </p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <p class="typo-muted">Email</p>
            <p class="break-all app-body-title text-base">
              {{ displayEmail }}
            </p>
          </div>

          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <p class="typo-muted">Guide ID</p>
            <p class="app-body-title text-base">
              {{ currentGuideId || 'Unavailable' }}
            </p>
          </div>

          <div class="rounded-xl border border-black/10 p-4 dark:border-white/10 dark:bg-white/[0.02]">
            <label class="app-form-label" for="guide-phone">Phone Number</label>
            <input
              id="guide-phone"
              :value="phoneNumber"
              type="tel"
              inputmode="tel"
              pattern="[+0-9]*"
              maxlength="16"
              class="mt-2 app-form-select font-semibold text-base"
              placeholder="e.g. +14035550123"
              @input="onPhoneInput"
            />
            <p v-if="phoneInputError" class="mt-2 app-text-error">
              {{ phoneInputError }}
            </p>
          </div>
        </div>

        <div class="mt-5">
          <button
            type="button"
            class="w-full rounded-xl border border-brand px-4 py-3 text-sm font-semibold text-brand transition hover:bg-accent-light dark:border-sky-700 dark:text-sky-300 dark:hover:bg-sky-950/40"
            @click="resetToDefaults"
          >
            Reset to last saved
          </button>
        </div>
      </div>

      <div class="app-surface-card app-section-padding md:col-span-2">
        <div
          v-if="!currentGuideId"
          class="app-error-block"
        >
          Guide profile is not available.
        </div>

        <template v-else>
          <h2 class="app-body-title text-lg">Preferences</h2>
          <p class="app-subtitle">These settings help admins schedule you better.</p>

          <div v-if="loading" class="mt-5 text-sm text-black/60">Loading profile...</div>
          <div
            v-else-if="loadError"
            class="mt-5 app-error-block"
          >
            {{ loadError }}
          </div>

          <div v-else class="mt-5 space-y-6">
            <div class="rounded-2xl border border-black/10 p-5 dark:border-white/10 dark:bg-white/[0.02]">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 class="app-body-title text-base">Languages</h3>
                  <p class="typo-muted mt-0.5">Choose the languages you can support during tours.</p>
                </div>
                <span class="app-badge-sky">
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
                  <h3 class="app-body-title text-base">Availability</h3>
                  <p class="typo-muted mt-0.5">Maintain the time windows when you are usually available.</p>
                </div>
              </div>

              <div class="mt-4 space-y-3">
                <div
                  v-for="slot in availability.slots"
                  :key="slot.key"
                  class="rounded-xl border border-black/10 bg-surface-elevated p-4 dark:border-white/10"
                >
                  <div class="grid gap-3 md:grid-cols-[1.1fr_1fr_1fr] md:items-end">
                    <div class="space-y-2">
                      <label class="app-form-label">Day</label>
                      <div
                        class="w-full rounded-xl border border-black/10 bg-surface-input px-4 py-3 text-sm font-semibold text-ink dark:border-white/10 dark:text-slate-100"
                      >
                        {{ slot.day }}
                      </div>
                    </div>

                    <div class="space-y-2">
                      <label class="app-form-label">Start</label>
                      <input
                        v-model="slot.start"
                        type="time"
                        class="w-full rounded-xl border border-black/10 bg-surface-input px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand dark:border-white/15 dark:text-slate-100 dark:focus:ring-sky-800/50"
                      />
                    </div>

                    <div class="space-y-2">
                      <label class="app-form-label">End</label>
                      <input
                        v-model="slot.end"
                        type="time"
                        class="w-full rounded-xl border border-black/10 bg-surface-input px-4 py-3 text-sm outline-none focus:border-brand focus:ring-1 focus:ring-brand dark:border-white/15 dark:text-slate-100 dark:focus:ring-sky-800/50"
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
              :class="toastType === 'success' ? 'text-success' : 'app-text-error'"
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

const PHONE_MAX_DIGITS = 15
const PHONE_REGEX = /^\+?[1-9]\d{7,14}$/

function chipClass(arr, value) {
  const active = arr.includes(value)
  return active
    ? 'border-accent/40 bg-accent-light text-brand dark:border-sky-700/40 dark:bg-sky-950/50 dark:text-sky-200'
    : 'border-black/10 bg-surface-input text-black/70 hover:bg-accent-light/60 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5'
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
  availability.timezone = savedState.value.availability.timezone || ''
  availability.slots = mergeSlots(savedState.value.availability.slots)
}

function sanitizePhoneForInput(rawValue) {
  const rawText = String(rawValue || '').trim()
  const hasLeadingPlus = rawText.startsWith('+')
  const containsPlusInMiddle = rawText.slice(1).includes('+')
  const hasDisallowedCharacters = /[^0-9+\s().-]/.test(rawText)
  const digitsOnly = rawText.replace(/\D/g, '')
  const exceededMaxDigits = digitsOnly.length > PHONE_MAX_DIGITS
  const trimmedDigits = digitsOnly.slice(0, PHONE_MAX_DIGITS)
  const sanitizedPhone = hasLeadingPlus ? `+${trimmedDigits}` : trimmedDigits

  return {
    phone: sanitizedPhone === '+' ? '' : sanitizedPhone,
    hadInvalidCharacters: containsPlusInMiddle || hasDisallowedCharacters,
    exceededMaxDigits,
  }
}

function isValidPhoneNumber(phoneValue) {
  const value = String(phoneValue || '').trim()
  if (!value) return true
  return PHONE_REGEX.test(value)
}

function onPhoneInput(event) {
  const { phone, hadInvalidCharacters, exceededMaxDigits } = sanitizePhoneForInput(event?.target?.value)

  phoneNumber.value = phone
  phoneInputError.value = hadInvalidCharacters
    ? 'Use digits with an optional leading + only.'
    : exceededMaxDigits
      ? 'Phone number cannot be longer than 15 digits.'
      : ''
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
    const fallbackPhone = sanitizePhoneForInput(profile.value?.phone || profile.value?.phone_number || '').phone
    phoneNumber.value = fallbackPhone

    const [availabilityResponse, guideLanguagesResponse, languagesResponse] = await Promise.all([
      getGuideAvailability(currentGuideId.value),
      getGuideLanguages(currentGuideId.value),
      getLanguages(),
    ])

    languageOptions.value = Array.isArray(languagesResponse) ? languagesResponse : []
    const languageIds = (guideLanguagesResponse?.languages || [])
      .map((language) => Number(language?.id))
      .filter((id) => Number.isInteger(id) && id > 0)

    const availabilityState = {
      timezone: String(availabilityResponse?.timezone || ''),
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
    phoneInputError.value = ''

    if (!isValidPhoneNumber(phoneNumber.value)) {
      phoneInputError.value = 'Enter a valid phone number (example: +14035550123).'
      setToast('Please correct the phone number format before saving.', 'error')
      return
    }

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

    const requests = [
      updateGuideLanguages(currentGuideId.value, { language_ids: selectedLanguageIds.value }),
      updateGuideAvailability(currentGuideId.value, {
        timezone: availability.timezone || undefined,
        slots: normalizedSlots,
      }),
    ]

    if (phoneNumber.value !== savedState.value.phone) {
      requests.unshift(
        updateGuide(currentGuideId.value, {
          phone: phoneNumber.value,
        }),
      )
    }

    await Promise.all(requests)

    syncSavedState(selectedLanguageIds.value, {
      timezone: availability.timezone || '',
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
