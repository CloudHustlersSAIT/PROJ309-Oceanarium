<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-3 sm:items-center">
        <div>
          <h1 class="app-title">Notifications</h1>
          <p class="app-subtitle">Recent updates</p>
        </div>

        <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:gap-3">
          <button
            class="app-action-btn border border-black/15 text-[#1C1C1C] hover:bg-black/5 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="activeNotifications.length === 0"
            @click="archiveAllNotifications"
          >
            Archive all
          </button>
          <button
            class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB] disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="loading || activeUnreadCount === 0"
            @click="markAllRead"
          >
            Mark all as read
          </button>
        </div>
      </div>

      <div class="mt-4 overflow-x-auto pb-1">
        <div class="inline-flex rounded-xl border border-black/10 bg-white p-1">
          <button
            type="button"
            class="app-action-btn whitespace-nowrap"
            :class="
              viewMode === 'active'
                ? 'bg-[#CAF0F8] text-[#1C1C1C] ring-1 ring-[#00B4D8]/35'
                : 'text-black/75 hover:bg-black/5'
            "
            @click="viewMode = 'active'"
          >
            Active Notifications
          </button>
          <button
            type="button"
            class="app-action-btn whitespace-nowrap"
            :class="
              viewMode === 'archived'
                ? 'bg-[#CAF0F8] text-[#1C1C1C] ring-1 ring-[#00B4D8]/35'
                : 'text-black/75 hover:bg-black/5'
            "
            @click="viewMode = 'archived'"
          >
            Archived Notifications
          </button>
        </div>
      </div>

      <div class="mt-5 space-y-3">
        <div v-if="loading" class="text-sm text-black/60">Loading notifications...</div>
        <div v-else-if="error" class="text-sm font-medium text-[#B91C1C]">{{ error }}</div>

        <template v-else>
          <div
            v-for="notification in visibleNotifications"
            :key="notification.id"
            class="p-3.5 sm:p-4"
            :class="notificationCardClass(notification)"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="app-body-title leading-snug">
                  {{ notification.message }}
                </p>
                <p class="mt-1 text-sm font-medium text-black/70">
                  {{ notification.time }}
                </p>
                <p v-if="notification.meta" class="mt-1 text-sm text-black/55">
                  {{ notification.meta }}
                </p>
              </div>

              <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
                <button
                  v-if="!notification.archived && !notification.read"
                  type="button"
                  class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
                  :disabled="actionId === notification.id"
                  @click="markSingleRead(notification.id)"
                >
                  Mark as read
                </button>
                <button
                  v-if="!notification.archived"
                  type="button"
                  class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
                  @click="archiveNotification(notification.id)"
                >
                  Archive
                </button>
                <button
                  v-else
                  type="button"
                  class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
                  @click="restoreNotification(notification.id)"
                >
                  Restore
                </button>
                <button
                  type="button"
                  class="app-action-btn border border-[#E63946]/45 bg-[#FFF1F2] text-[#B91C1C] hover:bg-[#FFE4E6]"
                  @click="deleteNotification(notification.id)"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          <div v-if="visibleNotifications.length === 0" class="text-sm text-black/60">
            {{ viewMode === 'active' ? "You're all caught up!" : 'No archived notifications yet.' }}
          </div>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/services/api'

const LOCAL_ARCHIVE_KEY = 'guideArchivedNotifications'
const LOCAL_DELETE_KEY = 'guideDeletedNotifications'

const notifications = ref([])
const viewMode = ref('active')
const loading = ref(false)
const error = ref('')
const actionId = ref(null)
const archivedIds = ref(loadIdSet(LOCAL_ARCHIVE_KEY))
const deletedIds = ref(loadIdSet(LOCAL_DELETE_KEY))

function loadIdSet(key) {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) || '[]')
    return Array.isArray(parsed) ? parsed.map(Number).filter((value) => Number.isInteger(value) && value > 0) : []
  } catch {
    return []
  }
}

function persistIdSet(key, values) {
  window.localStorage.setItem(key, JSON.stringify(values))
}

function formatRelativeTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  const diffMs = Date.now() - date.getTime()
  const diffMinutes = Math.max(0, Math.round(diffMs / 60000))

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`

  const diffDays = Math.round(diffHours / 24)
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatEventType(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function normalizeNotification(notification) {
  const id = Number(notification?.id)
  const createdAt = notification?.created_at || notification?.createdAt || null
  const eventType = String(notification?.event_type || '').trim()
  const channel = String(notification?.channel || '').trim()
  const tourName = String(notification?.tour_name || '').trim()
  const priority = String(notification?.priority || '').trim()

  const metaParts = [formatEventType(eventType)]
  if (tourName) metaParts.push(tourName)
  if (channel) metaParts.push(channel)
  if (priority) metaParts.push(priority)

  return {
    id,
    message: String(notification?.message || 'Notification').trim(),
    time: formatRelativeTime(createdAt),
    read: Boolean(notification?.read_at || notification?.readAt),
    archived: archivedIds.value.includes(id),
    meta: metaParts.filter(Boolean).join(' • '),
  }
}

const visibleSourceNotifications = computed(() =>
  notifications.value.filter((notification) => !deletedIds.value.includes(notification.id)),
)

const activeNotifications = computed(() => visibleSourceNotifications.value.filter((n) => !n.archived))
const archivedNotifications = computed(() => visibleSourceNotifications.value.filter((n) => n.archived))
const visibleNotifications = computed(() =>
  viewMode.value === 'active' ? activeNotifications.value : archivedNotifications.value,
)
const activeUnreadCount = computed(() => activeNotifications.value.filter((n) => !n.read).length)

watch(
  activeUnreadCount,
  (count) => {
    localStorage.setItem('guideUnreadNotifications', String(count))
    window.dispatchEvent(new CustomEvent('guide-unread-updated', { detail: count }))
  },
  { immediate: true },
)

async function loadNotifications() {
  loading.value = true
  error.value = ''

  try {
    const response = await getNotifications()
    const rawNotifications = Array.isArray(response)
      ? response
      : Array.isArray(response?.notifications)
        ? response.notifications
        : []

    notifications.value = rawNotifications
      .filter((notification) => String(notification?.channel || '').toUpperCase() === 'PORTAL')
      .map(normalizeNotification)
  } catch (loadError) {
    notifications.value = []
    error.value = loadError?.message || 'Failed to load notifications.'
  } finally {
    loading.value = false
  }
}

async function markAllRead() {
  try {
    await markAllNotificationsRead()
    notifications.value = notifications.value.map((notification) => ({ ...notification, read: true }))
  } catch (loadError) {
    error.value = loadError?.message || 'Failed to mark notifications as read.'
  }
}

async function markSingleRead(id) {
  actionId.value = id
  try {
    await markNotificationRead(id)
    notifications.value = notifications.value.map((notification) =>
      notification.id === id ? { ...notification, read: true } : notification,
    )
  } catch (loadError) {
    error.value = loadError?.message || 'Failed to mark notification as read.'
  } finally {
    actionId.value = null
  }
}

function archiveNotification(id) {
  if (!archivedIds.value.includes(id)) {
    archivedIds.value = [...archivedIds.value, id]
    persistIdSet(LOCAL_ARCHIVE_KEY, archivedIds.value)
    notifications.value = notifications.value.map((notification) =>
      notification.id === id ? { ...notification, archived: true } : notification,
    )
  }
}

function restoreNotification(id) {
  archivedIds.value = archivedIds.value.filter((value) => value !== id)
  persistIdSet(LOCAL_ARCHIVE_KEY, archivedIds.value)
  notifications.value = notifications.value.map((notification) =>
    notification.id === id ? { ...notification, archived: false } : notification,
  )
}

function deleteNotification(id) {
  if (!deletedIds.value.includes(id)) {
    deletedIds.value = [...deletedIds.value, id]
    persistIdSet(LOCAL_DELETE_KEY, deletedIds.value)
  }
}

function archiveAllNotifications() {
  const nextArchived = Array.from(new Set([...archivedIds.value, ...activeNotifications.value.map((item) => item.id)]))
  archivedIds.value = nextArchived
  persistIdSet(LOCAL_ARCHIVE_KEY, archivedIds.value)
  notifications.value = notifications.value.map((notification) => ({ ...notification, archived: true }))
}

function notificationCardClass(notification) {
  return notification.read ? 'notification-card' : 'notification-card-unread'
}

onMounted(async () => {
  await loadNotifications()
})
</script>
