<script setup>
import { computed, reactive, ref } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import SaveButton from '../components/SaveButton.vue'
import { useAuth } from '../contexts/authContext'

const { user, profile } = useAuth()

const SETTINGS_STORAGE_KEY = 'oceanarium-admin-settings-v1'

const DEFAULT_SETTINGS = {
  displayName: 'Operations Administrator',
  email: '',
  language: 'English (US)',
  timezone: 'America/Sao_Paulo',
  reservationApproval: 'Manual review',
  scheduleLeadTime: '24 hours',
  scheduleConflictPolicy: 'Warn and require confirmation',
  allowUnassignedSchedules: true,
  autoEscalateUnassignable: true,
  notifyNewBookings: true,
  notifyOverbookingRisk: true,
  notifyGuideAvailabilityRisk: true,
  notifyDailyDigest: true,
  requireTwoFactor: true,
  sessionTimeout: '30 minutes',
  passwordResetPolicy: 'Email only',
  allowAdminDataExport: false,
}

const PERSISTED_SETTINGS_KEYS = [
  'language',
  'timezone',
  'reservationApproval',
  'scheduleLeadTime',
  'scheduleConflictPolicy',
  'allowUnassignedSchedules',
  'autoEscalateUnassignable',
  'notifyNewBookings',
  'notifyOverbookingRisk',
  'notifyGuideAvailabilityRisk',
  'notifyDailyDigest',
  'requireTwoFactor',
  'sessionTimeout',
  'passwordResetPolicy',
  'allowAdminDataExport',
]

function cloneDefaultSettings() {
  return { ...DEFAULT_SETTINGS }
}

function normalizeSettingValue(key, value) {
  const defaultValue = DEFAULT_SETTINGS[key]

  if (typeof defaultValue === 'boolean') {
    return typeof value === 'boolean' ? value : defaultValue
  }

  if (typeof defaultValue === 'string') {
    const normalized = String(value || '').trim()
    return normalized || defaultValue
  }

  return defaultValue
}

function sanitizeStoredSettings(rawStoredSettings) {
  if (!rawStoredSettings || typeof rawStoredSettings !== 'object') return {}

  const sanitized = {}
  PERSISTED_SETTINGS_KEYS.forEach((key) => {
    sanitized[key] = normalizeSettingValue(key, rawStoredSettings[key])
  })

  return sanitized
}

function loadStoredSettings() {
  if (typeof window === 'undefined') return {}

  try {
    const rawValue = window.localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!rawValue) return {}

    const parsedValue = JSON.parse(rawValue)
    return sanitizeStoredSettings(parsedValue)
  } catch {
    return {}
  }
}

function persistSettings() {
  if (typeof window === 'undefined') return

  const payload = {}
  PERSISTED_SETTINGS_KEYS.forEach((key) => {
    payload[key] = normalizeSettingValue(key, settingsForm[key])
  })

  window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(payload))
}

const settingsForm = reactive({
  ...cloneDefaultSettings(),
  ...loadStoredSettings(),
})

const infoMessage = ref('')
const savingSectionName = ref('')

const adminEmail = computed(() =>
  String(profile.value?.email || user.value?.email || settingsForm.email || 'admin@oceanarium.co'),
)

const adminRole = computed(() =>
  String(profile.value?.role || 'admin')
    .replace(/[_-]+/g, ' ')
    .trim()
    .toUpperCase(),
)

const adminStatus = computed(() =>
  profile.value?.is_active === false ? 'Restricted' : 'Active',
)

const policySummary = computed(() => [
  {
    label: 'Assignment Model',
    value: 'Language + Availability + Expertise',
    note: 'Hard constraints from guide assignment rules',
  },
  {
    label: 'Reservation Approval',
    value: settingsForm.reservationApproval,
    note: 'Applied by admin operations',
  },
  {
    label: 'Lead Time',
    value: settingsForm.scheduleLeadTime,
    note: 'Minimum notice before schedule start',
  },
  {
    label: 'Conflict Policy',
    value: settingsForm.scheduleConflictPolicy,
    note: 'Behavior when overlaps or violations are detected',
  },
])

if (!settingsForm.email) {
  settingsForm.email = adminEmail.value
}

if (settingsForm.displayName === DEFAULT_SETTINGS.displayName) {
  settingsForm.displayName = user.value?.displayName || settingsForm.displayName
}

function setInfoMessage(message) {
  infoMessage.value = message

  window.setTimeout(() => {
    if (infoMessage.value === message) {
      infoMessage.value = ''
    }
  }, 3500)
}

