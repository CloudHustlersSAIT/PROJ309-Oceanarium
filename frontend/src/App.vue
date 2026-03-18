<!-- src/App.vue -->
<template>
  <router-view />
  <AppToast />
</template>

<script setup>
import { watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import AppToast from '@/components/AppToast.vue'
import { useAuth } from '@/contexts/authContext'
import { useNotificationPoller } from '@/composables/useNotificationPoller'

const route = useRoute()
const { user, role } = useAuth()
const { startPolling, stopPolling } = useNotificationPoller({ role: 'admin' })

watch(
  () => [user.value, role.value, route.path],
  () => {
    const isAdmin = user.value && role.value === 'admin'
    const isAdminRoute =
      !route.path.startsWith('/guide') &&
      !route.path.startsWith('/login') &&
      !route.path.startsWith('/forgot')
    if (isAdmin && isAdminRoute) {
      startPolling()
    } else {
      stopPolling()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  stopPolling()
})
</script>
