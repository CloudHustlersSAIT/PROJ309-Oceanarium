<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { useNotificationStore } from '../stores/notification'

const store = useNotificationStore()

const EVENT_TYPE_CHIPS = [
  { key: null, label: 'All Types' },
  { key: 'GUIDE_ASSIGNED', label: 'Guide Assigned' },
  { key: 'GUIDE_REASSIGNED', label: 'Guide Reassigned' },
  { key: 'SCHEDULE_CHANGED', label: 'Schedule Changed' },
  { key: 'SCHEDULE_UNASSIGNABLE', label: 'Unassignable' },
  { key: 'RESERVATION_CANCELLED', label: 'Cancelled' },
  { key: 'RESERVATION_MOVED', label: 'Moved' },
]

const READ_FILTER_OPTIONS = [
  { value: 'all', label: 'All read states' },
  { value: 'unread', label: 'Unread only' },
  { value: 'read', label: 'Read only' },
]

const deleteConfirmId = ref(null)
let searchDebounceTimer = null

const summaryCards = computed(() => [
  {
    label: 'Total',
    value: store.summary.total,
    note: 'All notifications',
    filterAction: () => store.clearFilters(),
    accent: false,
  },
  {
    label: 'Unread',
    value: store.summary.unread,
    note: 'Need attention',
    filterAction: () => {
      store.clearFilters()
      store.setFilter('readFilter', 'unread')
      store.loadNotifications()
    },
    accent: store.summary.unread > 0,
    accentClass: 'border-[#00B4D8] bg-[#CAF0F8]/40 dark:border-sky-700/40 dark:bg-sky-950/45',
  },
  {
    label: 'Urgent',
    value: store.summary.by_priority?.urgent ?? 0,
    note: 'Immediate action',
    filterAction: () => {
      store.clearFilters()
      store.setFilter('priority', 'urgent')
      store.loadNotifications()
    },
    accent: (store.summary.by_priority?.urgent ?? 0) > 0,
    accentClass: 'border-red-300 bg-red-50 hover:bg-red-100 dark:border-red-700/70 dark:bg-red-950/65 dark:hover:bg-red-950/75',
  },
  {
    label: 'Action Required',
    value: store.summary.action_required,
    note: 'Pending decisions',
    filterAction: null,
    accent: store.summary.action_required > 0,
    accentClass: 'border-amber-300 bg-amber-50 hover:bg-amber-100 dark:border-amber-700/70 dark:bg-amber-950/60 dark:hover:bg-amber-950/70',
  },
])

function chipCount(key) {
  if (!key) return store.summary.total
  return store.summary.by_event_type?.[key] ?? 0
}

function selectEventType(key) {
  store.setFilter('eventType', key)
  store.loadNotifications()
}

function setReadFilter(value) {
  store.setFilter('readFilter', value)
  store.loadNotifications()
}

function onSearchInput(event) {
  const value = event.target.value
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    store.setFilter('searchQuery', value)
  }, 300)
}

function clearFiltersAndReload() {
  store.clearFilters()
  store.loadNotifications()
}

async function handleMarkAllRead() {
  await store.markAllRead()
}

function eventTypeBadgeClass(eventType) {
  const t = String(eventType || '')
    .trim()
    .toLowerCase()
  if (t.includes('unassignable')) return 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
  if (t.includes('cancel')) return 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
  if (t.includes('reassign')) return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
  if (t.includes('assign')) return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800 dark:bg-sky-950/45 dark:text-sky-300'
  if (t.includes('change') || t.includes('move')) return 'border-teal-200 bg-teal-50 text-teal-700 dark:border-teal-800 dark:bg-teal-950/45 dark:text-teal-300'
  return 'border-slate-200 bg-slate-50 text-slate-700 dark:border-white/10 dark:bg-[#1A2231] dark:text-slate-300'
}

function statusBadgeClass(status) {
  const s = String(status || '')
    .trim()
    .toLowerCase()
  if (s === 'sent') return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300'
  if (s === 'failed' || s === 'error') return 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300'
  return 'border-slate-200 bg-slate-50 text-slate-700 dark:border-white/10 dark:bg-[#1A2231] dark:text-slate-300'
}