function saveSection(sectionName) {
  savingSectionName.value = sectionName

  try {
    persistSettings()
    setInfoMessage(`${sectionName} settings saved locally.`)
  } finally {
    savingSectionName.value = ''
  }
}

function resetSettingsToDefault() {
  const defaults = cloneDefaultSettings()

  Object.keys(defaults).forEach((key) => {
    settingsForm[key] = defaults[key]
  })

  settingsForm.email = adminEmail.value
  settingsForm.displayName = user.value?.displayName || defaults.displayName

  persistSettings()
  setInfoMessage('Settings were reset to default values.')
}

</script>

<template>
  <div class="flex min-h-screen bg-[#F8F9FB] overflow-x-hidden dark:bg-[#0F1117]">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="app-page-wrap">
        <header class="app-surface-card app-section-padding">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <h1 class="typo-page-title">Settings</h1>
              <p class="mt-2 typo-body max-w-3xl">
                Configure administrator defaults for scheduling, guide assignment support, notifications,
                and security controls. Settings are frontend-only and are stored locally in this browser.
              </p>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 xl:max-w-sm dark:border-white/10 dark:bg-[#1C2333] dark:text-slate-300">
              <p class="font-semibold text-slate-900 dark:text-slate-100">Current Admin</p>
              <p class="mt-1 break-all">{{ adminEmail }}</p>
              <p class="mt-2 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-500">
                {{ adminRole }} - {{ adminStatus }}
              </p>
            </div>
          </div>

        </header>

        <p
          v-if="infoMessage"
          class="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700 dark:border-sky-800 dark:bg-sky-950/60 dark:text-sky-300"
        >
          {{ infoMessage }}
        </p>

        <div class="grid grid-cols-1 gap-5 2xl:grid-cols-[minmax(0,1fr)_360px]">
          <div class="space-y-5">
            <section class="app-surface-card app-section-padding">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="typo-section-title">Administrator Profile</h2>
                  <p class="mt-1 typo-muted">
                    Identity and localization used across notifications and operational views.
                  </p>
                </div>
                <SaveButton
                  label="Save Profile"
                  :disabled="savingSectionName === 'Profile'"
                  @save="saveSection('Profile')"
                />
              </div>

              <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
                <label class="block">
                  <span class="mb-1 block typo-card-label">Display Name</span>
                  <input
                    v-model="settingsForm.displayName"
                    type="text"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                  />
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Email Address</span>
                  <input
                    v-model="settingsForm.email"
                    type="email"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                  />
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Language</span>
                  <select
                    v-model="settingsForm.language"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>English (US)</option>
                    <option>English (UK)</option>
                    <option>Portuguese (BR)</option>
                    <option>Spanish (ES)</option>
                  </select>
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Timezone</span>
                  <select
                    v-model="settingsForm.timezone"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>America/Sao_Paulo</option>
                    <option>America/New_York</option>
                    <option>Europe/London</option>
                  </select>
                </label>
              </div>
            </section>

            <section class="app-surface-card app-section-padding">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="typo-section-title">Scheduling and Assignment Defaults</h2>
                  <p class="mt-1 typo-muted">
                    Operational controls aligned with guide assignment and schedule orchestration.
                  </p>
                </div>
                <SaveButton
                  label="Save Scheduling"
                  :disabled="savingSectionName === 'Scheduling'"
                  @save="saveSection('Scheduling')"
                />
              </div>

              <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
                <label class="block">
                  <span class="mb-1 block typo-card-label">Reservation Approval</span>
                  <select
                    v-model="settingsForm.reservationApproval"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>Manual review</option>
                    <option>Automatic when schedule exists</option>
                  </select>
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Scheduling Lead Time</span>
                  <select
                    v-model="settingsForm.scheduleLeadTime"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>12 hours</option>
                    <option>24 hours</option>
                    <option>48 hours</option>
                  </select>
                </label>

                <label class="block md:col-span-2">
                  <span class="mb-1 block typo-card-label">Conflict Policy</span>
                  <select
                    v-model="settingsForm.scheduleConflictPolicy"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>Warn and require confirmation</option>
                    <option>Block operation</option>
                    <option>Allow and log warning</option>
                  </select>
                </label>
              </div>

              <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input
                    v-model="settingsForm.allowUnassignedSchedules"
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20"
                  />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Allow unassigned schedules</span>
                    <span class="mt-1 block typo-caption">Allow schedule creation before a guide is assigned.</span>
                  </span>
                </label>

                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input
                    v-model="settingsForm.autoEscalateUnassignable"
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20"
                  />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Auto-escalate unassignable schedules</span>
                    <span class="mt-1 block typo-caption">Generate priority alerts when no guide satisfies constraints.</span>
                  </span>
                </label>
              </div>
            </section>

            <section class="app-surface-card app-section-padding">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="typo-section-title">Notification Preferences</h2>
                  <p class="mt-1 typo-muted">
                    Choose which operational events generate admin notifications.
                  </p>
                </div>
                <SaveButton
                  label="Save Notifications"
                  :disabled="savingSectionName === 'Notifications'"
                  @save="saveSection('Notifications')"
                />
              </div>

              <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input v-model="settingsForm.notifyDailyDigest" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20" />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Daily digest</span>
                    <span class="mt-1 block typo-caption">Summary of reservations, assignments, and incidents.</span>
                  </span>
                </label>

                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input v-model="settingsForm.notifyNewBookings" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20" />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">New booking alerts</span>
                    <span class="mt-1 block typo-caption">Alert when reservations require operational follow-up.</span>
                  </span>
                </label>

                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input v-model="settingsForm.notifyOverbookingRisk" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20" />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Overbooking risk alerts</span>
                    <span class="mt-1 block typo-caption">Warn when reservations indicate capacity pressure.</span>
                  </span>
                </label>

                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input v-model="settingsForm.notifyGuideAvailabilityRisk" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20" />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Guide availability risk alerts</span>
                    <span class="mt-1 block typo-caption">Alert when schedules are likely to become unassignable.</span>
                  </span>
                </label>
              </div>
            </section>
          </div>

          <aside class="space-y-5">
            <section class="app-surface-card app-section-padding">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="typo-section-title">Security and Access</h2>
                  <p class="mt-1 typo-muted">
                    Baseline controls for administrator access and session safety.
                  </p>
                </div>
                <SaveButton
                  label="Save Security"
                  :disabled="savingSectionName === 'Security'"
                  @save="saveSection('Security')"
                />
              </div>

              <div class="mt-5 space-y-4">
                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input v-model="settingsForm.requireTwoFactor" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20" />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Require two-factor authentication</span>
                    <span class="mt-1 block typo-caption">Recommended for all administrative sessions.</span>
                  </span>
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Session Timeout</span>
                  <select
                    v-model="settingsForm.sessionTimeout"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>15 minutes</option>
                    <option>30 minutes</option>
                    <option>60 minutes</option>
                  </select>
                </label>

                <label class="block">
                  <span class="mb-1 block typo-card-label">Password Reset Policy</span>
                  <select
                    v-model="settingsForm.passwordResetPolicy"
                    class="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  >
                    <option>Email only</option>
                    <option>Email plus admin approval</option>
                  </select>
                </label>

                <label class="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]">
                  <input
                    v-model="settingsForm.allowAdminDataExport"
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-slate-300 accent-[#0077B6] dark:border-white/20"
                  />
                  <span>
                    <span class="block text-sm font-semibold text-slate-900 dark:text-slate-100">Allow admin data exports</span>
                    <span class="mt-1 block typo-caption">Enable only when governance controls are met.</span>
                  </span>
                </label>
              </div>
            </section>

            <section class="app-surface-card app-section-padding">
              <h2 class="typo-section-title">Assignment Policy Snapshot</h2>
              <p class="mt-1 typo-muted">
                Quick view of current frontend defaults for scheduling and assignment behavior.
              </p>

              <dl class="mt-5 space-y-3">
                <div
                  v-for="item in policySummary"
                  :key="item.label"
                  class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-[#1C2333]"
                >
                  <dt class="typo-card-label">{{ item.label }}</dt>
                  <dd class="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">{{ item.value }}</dd>
                  <p class="mt-1 typo-caption">{{ item.note }}</p>
                </div>
              </dl>
            </section>

            <section class="app-surface-card app-section-padding">
              <h2 class="typo-section-title">Reset</h2>
              <p class="mt-1 typo-muted">Revert all local frontend settings to their default values.</p>
              <button
                type="button"
                class="mt-4 w-full rounded-xl border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 dark:border-red-800 dark:bg-red-950/50 dark:text-red-400 dark:hover:bg-red-950/80"
                @click="resetSettingsToDefault"
              >
                Reset to defaults
              </button>
            </section>
          </aside>
        </div>
      </section>
    </main>
  </div>
</template>
