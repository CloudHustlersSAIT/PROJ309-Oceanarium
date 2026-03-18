<template>
  <button
    type="button"
    aria-label="Open guide menu"
    class="fixed left-4 top-4 z-40 flex h-10 w-10 items-center justify-center rounded-lg bg-[#0077B6] text-white shadow-lg transition hover:bg-[#0097E7] md:hidden"
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

  <div
    v-show="mobileOpen"
    aria-hidden="true"
    class="fixed inset-0 z-40 bg-black/50 md:hidden"
    @click="closeMobile"
  />

  <aside
    class="fixed inset-y-0 left-0 z-50 h-screen w-80 shrink-0 bg-gradient-to-b from-[#00B4D8] via-[#0F77C6] to-[#0E4EA8] text-white shadow-xl transform transition-transform duration-200 ease-out -translate-x-full md:sticky md:top-0 md:translate-x-0"
    :class="{ 'translate-x-0': mobileOpen }"
  >
    <div class="flex h-full flex-col p-4">
      <button
        type="button"
        aria-label="Close guide menu"
        class="absolute right-3 top-3 rounded-lg p-2 text-white/90 hover:bg-white/10 md:hidden"
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

      <div
        class="mb-8 rounded-2xl bg-white px-6 py-4 shadow-lg dark:bg-[#16304A]/90 dark:shadow-black/30"
      >
        <img :src="logoText" alt="Oceanarium" class="h-11 w-auto" />
      </div>

      <nav class="space-y-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center justify-between rounded-2xl px-4 py-3 text-base font-semibold transition"
          :class="linkClass(item.to)"
          @click="closeMobile"
        >
          <span class="flex items-center gap-3">
            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-white/12">
              <img
                :src="item.icon"
                :alt="item.label + ' icon'"
                class="h-4 w-4 brightness-0 invert"
              />
            </span>
            {{ item.label }}
          </span>
          <span
            v-if="item.to === '/guide/notifications' && unreadCount > 0"
            class="inline-flex min-w-[1.35rem] items-center justify-center rounded-full bg-[#E63946] px-1.5 py-0.5 text-[11px] font-bold leading-none text-white"
          >
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </RouterLink>
      </nav>

      <div class="mt-auto border-t border-white/25 pt-4">
        <div class="mb-3 flex items-center gap-3 px-1">
          <span
            class="flex h-12 w-12 items-center justify-center rounded-full bg-white/85 text-lg font-bold text-[#0E4EA8] dark:bg-white/15 dark:text-white"
          >
            {{ avatarInitial }}
          </span>
          <div class="min-w-0">
            <p class="text-sm text-white/80">Welcome,</p>
            <p class="truncate text-lg font-semibold">{{ userEmail }}</p>
          </div>
        </div>

        <button
          class="w-full rounded-xl bg-white px-4 py-2.5 text-lg font-bold text-[#0E4EA8] transition hover:bg-[#CAF0F8] dark:bg-white/12 dark:text-white dark:hover:bg-white/18"
          @click="handleLogout"
        >
          Log out
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/contexts/authContext'
import { useNotificationStore } from '@/stores/notification'
import { firebaseDisabled } from '@/utils/firebase'

import iconHome from '@/assets/icons/home.svg'
import iconCalendar from '@/assets/icons/calendar.svg'
import iconBookings from '@/assets/icons/bookings.svg'
import iconNotifications from '@/assets/icons/notifications.svg'
import iconSettings from '@/assets/icons/settings.svg'
import logoText from '@/assets/images/logo-text.svg'

const route = useRoute()
const router = useRouter()
const { user, logout } = useAuth()
const notificationStore = useNotificationStore()
const unreadCount = computed(() => notificationStore.unreadCount)
const mobileOpen = ref(false)

const navItems = [
  { label: 'Home', to: '/guide/home', icon: iconHome },
  { label: 'Schedule', to: '/guide/schedule', icon: iconCalendar },
  { label: 'Requests', to: '/guide/requests', icon: iconBookings },
  { label: 'Notifications', to: '/guide/notifications', icon: iconNotifications },
  { label: 'Profile', to: '/guide/profile', icon: iconSettings },
]

const userEmail = computed(() => (firebaseDisabled ? 'guest@local' : user?.value?.email || 'Guide'))
const avatarInitial = computed(() => userEmail.value?.charAt(0)?.toUpperCase() || 'G')

function closeMobile() {
  mobileOpen.value = false
}

function openMobile() {
  mobileOpen.value = true
}

onMounted(() => {
  notificationStore.loadSummary()
})

watch(
  () => route.path,
  () => {
    closeMobile()
  },
)

function linkClass(path) {
  const active = route.path === path

  return active ? 'bg-white/22 text-white' : 'text-white/95 hover:bg-white/12'
}

async function handleLogout() {
  closeMobile()
  localStorage.removeItem('role')
  notificationStore.summary = {
    total: 0,
    unread: 0,
    action_required: 0,
    by_priority: { urgent: 0, high: 0, normal: 0, low: 0 },
    by_event_type: {},
  }

  if (!firebaseDisabled) {
    await logout()
  }

  router.push('/login')
}
</script>
