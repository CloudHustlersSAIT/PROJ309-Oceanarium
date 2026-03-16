<template>
  <header class="sticky top-0 z-20 border-b border-black/10 bg-white/90 backdrop-blur dark:border-white/10 dark:bg-[#0F1117]/90 md:hidden">
    <div
      class="mx-auto flex max-w-6xl flex-nowrap items-center justify-between gap-3 overflow-hidden px-4 py-3.5 sm:px-6 lg:px-8"
    >
      <div class="flex min-w-0 flex-nowrap items-center gap-3 sm:gap-3.5">
        <img
          src="@/assets/images/logo.svg"
          alt="Oceanarium Logo"
          class="h-9 w-auto shrink-0 sm:h-10"
        />
        <div class="min-w-0 leading-tight">
          <p class="truncate text-base font-bold text-[#1C1C1C] dark:text-slate-100">Oceanarium Portal</p>
          <p class="truncate text-sm text-black/65 dark:text-slate-400">Guide</p>
        </div>
      </div>

      <button
        type="button"
        class="inline-flex items-center justify-center rounded-xl border border-black/15 bg-white px-3 py-2 text-sm font-semibold text-[#1C1C1C] transition hover:bg-[#CAF0F8]/50 dark:border-white/15 dark:bg-[#161B27] dark:text-slate-100 dark:hover:bg-white/5 md:hidden"
        aria-label="Open menu"
        @click="toggleMenu"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>
  </header>

  <transition
    enter-active-class="transition-opacity duration-200"
    leave-active-class="transition-opacity duration-200"
    enter-from-class="opacity-0"
    leave-to-class="opacity-0"
  >
    <div v-if="isMenuOpen" class="fixed inset-0 z-40 md:hidden">
      <button
        type="button"
        class="absolute inset-0 bg-black/40"
        aria-label="Close menu overlay"
        @click="closeMenu"
      ></button>

      <transition
        enter-active-class="transform transition duration-200 ease-out"
        leave-active-class="transform transition duration-200 ease-in"
        enter-from-class="translate-x-full"
        leave-to-class="translate-x-full"
      >
        <aside
          v-show="isMenuOpen"
          class="absolute right-0 top-0 h-full w-[86vw] max-w-sm border-l border-black/10 bg-white shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
        >
          <div class="flex h-full flex-col p-4">
            <div class="flex items-center justify-between">
              <p class="text-base font-bold text-[#1C1C1C] dark:text-slate-100">Guide Menu</p>
              <button
                type="button"
                class="rounded-lg border border-black/15 px-2.5 py-1.5 text-sm font-semibold text-black/70 hover:bg-black/5 dark:border-white/15 dark:text-slate-300 dark:hover:bg-white/5"
                @click="closeMenu"
              >
                Close
              </button>
            </div>

            <nav class="mt-4 space-y-2">
              <RouterLink
                to="/guide/home"
                class="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-base font-semibold transition"
                :class="linkClass('/guide/home')"
                @click="closeMenu"
              >
                Home
              </RouterLink>

              <RouterLink
                to="/guide/schedule"
                class="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-base font-semibold transition"
                :class="linkClass('/guide/schedule')"
                @click="closeMenu"
              >
                My Schedule
              </RouterLink>

              <RouterLink
                to="/guide/requests"
                class="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-base font-semibold transition"
                :class="linkClass('/guide/requests')"
                @click="closeMenu"
              >
                Requests
              </RouterLink>

              <RouterLink
                to="/guide/notifications"
                class="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-base font-semibold transition"
                :class="linkClass('/guide/notifications')"
                @click="closeMenu"
              >
                <span>Notifications</span>
                <span
                  v-if="unreadCount > 0"
                  class="inline-flex min-w-[1.35rem] items-center justify-center rounded-full bg-[#E63946] px-1.5 py-0.5 text-[11px] font-bold leading-none text-white"
                >
                  {{ unreadCount > 99 ? '99+' : unreadCount }}
                </span>
              </RouterLink>

              <RouterLink
                to="/guide/profile"
                class="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-base font-semibold transition"
                :class="linkClass('/guide/profile')"
                @click="closeMenu"
              >
                Profile
              </RouterLink>
            </nav>

            <div class="mt-auto rounded-xl border border-black/10 bg-black/[0.02] p-3 dark:border-white/10 dark:bg-white/[0.03]">
              <p class="text-sm text-black/60 dark:text-slate-400">Signed in as</p>
              <p class="text-base font-semibold break-all text-[#1C1C1C] dark:text-slate-100">{{ userEmail }}</p>

              <button
                class="mt-3 w-full rounded-xl bg-[#0077B6] px-4 py-2.5 text-base font-bold text-white hover:bg-[#0097E7] transition"
                @click="handleLogout"
              >
                Log out
              </button>
            </div>
          </div>
        </aside>
      </transition>
    </div>
  </transition>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/contexts/authContext'
import { firebaseDisabled } from '@/utils/firebase'

const route = useRoute()
const router = useRouter()
const { user, logout } = useAuth()
const unreadCount = ref(0)
const isMenuOpen = ref(false)

const userEmail = firebaseDisabled ? 'guest@local' : user?.value?.email || 'Guide'

function loadUnreadCountFromStorage() {
  const raw = localStorage.getItem('guideUnreadNotifications')
  const parsed = Number(raw)
  unreadCount.value = Number.isFinite(parsed) && parsed > 0 ? parsed : 0
}

function onUnreadUpdated(event) {
  const parsed = Number(event?.detail)
  unreadCount.value = Number.isFinite(parsed) && parsed > 0 ? parsed : 0
}

function onStorage(event) {
  if (event.key === 'guideUnreadNotifications') {
    loadUnreadCountFromStorage()
  }
}

onMounted(() => {
  loadUnreadCountFromStorage()
  window.addEventListener('guide-unread-updated', onUnreadUpdated)
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  window.removeEventListener('guide-unread-updated', onUnreadUpdated)
  window.removeEventListener('storage', onStorage)
})

watch(
  () => route.path,
  () => {
    isMenuOpen.value = false
  },
)

function linkClass(path) {
  const active = route.path === path

  return active
    ? 'bg-[#CAF0F8] text-[#0077B6] ring-1 ring-[#00B4D8]/40 dark:bg-sky-950/60 dark:text-sky-200 dark:ring-sky-700/40'
    : 'text-black hover:bg-[#CAF0F8]/60 hover:text-[#0077B6] dark:text-slate-300 dark:hover:bg-white/5 dark:hover:text-sky-200'
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
}

async function handleLogout() {
  closeMenu()
  localStorage.removeItem('role')
  localStorage.removeItem('guideUnreadNotifications')
  unreadCount.value = 0

  if (!firebaseDisabled) {
    await logout()
  }

  router.push('/login')
}
</script>
