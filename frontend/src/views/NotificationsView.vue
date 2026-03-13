<script setup>
import { computed, onMounted, ref } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import { getNotifications } from '../services/api'

const NOTIFICATION_UI_CACHE_KEY = 'admin-notification-ui-v1'

const lifecycleTabs = [
  { key: 'active', label: 'Active' },
  { key: 'archived', label: 'Archived' },
  { key: 'trash', label: 'Trash' },
]

const readFilterOptions = [
  { value: 'all', label: 'All read states' },
  { value: 'unread', label: 'Unread only' },
  { value: 'read', label: 'Read only' },
]

const activeTab = ref('active')
const readFilter = ref('all')
const searchQuery = ref('')
const feedbackMessage = ref('')
const notifications = ref([])
const loading = ref(false)
const error = ref('')

const totalCount = computed(() => notifications.value.length)
const unreadCount = computed(() =>
  notifications.value.filter((notification) => notification.lifecycle === 'active' && !notification.read)
    .length,
)

const notificationCounts = computed(() => ({
  active: notifications.value.filter((notification) => notification.lifecycle === 'active').length,
  archived: notifications.value.filter((notification) => notification.lifecycle === 'archived').length,
  trash: notifications.value.filter((notification) => notification.lifecycle === 'trash').length,
}))

const summaryCards = computed(() => [
  {
    label: 'Total Feed',
    value: totalCount.value,
    note: 'All loaded notifications',
  },
  {
    label: 'Unread',
    value: unreadCount.value,
    note: 'Still need attention',
  },
  {
    label: 'Active',
    value: notificationCounts.value.active,
    note: 'Current working set',
  },
  {
    label: 'Archived',
    value: notificationCounts.value.archived,
    note: 'Hidden from active flow',
  },
])

const visibleRows = computed(() => {
  const normalizedQuery = searchQuery.value.trim().toLowerCase()

  return notifications.value.filter((notification) => {
    const matchesLifecycle = notification.lifecycle === activeTab.value
    const matchesReadState =
      readFilter.value === 'all' ||
      (readFilter.value === 'read' && notification.read) ||
      (readFilter.value === 'unread' && !notification.read)
    const searchableContent = [
      notification.message,
      notification.eventType,
      notification.eventTypeLabel,
      notification.scheduleId,
      notification.channel,
      notification.channelLabel,
      notification.status,
      notification.statusLabel,
    ]
      .join(' ')
      .toLowerCase()
    const matchesSearch = !normalizedQuery || searchableContent.includes(normalizedQuery)

    return matchesLifecycle && matchesReadState && matchesSearch
  })
})

