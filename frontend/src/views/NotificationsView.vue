<script setup>
import { computed, ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const selectedRange = ref('All Time')
const activeTab = ref('all')
const searchQuery = ref('')
const feedbackMessage = ref('')

const notifications = ref([
  {
    id: 1,
    icon: 'swap',
    message: 'Guide Ana Costa swapped tour Dolphin Feeding with guide Hermes Costello on November 12th at 08:00',
    timeAgo: '2 Minutes Ago',
    status: 'all',
  },
  {
    id: 2,
    icon: 'warning',
    message: 'Guide Liam Brown will be unavailable on November 11th',
    timeAgo: '3 Hours Ago',
    status: 'all',
  },
  {
    id: 3,
    icon: 'cancel',
    message: 'Guide Liam Brown has cancelled the tour Molluscs on November 11th, Guide David Martinez assigned instead',
    timeAgo: '2 Days Ago',
    status: 'all',
  },
  {
    id: 4,
    icon: 'assign',
    message: 'Admin Kim Wexler assigned Guide James McGill to the tour Underwater Dining on November 11th',
    timeAgo: '2 Days Ago',
    status: 'archived',
  },
  {
    id: 5,
    icon: 'warning',
    message: 'System is unable to assign a guide to the tour Underwater Dining on November 11th, please review manually',
    timeAgo: '2 Days Ago',
    status: 'archived',
  },
  {
    id: 6,
    icon: 'assign',
    message: 'Admin Gus Fring assigned Guide Walter White to the tour Blue Sea Cooking on November 10th',
    timeAgo: '3 Days Ago',
    status: 'archived',
  },
  {
    id: 7,
    icon: 'warning',
    message: 'System is unable to assign a guide to the tour Blue Sea Cooking on November 10th, please review manually',
    timeAgo: '3 Days Ago',
    status: 'archived',
  },
  {
    id: 8,
    icon: 'swap',
    message: 'Guide Tyler Durden swapped tour Shark Diving with guide Aldo Raine on November 7th at 12:00',
    timeAgo: '28 Days Ago',
    status: 'trash',
  },
  {
    id: 9,
    icon: 'swap',
    message: 'Guide Ana Costa swapped tour Dolphin Feeding with guide Hermes Costello on November 12th at 08:00',
    timeAgo: '22 Days Ago',
    status: 'trash',
  },
])

const totalCount = computed(() => notifications.value.length)

const counts = computed(() => {
  return {
    all: notifications.value.filter((item) => item.status === 'all').length,
    archived: notifications.value.filter((item) => item.status === 'archived').length,
    trash: notifications.value.filter((item) => item.status === 'trash').length,
  }
})

const visibleRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return notifications.value.filter((item) => {
    const byTab = activeTab.value === 'all' ? item.status === 'all' : item.status === activeTab.value
    const bySearch = item.message.toLowerCase().includes(query)
    return byTab && bySearch
  })
})

function setTab(tab) {
  activeTab.value = tab
  feedbackMessage.value = ''
}

function archiveItem(id) {
  const target = notifications.value.find((item) => item.id === id)
  if (!target) return
  target.status = 'archived'
  feedbackMessage.value = 'Notification moved to Archived (prototype state).'
}

function moveToTrash(id) {
  const target = notifications.value.find((item) => item.id === id)
  if (!target) return
  target.status = 'trash'
  feedbackMessage.value = 'Notification moved to Delete (prototype state).'
}

function restoreFromTrash(id) {
  const target = notifications.value.find((item) => item.id === id)
  if (!target) return
  target.status = 'all'
  feedbackMessage.value = 'Notification restored to All (prototype state).'
}

function deleteForever(id) {
  notifications.value = notifications.value.filter((item) => item.id !== id)
  feedbackMessage.value = 'Notification deleted from prototype state.'
}

function iconGlyph(type) {
  if (type === 'swap') return '⇄'
  if (type === 'assign') return '⊕'
  if (type === 'cancel') return '⊗'
  return '!'
}
</script>