function priorityBorderClass(priority) {
  const p = String(priority || '')
    .trim()
    .toLowerCase()
  if (p === 'urgent') return 'border-l-red-500'
  if (p === 'high') return 'border-l-amber-400'
  if (p === 'low') return 'border-l-slate-300'
  return 'border-l-[#0077B6]'
}

function iconGlyph(type) {
  if (type === 'swap') return '⇄'
  if (type === 'assign') return '⊕'
  if (type === 'cancel') return '⊗'
  if (type === 'move') return '→'
  return '!'
}

function iconBgClass(type) {
  if (type === 'assign') return 'bg-sky-100 text-sky-700 dark:bg-sky-950/45 dark:text-sky-300'
  if (type === 'cancel') return 'bg-red-100 text-red-700 dark:bg-red-950/45 dark:text-red-300'
  if (type === 'warning') return 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
  if (type === 'move') return 'bg-teal-100 text-teal-700 dark:bg-teal-950/45 dark:text-teal-300'
  return 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-300'
}

function emptyMessage() {
  if (store.filters.eventType) {
    const chip = EVENT_TYPE_CHIPS.find((c) => c.key === store.filters.eventType)
    return `No "${chip?.label || store.filters.eventType}" notifications found.`
  }
  if (store.filters.readFilter === 'unread') return 'All notifications have been read.'
  if (store.filters.priority === 'urgent') return 'No urgent notifications — all clear.'
  if (store.filters.searchQuery.trim()) return 'No notifications match your search.'
  return 'No notifications yet.'
}

function confirmDelete(id) {
  deleteConfirmId.value = id
}

function cancelDelete() {
  deleteConfirmId.value = null
}

function handleDeleteForever() {
  if (deleteConfirmId.value !== null) {
    store.notifications = store.notifications.filter((n) => n.id !== deleteConfirmId.value)
    store.showFeedback('Notification removed.')
    deleteConfirmId.value = null
  }
}

const searchInputRef = ref('')

watch(
  () => store.filters.searchQuery,
  (val) => {
    searchInputRef.value = val
  },
)

onMounted(() => {
  store.init()
})

onUnmounted(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})
</script>

