<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-3 sm:items-center">
        <div>
          <h1 class="app-title">My Schedule</h1>
          <p class="app-subtitle">Weekly overview of assigned tours</p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button
            class="app-action-btn border border-black/10 text-[#1C1C1C] hover:bg-[#CAF0F8]/50"
            @click="prevWeek"
          >
            &lt;- Prev
          </button>

          <span
            class="app-action-btn inline-flex items-center border border-[#0077B6]/20 bg-[#EAF6FD] text-[#005A8A]"
          >
            {{ weekLabel }}
          </span>

          <button
            class="app-action-btn border border-black/10 text-[#1C1C1C] hover:bg-[#CAF0F8]/50"
            @click="nextWeek"
          >
            Next ->
          </button>
        </div>
      </div>

      <div class="mt-5 space-y-3">
        <div v-for="event in events" :key="event.id" class="notification-card p-3.5 sm:p-4">
          <div class="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="app-body-title">
                {{ event.title }}
              </p>
              <p class="app-body-meta">
                {{ event.date }} • {{ event.time }} • {{ event.language }}
              </p>
            </div>

            <span
              class="px-3 py-1 text-xs rounded-full bg-[#00B4D8]/10 text-[#0077B6] font-semibold"
            >
              {{ event.status }}
            </span>
          </div>
        </div>

        <div v-if="events.length === 0" class="text-sm text-black/60">
          No tours scheduled for this week.
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const weekOffset = ref(0)

const weekLabel = computed(() => {
  if (weekOffset.value === 0) return 'This Week'
  if (weekOffset.value > 0) return `Week +${weekOffset.value}`
  return `Week ${weekOffset.value}`
})

function prevWeek() {
  weekOffset.value--
}

function nextWeek() {
  weekOffset.value++
}

const events = ref([
  {
    id: 1,
    title: 'Dolphin Feeding Experience',
    date: 'Feb 18, 2026',
    time: '2:00-3:00 PM',
    language: 'EN',
    status: 'Scheduled',
  },
  {
    id: 2,
    title: 'Reef Discovery',
    date: 'Feb 19, 2026',
    time: '11:00-12:00 PM',
    language: 'FR',
    status: 'Scheduled',
  },
])
</script>
