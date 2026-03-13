<script setup>
import { reactive, ref } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import SaveButton from '../components/SaveButton.vue'

const profile = reactive({
  name: 'David Guerrero',
  email: 'admin@oceanarium.co',
  phone: '+55 12345678',
  language: 'English (US)',
})

const twoFactorEnabled = ref(true)
const notificationChannels = reactive({
  email: false,
  sms: false,
  whatsapp: false,
})

const infoMessage = ref('')

function setInfoMessage(message) {
  infoMessage.value = message
  window.setTimeout(() => {
    infoMessage.value = ''
  }, 4000)
}

function saveProfile() {
  setInfoMessage('Prototype mode: changes are visual only and not persisted yet.')
}

function sendResetLink(channel) {
  setInfoMessage(`Prototype mode: reset link simulation sent via ${channel}.`)
}

function openPrototypeLink(label) {
  setInfoMessage(`Prototype mode: "${label}" is not connected yet.`)
}
</script>

<template>
  <div class="flex min-h-screen bg-[#F8F9FB] overflow-x-hidden">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <div class="mb-5">
        <h1 class="text-3xl md:text-4xl font-semibold text-gray-800">Settings</h1>
        <p class="mt-1 text-sm text-gray-500">
          Prototype screen for layout and interaction validation.
        </p>
      </div>

      <p
        v-if="infoMessage"
        class="mb-4 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700"
      >
        {{ infoMessage }}
      </p>

      <div
        class="grid grid-cols-1 xl:grid-cols-[minmax(640px,1fr)_minmax(360px,420px)] gap-4 items-start"
      >
        <section class="space-y-4">
          <div class="bg-white border border-gray-200 shadow-sm rounded p-4">
            <h2 class="text-2xl font-semibold text-gray-900 mb-4">Profile Information</h2>
            <div class="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-5">
              <div class="flex flex-col items-center">
                <img
                  src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=240&q=80"
                  alt="Profile photo"
                  class="h-36 w-36 rounded-full object-cover border border-gray-200"
                />
                <p class="mt-3 text-sm text-gray-500">Change Profile Picture</p>
                <SaveButton class="mt-3" label="Save Changes" @save="saveProfile" />
              </div>

              <div class="space-y-3">
                <div>
                  <label
                    class="block mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase"
                    >Name</label
                  >
                  <input
                    v-model="profile.name"
                    type="text"
                    class="w-full rounded border border-gray-300 px-3 py-2 text-base"
                  />
                </div>

                <div>
                  <label
                    class="block mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase"
                    >Email Address</label
                  >
                  <input
                    v-model="profile.email"
                    type="email"
                    class="w-full rounded border border-gray-300 px-3 py-2 text-base"
                  />
                </div>

                <div>
                  <label
                    class="block mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase"
                    >Phone Number</label
                  >
                  <input
                    v-model="profile.phone"
                    type="text"
                    class="w-full rounded border border-gray-300 px-3 py-2 text-base"
                  />
                </div>

                <div>
                  <label
                    class="block mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase"
                    >Language</label
                  >
                  <select
                    v-model="profile.language"
                    class="w-full rounded border border-gray-300 px-3 py-2 text-base bg-white"
                  >
                    <option>English (US)</option>
                    <option>English (UK)</option>
                    <option>Portuguese (BR)</option>
                    <option>Spanish (ES)</option>
                  </select>
                </div>

                <div class="pt-1">
                  <SaveButton label="Save Profile" @save="saveProfile" />
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white border border-gray-200 shadow-sm rounded p-4">
            <h2 class="text-2xl font-semibold text-gray-900 mb-3">User Management</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
              <button
                type="button"
                class="rounded border border-gray-300 bg-gray-50 py-2 text-base hover:bg-gray-100"
                @click="openPrototypeLink('Add New Guide')"
              >
                Add New Guide
              </button>
              <button
                type="button"
                class="rounded border border-gray-300 bg-gray-50 py-2 text-base hover:bg-gray-100"
                @click="openPrototypeLink('View Guides')"
              >
                View Guides
              </button>
              <button
                type="button"
                class="rounded border border-gray-300 bg-gray-50 py-2 text-base hover:bg-gray-100"
                @click="openPrototypeLink('Guide Password Reset')"
              >
                Guide Password Reset
              </button>
              <button
                type="button"
                class="rounded border border-gray-300 bg-gray-50 py-2 text-base hover:bg-gray-100"
                @click="openPrototypeLink('Assign Guide')"
              >
                Assign Guide
              </button>
            </div>
          </div>

          <div class="bg-white border border-gray-200 shadow-sm rounded p-4">
            <h2 class="text-2xl font-semibold text-gray-900 mb-3">Notifications</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
              <label
                class="flex items-center gap-3 rounded border border-gray-300 bg-gray-50 px-3 py-2 text-base"
              >
                <input v-model="notificationChannels.email" type="checkbox" class="h-5 w-5" />
                Email
              </label>
              <label
                class="flex items-center gap-3 rounded border border-gray-300 bg-gray-50 px-3 py-2 text-base"
              >
                <input v-model="notificationChannels.sms" type="checkbox" class="h-5 w-5" />
                SMS
              </label>
              <label
                class="flex items-center gap-3 rounded border border-gray-300 bg-gray-50 px-3 py-2 text-base md:col-span-1"
              >
                <input v-model="notificationChannels.whatsapp" type="checkbox" class="h-5 w-5" />
                WhatsApp
              </label>
            </div>
            <SaveButton class="mt-3" label="Save Notification Preferences" @save="saveProfile" />
          </div>

          <div class="bg-white border border-gray-200 shadow-sm rounded p-4">
            <h2 class="text-2xl font-semibold text-gray-900 mb-3">Help &amp; Support</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-y-1 text-base text-gray-700">
              <button
                type="button"
                class="text-left hover:underline"
                @click="openPrototypeLink('API Status')"
              >
                API Status
              </button>
              <button
                type="button"
                class="text-left hover:underline"
                @click="openPrototypeLink('Report a Problem')"
              >
                Report a Problem
              </button>
              <button
                type="button"
                class="text-left hover:underline"
                @click="openPrototypeLink('Terms & Conditions')"
              >
                Terms &amp; Conditions
              </button>
              <button
                type="button"
                class="text-left hover:underline"
                @click="openPrototypeLink('Version Information')"
              >
                Version Information
              </button>
              <button
                type="button"
                class="text-left hover:underline"
                @click="openPrototypeLink('Privacy Policy')"
              >
                Privacy Policy
              </button>
            </div>
          </div>
        </section>

        <section class="space-y-4">
          <div class="bg-white border border-gray-200 shadow-sm rounded p-4">
            <h2 class="text-2xl font-semibold text-gray-900 mb-4">Password &amp; Security</h2>
            <label class="flex items-center gap-3 mb-4 text-base">
              <button
                type="button"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                :class="twoFactorEnabled ? 'bg-blue-600' : 'bg-gray-300'"
                @click="twoFactorEnabled = !twoFactorEnabled"
              >
                <span
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition"
                  :class="twoFactorEnabled ? 'translate-x-6' : 'translate-x-1'"
                />
              </button>
              Two-factor authentication (2FA)
            </label>

            <p class="text-base font-medium mb-2">Password Reset Link</p>
            <div class="flex flex-wrap gap-3 mb-5">
              <button
                type="button"
                class="rounded bg-sky-500 px-4 py-2 text-white text-sm font-medium"
                @click="sendResetLink('Email')"
              >
                Send Via Email
              </button>
              <button
                type="button"
                class="rounded bg-sky-500 px-4 py-2 text-white text-sm font-medium"
                @click="sendResetLink('SMS')"
              >
                Send Via SMS
              </button>
            </div>

            <p class="text-sm text-gray-700 mb-1">
              Recovery Phone: <span class="text-[#8D97FF]">+55 12345678</span>
            </p>
            <p class="text-sm text-gray-700">
              Recovery Email: <span class="text-[#8D97FF]">+55 12345678</span>
            </p>

            <SaveButton class="mt-4" label="Save Security Settings" @save="saveProfile" />
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
