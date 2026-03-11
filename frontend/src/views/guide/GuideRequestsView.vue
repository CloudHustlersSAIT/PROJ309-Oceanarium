<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <h1 class="app-title">Swap Requests</h1>
      <p class="app-subtitle">Accept or reject tour swaps</p>

      <div class="mt-5 space-y-3">
        <div v-for="request in requests" :key="request.id" class="notification-card p-3.5 sm:p-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="app-body-title">
                {{ request.title }}
              </p>
              <p class="app-body-meta">{{ request.date }} • {{ request.time }}</p>
              <p class="app-body-meta">Requested by {{ request.from }}</p>
            </div>

            <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
              <button
                class="app-action-btn bg-[#2A9D8F] text-white hover:opacity-90"
                @click="accept(request.id)"
              >
                Accept
              </button>

              <button
                class="app-action-btn bg-[#E63946] text-white hover:opacity-90"
                @click="reject(request.id)"
              >
                Reject
              </button>
            </div>
          </div>
        </div>

        <div v-if="requests.length === 0" class="text-sm text-black/60">No pending requests.</div>
      </div>

      <p v-if="toast" class="mt-4 text-sm font-semibold text-[#0077B6]">
        {{ toast }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const requests = ref([
  {
    id: 1,
    title: 'Dolphin Feeding Experience',
    date: 'Feb 20, 2026',
    time: '2:00-3:00 PM',
    from: 'Ana Costa',
  },
  {
    id: 2,
    title: 'Reef Discovery',
    date: 'Feb 21, 2026',
    time: '11:00-12:00 PM',
    from: 'Liam Brown',
  },
])

const toast = ref('')

function accept(id) {
  requests.value = requests.value.filter((r) => r.id !== id)
  toast.value = 'Swap request accepted.'
  setTimeout(() => (toast.value = ''), 2000)
}

function reject(id) {
  requests.value = requests.value.filter((r) => r.id !== id)
  toast.value = 'Swap request rejected.'
  setTimeout(() => (toast.value = ''), 2000)
}
</script>
