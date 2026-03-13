<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../contexts/authContext'

import SidebarButton from './SidebarButton.vue'

const router = useRouter()
const route = useRoute()
const { user, logout } = useAuth()

// Mobile drawer: closed by default on small screens; sidebar becomes overlay
const mobileOpen = ref(false)
function closeMobile() {
  mobileOpen.value = false
}
function openMobile() {
  mobileOpen.value = true
}

// Close drawer when route changes (e.g. user navigates from calendar to home on mobile).
watch(
  () => route.path,
  () => {
    closeMobile()
  },
)

//Import icons
import iconHome from '../assets/icons/home.svg'
import iconDashboard from '../assets/icons/dashboards.svg'
import iconNotifications from '../assets/icons/notifications.svg'
import iconAssets from '../assets/icons/assets.svg'
import iconBookings from '../assets/icons/bookings.svg'
import iconCalendar from '../assets/icons/calendar.svg'
import iconSettings from '../assets/icons/settings.svg'

// Navigation items — use the imported icon variables
const navItems = [
  { label: 'Home', to: 'home', icon: iconHome },
  { label: 'Dashboard', to: 'dashboard', icon: iconDashboard },
  { label: 'Notifications', to: 'notifications', icon: iconNotifications },
  { label: 'Assets', to: 'assets', icon: iconAssets },
  { label: 'Reservation', to: 'bookings', icon: iconBookings },
  { label: 'Calendar', to: 'calendar', icon: iconCalendar },
  { label: 'Settings', to: 'settings', icon: iconSettings },
]

// Derive a friendly display name from Firebase user
const displayName = computed(() => {
  if (!user.value) return 'Guest'
  return user.value.displayName || user.value.email || 'User'
})

// First letter for avatar circle
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
  <div class="hidden md:block w-80 shrink-0" aria-hidden="true" />

  <button
    type="button"
    aria-label="Open menu"
    class="fixed left-4 top-4 z-30 flex md:hidden h-10 w-10 items-center justify-center rounded-lg bg-[#0077B6] text-white shadow-lg hover:bg-[#0097e7] transition"
    @click="openMobile"
  >
    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 6h16M4 12h16M4 18h16"
      />
    </svg>
  </button>

  <!-- Backdrop when sidebar open on mobile: tap to close -->
  <div
    v-show="mobileOpen"
    aria-hidden="true"
    class="fixed inset-0 z-40 bg-black/50 md:hidden"
    @click="closeMobile"
  />

  <!-- Sidebar: drawer on mobile (fixed, slide-in), normal on md+ -->
  <aside
    class="w-80 max-w-[85vw] min-h-dvh md:h-screen md:max-h-screen md:max-w-none flex flex-col p-4 bg-linear-to-b from-[#00B4D8] to-[#0047ab] text-white shadow-lg fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-out -translate-x-full md:translate-x-0 overflow-y-auto md:overflow-hidden"
    :class="{ 'translate-x-0': mobileOpen }"
  >
    <!-- Close button for mobile (visible only when drawer is open) -->
    <button
      type="button"
      aria-label="Close menu"
      class="absolute right-3 top-3 p-2 rounded-lg md:hidden text-white/90 hover:bg-white/10"
      @click="closeMobile"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
    <div class="mb-6 md:mb-8">
      <div
        class="items-center bg-white rounded-xl px-10 py-4 drop-shadow-xl/25 flex justify-center"
      >
        <img src="/src/assets/images/logo-text.svg" alt="Company logo text" class="h-10 w-auto" />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col">
      <!-- Navigation -->
      <nav class="flex-1 space-y-1 mt-2 overflow-y-auto pr-1">
        <SidebarButton
          v-for="item in navItems"
          :key="item.to"
          :label="item.label"
          :to="item.to"
          :icon="item.icon"
        />
      </nav>

      <!-- Bottom user info -->
      <div class="mt-6 border-t border-white/20 pt-4">
        <div class="flex items-center gap-3 mb-3 px-1">
          <!-- Avatar circle -->
          <div
            class="h-10 w-10 rounded-full bg-white/90 text-[#0077B6] flex items-center justify-center text-lg font-semibold shadow-md"
          >
            {{ avatarInitial }}
          </div>

          <div class="flex flex-col">
            <span class="text-xs opacity-80">Welcome,</span>
            <span class="text-sm font-semibold truncate max-w-36">
              {{ displayName }}
            </span>
          </div>
        </div>

        <!-- Logout button -->
        <button
          type="button"
          class="w-full py-2.5 rounded-xl text-sm font-semibold bg-white text-[#0077B6] hover:bg-[#CAF0F8] hover:text-[#0077B6] transition shadow-sm"
          @click="handleLogout"
        >
          Log out
        </button>
      </div>
    </div>
  </aside>
</template>
