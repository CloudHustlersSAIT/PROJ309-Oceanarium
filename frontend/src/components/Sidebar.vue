<script setup>
defineOptions({
  name: 'AppSidebar',
})

import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../contexts/authContext'

import SidebarButton from './SidebarButton.vue'

import iconHome from '../assets/icons/home.svg'
import iconDashboard from '../assets/icons/dashboards.svg'
import iconNotifications from '../assets/icons/notifications.svg'
import iconAssets from '../assets/icons/assets.svg'
import iconBookings from '../assets/icons/bookings.svg'
import iconCalendar from '../assets/icons/calendar.svg'
import iconSettings from '../assets/icons/settings.svg'

const router = useRouter()
const route = useRoute()
const { user, profile, logout } = useAuth()

const mobileOpen = ref(false)

function closeMobile() {
  mobileOpen.value = false
}

function openMobile() {
  mobileOpen.value = true
}

watch(
  () => route.path,
  () => {
    closeMobile()
  }
)

const navItems = [
  { label: 'Home', to: 'home', icon: iconHome },
  { label: 'Dashboard', to: 'dashboard', icon: iconDashboard },
  { label: 'Notifications', to: 'notifications', icon: iconNotifications },
  { label: 'Assets', to: 'assets', icon: iconAssets },
  { label: 'Bookings', to: 'bookings', icon: iconBookings },
  { label: 'Calendar', to: 'calendar', icon: iconCalendar },
  { label: 'Settings', to: 'settings', icon: iconSettings },
]

const displayName = computed(() => {
  if (profile.value?.first_name || profile.value?.last_name) {
    return `${profile.value.first_name || ''} ${profile.value.last_name || ''}`.trim()
  }

  if (!user.value) return 'Guest'

  return user.value.displayName || profile.value?.email || user.value.email || 'User'
})

const avatarInitial = computed(() => {
  const name = displayName.value
  return name ? name.charAt(0).toUpperCase() : '?'
})

async function handleLogout() {
  await logout()
  router.push('/login')
}
</script>

<template>
  <button
    type="button"
    aria-label="Open menu"
    class="fixed left-4 top-4 z-30 flex h-10 w-10 items-center justify-center rounded-lg bg-[#0077B6] text-white shadow-lg transition hover:bg-[#0097e7] md:hidden"
    @click="openMobile"
  >
    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  </button>

  <div
    v-show="mobileOpen"
    aria-hidden="true"
    class="fixed inset-0 z-40 bg-black/50 md:hidden"
    @click="closeMobile"
  />

  <aside
    class="fixed inset-y-0 left-0 z-50 flex h-screen w-80 -translate-x-full transform flex-col bg-gradient-to-b from-[#00B4D8] to-[#0047ab] p-4 text-white shadow-lg transition-transform duration-200 ease-out md:static md:translate-x-0"
    :class="{ 'translate-x-0': mobileOpen }"
  >
    <button
      type="button"
      aria-label="Close menu"
      class="absolute right-3 top-3 rounded-lg p-2 text-white/90 hover:bg-white/10 md:hidden"
      @click="closeMobile"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <div class="mb-10">
      <div class="flex items-center justify-center rounded-xl bg-white px-10 py-4 drop-shadow-xl/25">
        <img
          src="/src/assets/images/logo-text.svg"
          alt="Company logo text"
          class="h-10 w-auto"
        />
      </div>
    </div>

    <nav class="mt-2 flex-1 space-y-1">
      <SidebarButton
        v-for="item in navItems"
        :key="item.to"
        :label="item.label"
        :to="item.to"
        :icon="item.icon"
      />
    </nav>

    <div class="mt-6 border-t border-white/20 pt-4">
      <div class="mb-3 flex items-center gap-3 px-1">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-lg font-semibold text-[#0077B6] shadow-md"
        >
          {{ avatarInitial }}
        </div>

        <div class="flex flex-col">
          <span class="text-xs opacity-80">Welcome,</span>
          <span class="max-w-[9rem] truncate text-sm font-semibold">
            {{ displayName }}
          </span>
        </div>
      </div>

      <button
        type="button"
        class="w-full rounded-xl bg-white py-2.5 text-sm font-semibold text-[#0077B6] shadow-sm transition hover:bg-[#CAF0F8] hover:text-[#0077B6]"
        @click="handleLogout"
      >
        Log out
      </button>
    </div>
  </aside>
</template>