function loadNotificationUiCache() {
  if (typeof window === 'undefined') return {}

  try {
    const raw = window.localStorage.getItem(NOTIFICATION_UI_CACHE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function persistNotificationUiCache() {
  if (typeof window === 'undefined') return

  try {
    const cache = Object.fromEntries(
      notifications.value.map((notification) => [
        String(notification.id),
        {
          read: Boolean(notification.read),
          lifecycle: notification.lifecycle,
        },
      ]),
    )
    window.localStorage.setItem(NOTIFICATION_UI_CACHE_KEY, JSON.stringify(cache))
  } catch {
    // Keep notifications usable even when storage is unavailable.
  }
}

function normalizeLifecycle(value) {
  if (value === 'archived' || value === 'trash') return value
  return 'active'
}

function inferIcon(eventType, message) {
  const normalizedEventType = String(eventType || '').trim().toLowerCase()
  const normalizedMessage = String(message || '').trim().toLowerCase()

  if (normalizedEventType.includes('swap') || normalizedMessage.includes('swap')) return 'swap'
  if (normalizedEventType.includes('assign') || normalizedMessage.includes('assign')) return 'assign'
  if (normalizedEventType.includes('cancel') || normalizedMessage.includes('cancel')) return 'cancel'
  if (normalizedEventType.includes('move') || normalizedMessage.includes('moved')) return 'move'
  return 'warning'
}

function formatTimeAgo(value) {
  if (!value) return 'Recently'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'Recently'

  const diffMs = Date.now() - parsed.getTime()
  const diffMinutes = Math.max(1, Math.floor(diffMs / 60000))

  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`

  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
}

function formatDateTime(value) {
  if (!value) return 'Not sent yet'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'Invalid date'

  return parsed.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatEnumLabel(value) {
  const normalizedValue = String(value || '').trim()
  if (!normalizedValue) return 'Unknown'

  return normalizedValue
    .toLowerCase()
    .split('_')
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')
}

function eventTypeBadgeClass(eventType) {
  const normalizedEventType = String(eventType || '').trim().toLowerCase()

  if (normalizedEventType.includes('cancel')) {
    return 'border-red-200 bg-red-50 text-red-700'
  }
  if (normalizedEventType.includes('warning')) {
    return 'border-amber-200 bg-amber-50 text-amber-700'
  }
  if (normalizedEventType.includes('assign') || normalizedEventType.includes('move')) {
    return 'border-sky-200 bg-sky-50 text-sky-700'
  }
  return 'border-slate-200 bg-slate-50 text-slate-700'
}

function statusBadgeClass(status) {
  const normalizedStatus = String(status || '').trim().toLowerCase()

  if (normalizedStatus === 'sent') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  }
  if (normalizedStatus === 'failed' || normalizedStatus === 'error') {
    return 'border-red-200 bg-red-50 text-red-700'
  }
  return 'border-slate-200 bg-slate-50 text-slate-700'
}

function normalizeNotification(item, uiCache) {
  const id = Number(item?.id)
  const cacheEntry = uiCache[String(id)] || {}
  const message = String(item?.message || 'Notification received').trim()
  const eventType = String(item?.event_type || item?.eventType || 'system').trim() || 'system'
  const scheduleId = item?.schedule_id ?? item?.scheduleId ?? null
  const createdAt = item?.created_at || item?.createdAt || null
  const sentAt = item?.sent_at || item?.sentAt || null
  const channel = String(item?.channel || 'PORTAL').trim() || 'PORTAL'
  const status = String(item?.status || 'SENT').trim() || 'SENT'

  return {
    id,
    eventType,
    eventTypeLabel: formatEnumLabel(eventType),
    scheduleId,
    channel,
    channelLabel: formatEnumLabel(channel),
    status,
    statusLabel: formatEnumLabel(status),
    message,
    read: typeof cacheEntry.read === 'boolean' ? cacheEntry.read : false,
    lifecycle: normalizeLifecycle(cacheEntry.lifecycle),
    icon: inferIcon(eventType, message),
    createdAt,
    sentAt,
    timeAgo: formatTimeAgo(createdAt || sentAt),
    createdAtLabel: formatDateTime(createdAt),
  }
}

async function loadNotifications() {
  loading.value = true
  error.value = ''

  try {
    const data = await getNotifications()
    const uiCache = loadNotificationUiCache()
    notifications.value = Array.isArray(data)
      ? data.map((notification) => normalizeNotification(notification, uiCache))
      : []
    persistNotificationUiCache()
  } catch (err) {
    error.value = err?.message || 'Unable to load notifications.'
    notifications.value = []
  } finally {
    loading.value = false
  }
}

function setTab(tab) {
    activeTab.value = tab
    feedbackMessage.value = ''
}

function setReadFilter(value) {
  readFilter.value = value
  feedbackMessage.value = ''
}

function updateNotification(id, updates, message) {
  notifications.value = notifications.value.map((notification) =>
    notification.id === id ? { ...notification, ...updates } : notification,
  )
  persistNotificationUiCache()
  feedbackMessage.value = message
}

function markAsRead(id) {
  updateNotification(id, { read: true }, 'Notification marked as read (local prototype state).')
}

function markAsUnread(id) {
  updateNotification(id, { read: false }, 'Notification marked as unread (local prototype state).')
}

function archiveItem(id) {
  updateNotification(
    id,
    { lifecycle: 'archived', read: true },
    'Notification moved to Archived (local prototype state).',
  )
}

function moveToTrash(id) {
  updateNotification(
    id,
    { lifecycle: 'trash', read: true },
    'Notification moved to Trash (local prototype state).',
  )
}

function restoreFromTrash(id) {
  updateNotification(
    id,
    { lifecycle: 'active', read: false },
    'Notification restored to Active (local prototype state).',
  )
}

function deleteForever(id) {
  notifications.value = notifications.value.filter((notification) => notification.id !== id)
  persistNotificationUiCache()
  feedbackMessage.value = 'Notification deleted from local prototype state.'
}

function iconGlyph(type) {
  if (type === 'swap') return '⇄'
  if (type === 'assign') return '⊕'
  if (type === 'cancel') return '⊗'
  if (type === 'move') return '→'
  return '!'
}

onMounted(loadNotifications)
</script>

<template>
  <div class="flex min-h-screen bg-[#F4F7FA] overflow-x-hidden">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="app-page-wrap">
        <header class="app-surface-card app-section-padding">
          <div>
            <div>
              <h1 class="typo-page-title">Notifications Overview</h1>
              <p class="mt-2 typo-body max-w-3xl">
                Authenticated administrator feed for operational events. Each entry preserves the
                API structure while improving readability and decision speed.
              </p>
            </div>
          </div>

          <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <article
              v-for="card in summaryCards"
              :key="card.label"
              class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <p class="typo-card-label">{{ card.label }}</p>
              <p class="typo-card-value">{{ card.value }}</p>
              <p class="typo-caption mt-1">{{ card.note }}</p>
            </article>
          </div>
        </header>

        <section class="app-surface-card app-section-padding">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div class="flex-1">
              <label class="mb-1 block typo-card-label">Search Feed</label>
              <div class="relative max-w-2xl">
                <input
                  v-model="searchQuery"
                  type="search"
                  placeholder="Search by message, event type, schedule, channel, or status"
                  class="typo-body w-full rounded-xl border border-slate-300 bg-white px-10 py-2.5 outline-none focus:ring-2 focus:ring-sky-200"
                />
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
              </div>
            </div>

            <div class="flex flex-col gap-1 lg:w-56">
              <label class="typo-card-label">Read State</label>
              <select
                :value="readFilter"
                class="typo-body rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:ring-2 focus:ring-sky-200"
                @change="setReadFilter($event.target.value)"
              >
                <option
                  v-for="option in readFilterOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap gap-2 border-t border-slate-200 pt-4">
            <button
              v-for="tab in lifecycleTabs"
              :key="tab.key"
              type="button"
              class="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-semibold transition"
              :class="
                activeTab === tab.key
                  ? 'border-[#0077B6] bg-[#0077B6] text-white'
                  : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
              "
              @click="setTab(tab.key)"
            >
              <span class="inline-flex min-w-5 items-center justify-center rounded-full border border-current px-1 text-xs">
                {{ notificationCounts[tab.key] }}
              </span>
              {{ tab.label }}
            </button>
          </div>
        </section>

        <section class="app-surface-card overflow-hidden">
          <div class="border-b border-slate-200 px-4 py-4 md:px-5">
            <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 class="typo-section-title">
                  {{ lifecycleTabs.find((tab) => tab.key === activeTab)?.label || 'Notifications' }}
                </h2>
                <p class="typo-muted">
                  {{ visibleRows.length }} visible item{{ visibleRows.length === 1 ? '' : 's' }}
                  after current filters.
                </p>
              </div>

              <p
                v-if="activeTab === 'trash'"
                class="typo-caption rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-700"
              >
                Trash retention is still local-only. Permanent removal policy should move to backend.
              </p>
            </div>
          </div>

          <div v-if="error" class="typo-body border-b border-red-200 bg-red-50 px-4 py-3 text-red-700 md:px-5">
            {{ error }}
          </div>

          <div v-if="loading" class="typo-muted px-4 py-10 text-center md:px-5">
            Loading notifications...
          </div>

          <div
            v-else-if="visibleRows.length === 0"
            class="typo-muted px-4 py-10 text-center md:px-5"
          >
            No notifications found for the current filters.
          </div>

          <ul v-else class="divide-y divide-slate-200">
            <li
              v-for="notification in visibleRows"
              :key="notification.id"
              class="px-4 py-4 transition-colors md:px-5"
              :class="notification.read ? 'hover:bg-slate-50' : 'bg-sky-50/60 hover:bg-sky-50'"
            >
              <div class="grid gap-4 xl:grid-cols-[28px_minmax(0,1fr)_auto] xl:items-start">
                <span class="flex h-7 w-7 items-center justify-center rounded-full bg-white text-sm text-slate-700 shadow-sm">
                  {{ iconGlyph(notification.icon) }}
                </span>

                <div class="min-w-0">
                  <div class="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
                    <div class="min-w-0">
                      <p class="typo-body font-semibold leading-snug text-slate-900">
                        {{ notification.message }}
                      </p>
                      <div class="mt-2 flex flex-wrap gap-2">
                        <span
                          class="rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide"
                          :class="eventTypeBadgeClass(notification.eventType)"
                        >
                          {{ notification.eventTypeLabel }}
                        </span>
                        <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold tracking-wide text-slate-700">
                          Schedule #{{ notification.scheduleId ?? 'N/A' }}
                        </span>
                        <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold tracking-wide text-slate-700">
                          {{ notification.channelLabel }}
                        </span>
                        <span
                          class="rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide"
                          :class="statusBadgeClass(notification.status)"
                        >
                          {{ notification.statusLabel }}
                        </span>
                        <span
                          class="rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide"
                          :class="notification.read ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-sky-200 bg-sky-50 text-sky-700'"
                        >
                          {{ notification.read ? 'Read' : 'Unread' }}
                        </span>
                      </div>
                    </div>

                    <div class="typo-caption lg:text-right">
                      <p><span class="font-semibold text-slate-700">Created:</span> {{ notification.createdAtLabel }}</p>
                      <p class="mt-1"><span class="font-semibold text-slate-700">Relative:</span> {{ notification.timeAgo }}</p>
                    </div>
                  </div>
                </div>

                <div class="flex flex-wrap items-center gap-2 xl:w-56 xl:justify-end">
                  <button
                    v-if="!notification.read"
                    type="button"
                    class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="markAsRead(notification.id)"
                  >
                    Mark read
                  </button>
                  <button
                    v-else
                    type="button"
                    class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="markAsUnread(notification.id)"
                  >
                    Mark unread
                  </button>
                  <button
                    v-if="notification.lifecycle === 'active'"
                    type="button"
                    class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="archiveItem(notification.id)"
                  >
                    Archive
                  </button>
                  <button
                    v-if="notification.lifecycle !== 'trash'"
                    type="button"
                    class="rounded-lg border border-red-600 bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-red-700"
                    @click="moveToTrash(notification.id)"
                  >
                    Move to trash
                  </button>
                  <button
                    v-if="notification.lifecycle === 'trash'"
                    type="button"
                    class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="restoreFromTrash(notification.id)"
                  >
                    Restore
                  </button>
                  <button
                    v-if="notification.lifecycle === 'trash'"
                    type="button"
                    class="rounded-lg border border-red-600 bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-red-700"
                    @click="deleteForever(notification.id)"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          </ul>
        </section>

        <p class="typo-caption px-1">
          Read access is authenticated from the backend. Read, archive, trash, and delete states
          remain local prototype overlays until backend endpoints are added.
        </p>

        <p v-if="feedbackMessage" class="typo-body px-1 text-emerald-700">{{ feedbackMessage }}</p>
      </section>
    </main>
  </div>
</template>