<template>
  <div class="flex min-h-screen bg-[#F4F7FA] overflow-x-hidden">
    <Sidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <h1 class="text-4xl font-semibold text-gray-900">Notifications Overview</h1>

        <div class="flex flex-wrap gap-2">
          <div class="relative w-full max-w-md">
            <input
              v-model="searchQuery"
              type="search"
              placeholder="Search notifications"
              aria-label="Search notifications"
              class="w-full rounded-lg border border-gray-300 bg-white px-10 py-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-sky-200"
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true">⌕</span>
          </div>

          <select
            v-model="selectedRange"
            class="rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700"
          >
            <option>All Time</option>
            <option>This Month</option>
            <option>This Week</option>
            <option>This Day</option>
          </select>
        </div>
      </section>

      <section class="rounded-xl border border-gray-200 bg-[#E9EEF2] shadow-sm overflow-hidden">
        <div class="border-b border-gray-300 px-4 md:px-5 py-4 bg-[#E1E8ED]">
          <p class="text-4xl font-medium text-gray-900">
            Hey, <span class="font-semibold">Lucas!</span>
            <span class="text-2xl font-normal text-gray-700"> You have a total of <span class="font-semibold">{{ totalCount }}</span> notifications</span>
          </p>
        </div>

        <div v-if="activeTab === 'trash'" class="px-4 md:px-5 pt-2 text-xs text-red-500">
          Please note that notifications in Delete will be permanently removed after 30 days.
        </div>

        <div class="px-4 md:px-5 pt-3 pb-2 border-b border-gray-300">
          <div class="flex flex-wrap items-center gap-4 text-sm">
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-full px-3 py-1 border"
              :class="activeTab === 'all' ? 'bg-[#5AB2D8] text-white border-[#5AB2D8]' : 'bg-white text-gray-700 border-gray-300'"
              @click="setTab('all')"
            >
              <span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-current px-1 text-xs">{{ counts.all }}</span>
              All
            </button>

            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-full px-3 py-1 border"
              :class="activeTab === 'archived' ? 'bg-[#5AB2D8] text-white border-[#5AB2D8]' : 'bg-white text-gray-700 border-gray-300'"
              @click="setTab('archived')"
            >
              <span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-current px-1 text-xs">{{ counts.archived }}</span>
              Archived
            </button>

            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-full px-3 py-1 border"
              :class="activeTab === 'trash' ? 'bg-[#5AB2D8] text-white border-[#5AB2D8]' : 'bg-white text-gray-700 border-gray-300'"
              @click="setTab('trash')"
            >
              <span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-current px-1 text-xs">{{ counts.trash }}</span>
              Delete
            </button>
          </div>
        </div>

        <ul class="divide-y divide-gray-300/80">
          <li v-if="visibleRows.length === 0" class="px-4 md:px-5 py-8 text-center text-gray-500">
            No notifications found for this filter.
          </li>

          <li
            v-for="item in visibleRows"
            :key="item.id"
            class="px-4 md:px-5 py-3 grid grid-cols-[24px_1fr_auto_auto] gap-3 items-center hover:bg-[#DEE7EE] transition-colors"
          >
            <span class="text-gray-700 text-lg leading-none">{{ iconGlyph(item.icon) }}</span>
            <p class="text-sm text-gray-800">{{ item.message }}</p>
            <span class="text-sm text-gray-500 whitespace-nowrap">{{ item.timeAgo }}</span>

            <div class="flex items-center gap-2 whitespace-nowrap">
              <button
                v-if="item.status === 'all'"
                type="button"
                class="px-2.5 py-1.5 rounded border border-gray-300 text-xs text-gray-700"
                @click="archiveItem(item.id)"
              >
                Archive
              </button>
              <button
                v-if="item.status !== 'trash'"
                type="button"
                class="px-2.5 py-1.5 rounded border border-red-600 bg-red-600 text-white text-xs hover:bg-red-700"
                @click="moveToTrash(item.id)"
              >
                Delete
              </button>
              <button
                v-if="item.status === 'trash'"
                type="button"
                class="px-2.5 py-1.5 rounded border border-gray-300 text-xs text-gray-700"
                @click="restoreFromTrash(item.id)"
              >
                Restore
              </button>
              <button
                v-if="item.status === 'trash'"
                type="button"
                class="px-2.5 py-1.5 rounded border border-red-600 bg-red-600 text-white text-xs hover:bg-red-700"
                @click="deleteForever(item.id)"
              >
                Delete
              </button>
            </div>
          </li>
        </ul>
      </section>

      <p class="mt-3 text-sm text-gray-500">Prototype mode: all actions are local to the current frontend session.</p>
      <p v-if="feedbackMessage" class="mt-1 text-sm text-emerald-700">{{ feedbackMessage }}</p>
    </main>
  </div>
</template>
