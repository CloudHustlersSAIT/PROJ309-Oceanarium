<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../contexts/authContext'

import SidebarButton from './SidebarButton.vue'

const router = useRouter()
const { user, logout } = useAuth()

// Navigation items IF YOU WANT NEW BUTTONS, ADD THEM HERE
const navItems = [
  { label: 'Home', to: 'home', icon: '/src/assets/icons/home.svg' },
  { label: 'Dashboard', to: 'dashboard', icon: '/src/assets/icons/dashboards.svg' },
  // Add more here later
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

// Determine if a nav item is active
const isActive = (path) => route.path === path

async function handleLogout() {
  await logout()
  router.push('/login')
}
</script>

<template>
  <aside
    class="w-64 h-screen flex flex-col p-4 bg-gradient-to-b from-[#00B4D8] to-[#0047ab] text-white shadow-lg"
  >
    <!-- Logo -->
    <!-- Top: logo -->
    <div class="mb-10">
      <div
        class="items-center bg-white rounded-xl px-10 py-4 drop-shadow-xl/25 flex justify-center"
      >
        <img
          src="/src/assets/images/logo-text.svg"
          alt="Company logo text"
          class="h-10 w-auto drop-shadow-lg"
        />
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 space-y-1 mt-2">
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
          <span class="text-sm font-semibold truncate max-w-[9rem]">
            {{ displayName }}
          </span>
        </div>
      </div>

      <!-- Logout button -->
      <button
        type="button"
        @click="handleLogout"
        class="w-full py-2.5 rounded-xl text-sm font-semibold bg-white text-[#0077B6] hover:bg-[#CAF0F8] hover:text-[#0077B6] transition shadow-sm"
      >
        Log out
      </button>
    </div>
  </aside>
</template>