<template>
  <div class="flex min-h-screen overflow-x-hidden bg-[#F4F7FA] dark:bg-[#0F1117]">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="app-page-wrap">
        <!-- Page Header -->
        <header class="app-surface-card app-section-padding">
          <div>
            <h1 class="typo-page-title">Notifications</h1>
            <p class="mt-2 typo-body max-w-3xl">
              Operational events for scheduling, guide assignments, and alerts.
            </p>
          </div>

          <!-- Summary Cards -->
          <div class="mt-5 grid grid-cols-2 gap-3 xl:grid-cols-4">
            <button
              v-for="card in summaryCards"
              :key="card.label"
              type="button"
              class="rounded-xl border px-4 py-3 text-left transition hover:shadow-sm disabled:cursor-default disabled:opacity-90"
              :class="card.accent ? card.accentClass : 'border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-[#1A2231]'"
              :disabled="!card.filterAction"
              :title="`Click to filter by ${card.label.toLowerCase()}`"
              @click="card.filterAction?.()"
            >
              <p class="typo-card-label">{{ card.label }}</p>
              <p class="typo-card-value">{{ card.value }}</p>
              <p class="typo-caption mt-1">{{ card.note }}</p>
            </button>
          </div>
        </header>

        <!-- Filter Bar -->
        <section class="app-surface-card app-section-padding">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <!-- Search -->
            <div class="flex-1">
              <label class="mb-1 block typo-card-label">Search</label>
              <div class="relative max-w-2xl">
                <input
                  :value="searchInputRef"
                  type="search"
                  placeholder="Search by message, event type, schedule, or status"
                  class="typo-body w-full rounded-xl border border-slate-300 bg-white px-10 py-2.5 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                  @input="onSearchInput"
                />
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </span>
              </div>
            </div>

            <!-- Read State + Clear -->
            <div class="flex items-end gap-3">
              <div class="flex flex-col gap-1">
                <label class="typo-card-label">Read State</label>
                <select
                  :value="store.filters.readFilter"
                  class="typo-body rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:ring-2 focus:ring-sky-200 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:focus:ring-sky-800/50"
                  @change="setReadFilter($event.target.value)"
                >
                  <option
                    v-for="option in READ_FILTER_OPTIONS"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <button
                v-if="store.hasActiveFilters"
                type="button"
                class="mb-0.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium text-[#0077B6] transition hover:bg-sky-50 dark:text-sky-300 dark:hover:bg-sky-950/40"
                @click="clearFiltersAndReload"
              >
                Clear filters
              </button>
            </div>
          </div>

          <!-- Event Type Chips -->
          <div class="mt-4 flex flex-wrap gap-2 border-t border-slate-200 pt-4 dark:border-white/10">
            <button
              v-for="chip in EVENT_TYPE_CHIPS"
              :key="chip.key ?? 'all'"
              type="button"
              class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold transition"
              :class="
                store.filters.eventType === chip.key
                  ? 'border-[#0077B6] bg-[#0077B6] text-white'
                  : chip.key === 'SCHEDULE_UNASSIGNABLE' && chipCount(chip.key) > 0
                    ? 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300 dark:hover:bg-red-950/60'
                    : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5'
              "
              @click="selectEventType(chip.key)"
            >
              {{ chip.label }}
              <span
                class="inline-flex min-w-5 items-center justify-center rounded-full px-1 text-xs"
                :class="
                  store.filters.eventType === chip.key
                    ? 'bg-white/25 text-white'
                    : 'bg-slate-200/70 text-slate-600 dark:bg-white/10 dark:text-slate-300'
                "
              >
                {{ chipCount(chip.key) }}
              </span>
            </button>
          </div>
        </section>

        <!-- Bulk Actions Toolbar -->
        <div class="flex items-center justify-between gap-3 px-1">
          <p class="typo-muted">
            {{ store.filteredNotifications.length }}
            notification{{ store.filteredNotifications.length === 1 ? '' : 's' }}
          </p>
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
            :disabled="store.unreadCount === 0"
            @click="handleMarkAllRead"
          >
            Mark all as read
          </button>
        </div>

        <!-- Notification List -->
        <section class="app-surface-card overflow-hidden">
          <!-- Error State -->
          <div
            v-if="store.error"
            class="flex items-center justify-between gap-3 border-b border-red-200 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950/45 md:px-5"
          >
            <p class="typo-body text-red-700 dark:text-red-300">{{ store.error }}</p>
            <button
              type="button"
              class="shrink-0 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-50 dark:border-red-800 dark:bg-[#1C2333] dark:text-red-300 dark:hover:bg-red-950/35"
              @click="store.loadNotifications()"
            >
              Retry
            </button>
          </div>

          <!-- Loading Skeleton -->
          <div v-if="store.loading" class="divide-y divide-slate-200 dark:divide-white/10">
            <div v-for="i in 3" :key="i" class="px-4 py-4 md:px-5">
              <div class="flex gap-4 animate-pulse">
                <div class="h-8 w-8 shrink-0 rounded-full bg-slate-200 dark:bg-white/10" />
                <div class="flex-1 space-y-3">
                  <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10" />
                  <div class="flex gap-2">
                    <div class="h-5 w-24 rounded-full bg-slate-200 dark:bg-white/10" />
                    <div class="h-5 w-20 rounded-full bg-slate-200 dark:bg-white/10" />
                    <div class="h-5 w-16 rounded-full bg-slate-200 dark:bg-white/10" />
                  </div>
                </div>
                <div class="h-4 w-20 rounded bg-slate-200 dark:bg-white/10" />
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="store.filteredNotifications.length === 0"
            class="px-4 py-14 text-center md:px-5"
          >
            <div
              class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400 dark:bg-white/10 dark:text-slate-500"
            >
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <p class="typo-muted">{{ emptyMessage() }}</p>
            <button
              v-if="store.hasActiveFilters"
              type="button"
              class="mt-3 text-sm font-medium text-[#0077B6] hover:underline"
              @click="clearFiltersAndReload"
            >
              Clear all filters
            </button>
          </div>

          <!-- Notification Cards -->
          <ul v-else class="divide-y divide-slate-100 dark:divide-white/8">
            <li
              v-for="notification in store.filteredNotifications"
              :key="notification.id"
              class="border-l-4 px-4 py-4 md:px-5"
              :class="[
                priorityBorderClass(notification.priority),
                notification.read ? 'notification-card' : 'notification-card-unread',
              ]"
            >
              <div class="flex gap-3">
                <!-- Icon -->
                <span
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold"
                  :class="iconBgClass(notification.icon)"
                >
                  {{ iconGlyph(notification.icon) }}
                </span>

                <!-- Content -->
                <div class="min-w-0 flex-1">
                  <div class="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
                    <div class="min-w-0">
                      <p
                        class="typo-body leading-snug text-slate-900 dark:text-slate-100"
                        :class="{ 'font-semibold': !notification.read }"
                      >
                        {{ notification.message }}
                      </p>

                      <!-- Badge Row -->
                      <div class="mt-2 flex flex-wrap gap-1.5">
                        <span
                          class="rounded-full border px-2 py-0.5 text-[11px] font-semibold tracking-wide"
                          :class="eventTypeBadgeClass(notification.eventType)"
                        >
                          {{ notification.eventTypeLabel }}
                        </span>
                        <span
                          v-if="notification.scheduleId"
                          class="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-semibold tracking-wide text-slate-600 dark:border-white/10 dark:bg-[#1C2333] dark:text-slate-300"
                        >
                          Schedule #{{ notification.scheduleId }}
                        </span>
                        <span
                          class="rounded-full border px-2 py-0.5 text-[11px] font-semibold tracking-wide"
                          :class="statusBadgeClass(notification.status)"
                        >
                          {{ notification.statusLabel }}
                        </span>
                        <span
                          v-if="notification.emailStatusLabel"
                          class="rounded-full border px-2 py-0.5 text-[11px] font-semibold tracking-wide"
                          :class="statusBadgeClass(notification.emailStatus)"
                          :title="
                            notification.emailSentAtLabel
                              ? `Email ${notification.emailStatusLabel} at ${notification.emailSentAtLabel}`
                              : `Email ${notification.emailStatusLabel}`
                          "
                        >
                          Email {{ notification.emailStatusLabel }}
                        </span>
                        <span
                          v-if="notification.priority === 'urgent'"
                          class="rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[11px] font-bold tracking-wide text-red-700 dark:border-red-800 dark:bg-red-950/45 dark:text-red-300"
                        >
                          Urgent
                        </span>
                        <span
                          v-if="notification.actionRequired"
                          class="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-bold tracking-wide text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                        >
                          Action Required
                        </span>
                      </div>
                    </div>

                    <!-- Timestamp -->
                    <div class="shrink-0 typo-caption lg:text-right">
                      <p class="font-medium text-slate-600 dark:text-slate-300">{{ notification.timeAgo }}</p>
                      <p class="mt-0.5">{{ notification.createdAtLabel }}</p>
                    </div>
                  </div>

                  <!-- Actions -->
                  <div class="mt-3 flex flex-wrap items-center gap-2">
                    <button
                      v-if="!notification.read"
                      type="button"
                      class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
                      @click="store.markRead(notification.id)"
                    >
                      Mark read
                    </button>
                    <button
                      v-if="notification.primaryAction"
                      type="button"
                      class="rounded-lg border border-[#0077B6] bg-[#0077B6] px-3 py-1.5 text-xs font-medium text-white transition hover:bg-[#006399]"
                      @click="$router.push(notification.primaryAction.url)"
                    >
                      {{ notification.primaryAction.label }}
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50 dark:border-red-800 dark:bg-[#1C2333] dark:text-red-300 dark:hover:bg-red-950/35"
                      @click="confirmDelete(notification.id)"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </section>

        <!-- Feedback Toast -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="translate-y-2 opacity-0"
          enter-to-class="translate-y-0 opacity-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="translate-y-0 opacity-100"
          leave-to-class="translate-y-2 opacity-0"
        >
          <p
            v-if="store.feedbackMessage"
            class="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-2.5 text-sm font-medium text-emerald-700 shadow-lg dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300"
          >
            {{ store.feedbackMessage }}
          </p>
        </Transition>

        <!-- Confirm Delete Dialog -->
        <ConfirmDialog
          :open="deleteConfirmId !== null"
          title="Delete notification"
          message="This notification will be permanently removed. This action cannot be undone."
          confirm-label="Delete forever"
          @confirm="handleDeleteForever"
          @cancel="cancelDelete"
        />
      </section>
    </main>
  </div>
</template>
