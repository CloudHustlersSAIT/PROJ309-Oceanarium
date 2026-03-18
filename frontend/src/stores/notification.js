import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  getNotifications,
  getNotificationSummary,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/api'
import { useToast } from '../composables/useToast'

const EVENT_TYPE_LABELS = {
  GUIDE_ASSIGNED: 'Guide Assigned',
  GUIDE_REASSIGNED: 'Guide Reassigned',
  SCHEDULE_UNASSIGNABLE: 'Unassignable',
  SCHEDULE_CHANGED: 'Schedule Changed',
  RESERVATION_CANCELLED: 'Reservation Cancelled',
  RESERVATION_MOVED: 'Reservation Moved',
}

function formatEnumLabel(value) {
  const normalized = String(value || '').trim()
  if (!normalized) return 'Unknown'
  if (EVENT_TYPE_LABELS[normalized]) return EVENT_TYPE_LABELS[normalized]
  return normalized
    .toLowerCase()
    .split('_')
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ')
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

function inferIcon(eventType, message) {
  const type = String(eventType || '')
    .trim()
    .toLowerCase()
  const msg = String(message || '')
    .trim()
    .toLowerCase()
  if (type.includes('swap') || msg.includes('swap')) return 'swap'
  if (type.includes('unassignable') || msg.includes('unassignable')) return 'warning'
  if (type.includes('assign') || msg.includes('assign')) return 'assign'
  if (type.includes('cancel') || msg.includes('cancel')) return 'cancel'
  if (type.includes('move') || msg.includes('moved')) return 'move'
  if (type.includes('change') || msg.includes('change')) return 'move'
  return 'warning'
}

function normalizeNotification(item) {
  const id = Number(item?.id)
  const message = String(item?.message || 'Notification received').trim()
  const eventType = String(item?.event_type || item?.eventType || 'system').trim() || 'system'
  const scheduleId = item?.schedule_id ?? item?.scheduleId ?? null
  const createdAt = item?.created_at || item?.createdAt || null
  const sentAt = item?.sent_at || item?.sentAt || null
  const readAt = item?.read_at || item?.readAt || null
  const channel = String(item?.channel || 'PORTAL').trim() || 'PORTAL'
  const status = String(item?.status || 'SENT').trim() || 'SENT'
  const priority = String(item?.priority || 'normal').trim() || 'normal'
  const actionRequired = Boolean(item?.action_required || item?.actionRequired)
  const primaryAction = item?.primary_action || null
  const emailStatus = item?.email_status || item?.emailStatus || null
  const emailSentAt = item?.email_sent_at || item?.emailSentAt || null

  return {
    id,
    eventType,
    eventTypeLabel: formatEnumLabel(eventType),
    scheduleId,
    channel,
    channelLabel: formatEnumLabel(channel),
    status,
    statusLabel: formatEnumLabel(status),
    priority,
    actionRequired,
    primaryAction,
    message,
    read: readAt !== null,
    readAt,
    icon: inferIcon(eventType, message),
    createdAt,
    sentAt,
    timeAgo: formatTimeAgo(createdAt || sentAt),
    createdAtLabel: formatDateTime(createdAt),
    emailStatus,
    emailStatusLabel: emailStatus ? formatEnumLabel(emailStatus) : null,
    emailSentAt,
    emailSentAtLabel: emailSentAt ? formatDateTime(emailSentAt) : null,
  }
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const summary = ref({
    total: 0,
    unread: 0,
    action_required: 0,
    by_priority: { urgent: 0, high: 0, normal: 0, low: 0 },
    by_event_type: {},
  })
  const filters = ref({
    eventType: null,
    readFilter: 'all',
    searchQuery: '',
    priority: null,
  })
  const loading = ref(false)
  const error = ref('')

  const { addToast } = useToast()

  const unreadCount = computed(() => summary.value.unread || 0)

  const filteredNotifications = computed(() => {
    const query = filters.value.searchQuery.trim().toLowerCase()

    return notifications.value.filter((n) => {
      if (filters.value.eventType && n.eventType !== filters.value.eventType) return false

      if (filters.value.readFilter === 'unread' && n.read) return false
      if (filters.value.readFilter === 'read' && !n.read) return false

      if (filters.value.priority && n.priority !== filters.value.priority) return false

      if (query) {
        const searchable = [
          n.message,
          n.eventType,
          n.eventTypeLabel,
          n.scheduleId,
          n.channel,
          n.status,
        ]
          .join(' ')
          .toLowerCase()
        if (!searchable.includes(query)) return false
      }

      return true
    })
  })

  async function loadNotifications() {
    loading.value = true
    error.value = ''
    try {
      const apiFilters = {}
      if (filters.value.eventType) apiFilters.eventType = filters.value.eventType
      if (filters.value.readFilter === 'unread') apiFilters.unreadOnly = true
      if (filters.value.priority) apiFilters.priority = filters.value.priority

      const data = await getNotifications(apiFilters)
      const items = data?.notifications ?? (Array.isArray(data) ? data : [])
      notifications.value = items.map(normalizeNotification)
    } catch (err) {
      error.value = err?.message || 'Unable to load notifications.'
      notifications.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadSummary() {
    try {
      const data = await getNotificationSummary()
      summary.value = {
        total: data.total ?? 0,
        unread: data.unread ?? 0,
        action_required: data.action_required ?? 0,
        by_priority: data.by_priority ?? { urgent: 0, high: 0, normal: 0, low: 0 },
        by_event_type: data.by_event_type ?? {},
      }
    } catch {
      // Summary is non-critical; keep existing values
    }
  }

  async function markRead(id) {
    const notification = notifications.value.find((n) => n.id === id)
    if (!notification || notification.read) return

    notification.read = true
    notification.readAt = new Date().toISOString()
    if (summary.value.unread > 0) summary.value.unread--

    try {
      await markNotificationRead(id)
    } catch {
      notification.read = false
      notification.readAt = null
      if (summary.value.unread >= 0) summary.value.unread++
    }
  }

  async function markAllRead(eventType) {
    const target = eventType || filters.value.eventType || undefined
    const affected = notifications.value.filter(
      (n) => !n.read && (!target || n.eventType === target),
    )
    if (affected.length === 0) return

    affected.forEach((n) => {
      n.read = true
      n.readAt = new Date().toISOString()
    })
    summary.value.unread = Math.max(0, summary.value.unread - affected.length)

    try {
      await markAllNotificationsRead(target)
      addToast(
        `${affected.length} notification${affected.length === 1 ? '' : 's'} marked as read.`,
        { type: 'success', title: 'Notifications Updated' },
      )
    } catch {
      affected.forEach((n) => {
        n.read = false
        n.readAt = null
      })
      await loadSummary()
    }
  }

  function setFilter(key, value) {
    filters.value[key] = value
  }

  function clearFilters() {
    filters.value.eventType = null
    filters.value.readFilter = 'all'
    filters.value.searchQuery = ''
    filters.value.priority = null
  }

  const hasActiveFilters = computed(() => {
    return (
      filters.value.eventType !== null ||
      filters.value.readFilter !== 'all' ||
      filters.value.searchQuery.trim() !== '' ||
      filters.value.priority !== null
    )
  })

  async function init() {
    await Promise.all([loadNotifications(), loadSummary()])
  }

  return {
    notifications,
    summary,
    filters,
    loading,
    error,
    unreadCount,
    filteredNotifications,
    hasActiveFilters,
    loadNotifications,
    loadSummary,
    markRead,
    markAllRead,
    setFilter,
    clearFilters,
    init,
  }
})
