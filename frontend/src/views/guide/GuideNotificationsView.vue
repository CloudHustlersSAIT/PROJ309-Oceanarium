<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-3 sm:items-center">
        <div>
          <h1 class="app-title">Notifications</h1>
          <p class="app-subtitle">Recent updates for your guide account</p>
        </div>

        <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:gap-3">
          <button
            class="app-btn-ghost"
            :disabled="loading || unreadCount === 0"
            @click="markAllRead"
          >
            Mark all as read
          </button>
          <button
            class="app-btn-sky"
            :disabled="loading"
            @click="loadNotifications"
          >
            Refresh
          </button>
        </div>
      </div>

      <div class="mt-5 grid gap-4 md:grid-cols-3">
        <div class="app-stat-card">
          <p class="typo-card-label">Unread</p>
          <p class="typo-card-value">{{ unreadCount }}</p>
        </div>
        <div class="app-stat-card">
          <p class="typo-card-label">Urgent</p>
          <p class="typo-card-value">{{ urgentCount }}</p>
        </div>
        <div class="app-stat-card">
          <p class="typo-card-label">Action Required</p>
          <p class="typo-card-value">{{ actionRequiredCount }}</p>
        </div>
      </div>

      <div class="mt-5 grid gap-3 lg:grid-cols-4">
        <label class="block">
          <span class="app-form-label">Channel</span>
          <select
            v-model="filters.channel"
            class="app-form-select"
          >
            <option value="">All channels</option>
            <option value="PORTAL">Portal</option>
            <option value="EMAIL">Email</option>
          </select>
        </label>

        <label class="block">
          <span class="app-form-label">Priority</span>
          <select
            v-model="filters.priority"
            class="app-form-select"
          >
            <option value="">All priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="normal">Normal</option>
            <option value="low">Low</option>
          </select>
        </label>

        <label class="block">
          <span class="app-form-label">Event Type</span>
          <select
            v-model="filters.eventType"
            class="app-form-select"
          >
            <option value="">All event types</option>
            <option v-for="option in eventTypeOptions" :key="option" :value="option">
              {{ formatEventType(option) }}
            </option>
          </select>
        </label>

        <label class="app-stat-card flex items-end gap-3 px-4 py-3">
          <input v-model="filters.unreadOnly" type="checkbox" class="h-4 w-4 rounded border-line-sky text-brand" />
          <span class="app-form-label mb-0">Unread only</span>
        </label>
      </div>

      <div class="mt-5 space-y-3">
        <div v-if="loading" class="typo-muted">Loading notifications...</div>
        <div v-else-if="error" class="app-text-error">{{ error }}</div>

        <template v-else>
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="p-3.5 sm:p-4"
            :class="notificationCardClass(notification)"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="app-body-title leading-snug">
                  {{ notification.message }}
                </p>
                <p class="mt-1 text-sm font-medium text-black/70 dark:text-slate-300">
                  {{ notification.time }}
                </p>
                <p v-if="notification.meta" class="mt-1 text-sm text-black/55 dark:text-slate-400">
                  {{ notification.meta }}
                </p>
              </div>

              <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
                <button
                  type="button"
                  class="app-btn-sky"
                  :disabled="actionId === notification.id"
                  @click="viewDetails(notification.id)"
                >
                  {{ actionId === notification.id ? 'Loading...' : 'View details' }}
                </button>
                <button
                  v-if="!notification.read"
                  type="button"
                  class="app-btn-sky"
                  :disabled="actionId === notification.id"
                  @click="markSingleRead(notification.id)"
                >
                  Mark as read
                </button>
              </div>
            </div>
          </div>

          <div v-if="notifications.length === 0" class="text-sm text-black/60 dark:text-slate-400">
            You are all caught up.
          </div>
        </template>
      </div>

      <div class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-black/10 pt-4 dark:border-white/10">
        <p class="text-sm text-black/60 dark:text-slate-400">
          Showing {{ pagination.offset + 1 }}-{{ Math.min(pagination.offset + notifications.length, pagination.offset + pagination.limit) }}
          of {{ pagination.total }}
        </p>

        <div class="flex items-center gap-2">
          <button
            class="app-btn-ghost"
            :disabled="loading || pagination.offset === 0"
            @click="prevPage"
          >
            Prev
          </button>
          <button
            class="app-btn-ghost"
            :disabled="loading || !pagination.hasMore"
            @click="nextPage"
          >
            Next
          </button>
        </div>
      </div>
    </section>

    <div
      v-if="detailOpen"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4"
      @click.self="closeDetail"
    >
      <div class="w-full max-w-2xl rounded-[28px] border border-line-sky-light bg-surface-card p-6 shadow-[0_20px_50px_rgba(0,0,0,0.18)] dark:border-white/10 dark:shadow-black/40">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="typo-modal-title">Notification Details</h2>
            <p class="mt-1 typo-muted">{{ selectedNotification?.createdAtLabel || '' }}</p>
          </div>

          <button
            type="button"
            class="app-btn-ghost"
            @click="closeDetail"
          >
            Close
          </button>
        </div>

        <div v-if="detailLoading" class="mt-5 text-sm text-black/60 dark:text-slate-400">Loading details...</div>
        <div v-else-if="detailError" class="mt-5 app-text-error">{{ detailError }}</div>
        <div v-else-if="selectedNotification" class="mt-5 space-y-4">
          <div class="app-stat-card">
            <p class="typo-card-label">Message</p>
            <p class="mt-2 app-body-title text-base">{{ selectedNotification.message }}</p>
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            <div class="app-stat-card">
              <p class="typo-card-label">Event Type</p>
              <p class="mt-2 app-body-title">{{ formatEventType(selectedNotification.eventType) }}</p>
            </div>
            <div class="app-stat-card">
              <p class="typo-card-label">Priority</p>
              <p class="mt-2 app-body-title">{{ selectedNotification.priorityLabel }}</p>
            </div>
            <div class="app-stat-card">
              <p class="typo-card-label">Channel</p>
              <p class="mt-2 app-body-title">{{ selectedNotification.channelLabel }}</p>
            </div>
            <div class="app-stat-card">
              <p class="typo-card-label">Schedule</p>
              <p class="mt-2 app-body-title">{{ selectedNotification.tourName || 'Not linked' }}</p>
            </div>
          </div>

          <div v-if="selectedNotification.detailText" class="app-stat-card">
            <p class="typo-card-label">Details</p>
            <p class="mt-2 whitespace-pre-wrap typo-body">{{ selectedNotification.detailText }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import {
  getNotificationDetail,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/services/api'

const loading = ref(false)
const error = ref('')
const actionId = ref(null)
const notifications = ref([])
const detailOpen = ref(false)
const detailLoading = ref(false)
const detailError = ref('')
const selectedNotification = ref(null)
const pagination = ref({ total: 0, limit: 10, offset: 0, hasMore: false })
const summary = ref({ unread_count: 0, urgent_count: 0, action_required_count: 0 })
const filters = ref({
  channel: 'PORTAL',
  priority: '',
  eventType: '',
  unreadOnly: false,
})

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

function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function formatEventType(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatLabel(value, fallback = '-') {
  const normalized = String(value || '').trim()
  if (!normalized) return fallback
  return normalized.replace(/_/g, ' ')
}

function normalizeNotification(notification) {
  const eventType = String(notification?.event_type || '').trim()
  const channel = String(notification?.channel || '').trim()
  const priority = String(notification?.priority || '').trim()
  const tourName = String(notification?.tour_name || '').trim()

  return {
    id: Number(notification?.id),
    message: String(notification?.message || 'Notification').trim(),
    time: formatRelativeTime(notification?.created_at),
    createdAtLabel: formatDateTime(notification?.created_at),
    read: Boolean(notification?.read_at),
    eventType,
    channel,
    priority,
    channelLabel: formatLabel(channel, 'Unknown'),
    priorityLabel: formatLabel(priority, 'Normal'),
    tourName,
    meta: [formatEventType(eventType), tourName, formatLabel(priority, '')].filter(Boolean).join(' - '),
  }
}

function normalizeNotificationDetail(notification) {
  const detail = notification?.detail
  let detailText = ''

  if (typeof detail === 'string') {
    detailText = detail
  } else if (detail && typeof detail === 'object') {
    detailText = JSON.stringify(detail, null, 2)
  }

  return {
    id: Number(notification?.id),
    message: String(notification?.message || 'Notification').trim(),
    createdAtLabel: formatDateTime(notification?.created_at),
    eventType: String(notification?.event_type || '').trim(),
    channelLabel: formatLabel(notification?.channel, 'Unknown'),
    priorityLabel: formatLabel(notification?.priority, 'Normal'),
    tourName: String(notification?.tour_name || '').trim(),
    detailText,
  }
}

const unreadCount = computed(() => Number(summary.value?.unread_count ?? 0))
const urgentCount = computed(() => Number(summary.value?.urgent_count ?? 0))
const actionRequiredCount = computed(() => Number(summary.value?.action_required_count ?? 0))
const eventTypeOptions = computed(() => {
  const values = new Set(notifications.value.map((notification) => notification.eventType).filter(Boolean))
  return Array.from(values).sort((left, right) => left.localeCompare(right))
})

watch(
  unreadCount,
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
    const response = await getNotifications({
      channel: filters.value.channel || undefined,
      priority: filters.value.priority || undefined,
      eventType: filters.value.eventType || undefined,
      unreadOnly: filters.value.unreadOnly,
      limit: pagination.value.limit,
      offset: pagination.value.offset,
    })

    const rawNotifications = Array.isArray(response?.notifications) ? response.notifications : []

    notifications.value = rawNotifications.map(normalizeNotification)
    pagination.value = {
      total: Number(response?.pagination?.total ?? rawNotifications.length),
      limit: Number(response?.pagination?.limit ?? pagination.value.limit),
      offset: Number(response?.pagination?.offset ?? pagination.value.offset),
      hasMore: Boolean(response?.pagination?.has_more),
    }
    summary.value = {
      unread_count: Number(response?.summary?.unread_count ?? 0),
      urgent_count: Number(response?.summary?.urgent_count ?? 0),
      action_required_count: Number(response?.summary?.action_required_count ?? 0),
    }
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
    await loadNotifications()
  } catch (loadError) {
    error.value = loadError?.message || 'Failed to mark notifications as read.'
  }
}

async function markSingleRead(id) {
  actionId.value = id
  try {
    await markNotificationRead(id)
    await loadNotifications()
  } catch (loadError) {
    error.value = loadError?.message || 'Failed to mark notification as read.'
  } finally {
    actionId.value = null
  }
}

async function viewDetails(id) {
  actionId.value = id
  detailOpen.value = true
  detailLoading.value = true
  detailError.value = ''

  try {
    const response = await getNotificationDetail(id)
    selectedNotification.value = normalizeNotificationDetail(response)
    await loadNotifications()
  } catch (loadError) {
    selectedNotification.value = null
    detailError.value = loadError?.message || 'Failed to load notification details.'
  } finally {
    detailLoading.value = false
    actionId.value = null
  }
}

function closeDetail() {
  detailOpen.value = false
  detailLoading.value = false
  detailError.value = ''
  selectedNotification.value = null
}

function prevPage() {
  pagination.value.offset = Math.max(0, pagination.value.offset - pagination.value.limit)
  loadNotifications()
}

function nextPage() {
  if (!pagination.value.hasMore) return
  pagination.value.offset += pagination.value.limit
  loadNotifications()
}

function notificationCardClass(notification) {
  return notification.read ? 'notification-card' : 'notification-card-unread'
}

watch(
  () => [filters.value.channel, filters.value.priority, filters.value.eventType, filters.value.unreadOnly],
  () => {
    pagination.value.offset = 0
    loadNotifications()
  },
)

onMounted(async () => {
  await loadNotifications()
})
</script>