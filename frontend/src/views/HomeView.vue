<script setup>
import { onMounted, ref } from 'vue'
import {
  getGuides,
  getTours,
  getNotifications,
  getStats,
  createBooking,
  rescheduleBooking,
  cancelBooking,
  reportIssue,
} from '../services/api'

import Sidebar from '../components/Sidebar.vue'

const notifications = ref([
  {
    time: '2 Minutes Ago',
    text: 'Guide Ana Costa swapped tour Dolphin Feeding with guide Hermes Costello on November 5th at 08:00',
  },
  { time: '3 Hours Ago', text: 'Guide Liam Brown will be unavailable on November 9th' },
  {
    time: '2 Days Ago',
    text: 'Guide Liam Brown has cancelled the tour Molluscs on November 9th, Guide David Martinez assigned instead',
  },
])

const showGuidesModal = ref(false)
const showAddBookingModal = ref(false)
const showRescheduleModal = ref(false)
const showReportIssueModal = ref(false)
const showCancelBookingModal = ref(false)

const addBookingForm = ref({
  customerId: '',
  tourId: '',
  date: '',
  adultTickets: 0,
  childTickets: 0,
})

const rescheduleForm = ref({
  bookingId: '',
  newDate: '',
})

const reportIssueForm = ref({
  description: '',
})

const cancelBookingForm = ref({
  bookingId: '',
})

const guidesWorking = ref([])
const tours = ref([])
const stats = ref({
  toursToday: 0,
  customersToday: 0,
  cancellations: 0,
  avgRating: '5.0',
})

const todaySchedule = [
  { time: '08:00', guide: 'Ana Costa', tour: 'Shark Diving' },
  { time: '10:00', guide: 'Hermes Costello', tour: 'Dolphin Feeding' },
  { time: '10:00', guide: 'Ann A. Kim', tour: 'Deep Sea Experience' },
  { time: '11:00', guide: 'Chen Wei', tour: 'Molluscs' },
  { time: '11:00', guide: 'Liam Brown', tour: 'History of the Ocean' },
  { time: '13:00', guide: 'Ana Costa', tour: 'Coral Exploration' },
  { time: '14:00', guide: 'Walter White', tour: 'Dolphin Feeding' },
  { time: '14:00', guide: 'David Martinez', tour: 'Whales!' },
]

const recentActivity = [
  { time: 'Today at 13:00', text: 'Ana Costa Reached 4.9 Rating!' },
  { time: 'Today at 09:00', text: 'Cancellation for Molluscs' },
  { time: 'Yesterday at 18:00', text: 'Cancellation for Whales!' },
]

const closeAllModals = () => {
  showGuidesModal.value = false
  showAddBookingModal.value = false
  showRescheduleModal.value = false
  showReportIssueModal.value = false
  showCancelBookingModal.value = false
}

async function loadData() {
  try {
    guidesWorking.value = await getGuides()
    tours.value = await getTours()

    const raw = await getNotifications()
    notifications.value = Array.isArray(raw)
      ? raw.map((n, i) => ({
          id: n.id ?? i,
          time: n.timestamp || n.time || '—',
          text: n.message || n.text || '—',
        }))
      : notifications.value

    stats.value = await getStats()
  } catch {
    // Failed to load data - page will render with default values
  }
}

async function handleAddBooking() {
  try {
    await createBooking({
      customer_id: addBookingForm.value.customerId,
      tour_id: parseInt(addBookingForm.value.tourId),
      date: addBookingForm.value.date,
      adult_tickets: parseInt(addBookingForm.value.adultTickets),
      child_tickets: parseInt(addBookingForm.value.childTickets),
    })

    alert('Booking created successfully!')
    closeAllModals()
    await loadData()

    addBookingForm.value = {
      customer_id: '',
      tour_id: '',
      date: '',
      adult_tickets: 0,
      child_tickets: 0,
    }
  } catch {
    alert('Failed to create booking')
  }
}

async function handleReschedule() {
  try {
    await rescheduleBooking(rescheduleForm.value.bookingId, rescheduleForm.value.newDate)

    alert('Booking rescheduled successfully!')
    closeAllModals()

    rescheduleForm.value = {
      bookingId: '',
      newDate: '',
    }
  } catch {
    alert('Failed to reschedule booking')
  }
}

async function handleCancelBooking() {
  try {
    await cancelBooking(cancelBookingForm.value.bookingId)

    alert('Booking cancelled successfully!')
    closeAllModals()
    await loadData()

    cancelBookingForm.value = {
      bookingId: '',
    }
  } catch {
    alert('Failed to cancel booking')
  }
}

async function handleReportIssue() {
  try {
    await reportIssue(reportIssueForm.value.description)

    alert('Issue reported successfully!')
    closeAllModals()

    reportIssueForm.value = {
      description: '',
    }
  } catch {
    alert('Failed to report issue')
  }
}

const greeting = ref('')

onMounted(async () => {
  const hour = new Date().getHours()

  if (hour < 12) greeting.value = 'Good Morning'
  else if (hour < 18) greeting.value = 'Good Afternoon'
  else greeting.value = 'Good Evening'

  try {
    await loadData()
  } catch {
    // Page still renders with default data
  }
})
</script>

<template>
  <div class="flex min-h-screen">
    <Sidebar />

    <main class="flex-1">
      <div class="p-8">
        <h1 class="text-3xl font-bold text-gray-800">{{ greeting }}, Lucas!</h1>
        <p class="mt-1 text-lg text-gray-600">Here's what's happening at the Oceanarium Today</p>

        <div class="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div class="rounded-xl border border-blue-500 bg-white p-6 shadow-md">
            <h2 class="flex items-center text-xl font-semibold">
              <span class="mr-2">📅</span> Today's schedule
            </h2>

            <ul class="mt-4 space-y-3 text-sm">
              <li
                v-for="item in todaySchedule"
                :key="item.time + item.guide"
                class="border-l-4 border-blue-500 pl-3"
              >
                <strong>{{ item.time }}</strong> - Guide {{ item.guide }}<br />
                <span class="text-gray-600">{{ item.tour }}</span>
              </li>
            </ul>
          </div>

          <div class="space-y-6">
            <div class="rounded-xl border border-blue-500 bg-white p-6 shadow-md">
              <h3 class="mb-4 text-lg font-semibold">Quick KPIs</h3>

              <div class="grid grid-cols-3 gap-4">
                <div class="rounded-lg bg-blue-100 p-4 text-center">
                  <p class="text-sm text-gray-600">Tours Today</p>
                  <p class="text-3xl font-bold text-blue-800">14</p>
                </div>

                <div class="rounded-lg bg-blue-100 p-4 text-center">
                  <p class="text-sm text-gray-600">Customers Today</p>
                  <p class="text-3xl font-bold text-blue-800">84</p>
                </div>

                <div class="rounded-lg bg-blue-100 p-4 text-center">
                  <p class="text-sm text-gray-600">Cancellations</p>
                  <p class="text-3xl font-bold text-blue-800">2</p>
                </div>

                <div class="col-span-3 rounded-lg bg-blue-100 p-4 text-center">
                  <p class="text-sm text-gray-600">Avg Guide Rating</p>
                  <p class="text-3xl font-bold text-blue-800">5.0</p>
                </div>
              </div>
            </div>

            <div class="rounded-xl border border-blue-500 bg-white p-6 shadow-md">
              <h3 class="mb-4 text-lg font-semibold">Your Quick Actions</h3>

              <div class="grid grid-cols-3 gap-4 text-center">
                <button
                  class="flex flex-col items-center rounded-lg bg-yellow-400 p-4 text-white hover:bg-yellow-500"
                  @click="showAddBookingModal = true"
                >
                  <span class="text-2xl">+</span>
                  <span class="mt-1 text-xs">Add Booking</span>
                </button>

                <button
                  class="flex flex-col items-center rounded-lg bg-blue-600 p-4 text-white hover:bg-blue-700"
                  @click="showGuidesModal = true"
                >
                  <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 4.354a4 4 0 110 5.292M15 21H9v-1c0-2.21 1.79-4 4-4h2c2.21 0 4 1.79 4 4v1z"
                    />
                  </svg>
                  <span class="mt-1 text-xs">View Guides</span>
                </button>

                <button
                  class="flex flex-col items-center rounded-lg bg-green-500 p-4 text-white hover:bg-green-600"
                  @click="showRescheduleModal = true"
                >
                  <span class="text-2xl">↻</span>
                  <span class="mt-1 text-xs">Reschedule</span>
                </button>

                <button
                  class="flex flex-col items-center rounded-lg bg-red-500 p-4 text-white hover:bg-red-600"
                  @click="showCancelBookingModal = true"
                >
                  <span class="text-2xl">✕</span>
                  <span class="mt-1 text-xs">Cancel Booking</span>
                </button>

                <button
                  class="flex flex-col items-center rounded-lg bg-orange-500 p-4 text-white hover:bg-orange-600"
                  @click="showReportIssueModal = true"
                >
                  <span class="text-2xl">!</span>
                  <span class="mt-1 text-xs">Report Issue</span>
                </button>

                <button
                  class="flex flex-col items-center rounded-lg bg-gray-600 p-4 text-white hover:bg-gray-700"
                >
                  <span class="text-2xl">↓</span>
                  <span class="mt-1 text-xs">Export</span>
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-6">
            <div class="rounded-xl border border-blue-500 bg-white p-6 shadow-md">
              <h3 class="mb-4 flex items-center text-lg font-semibold">
                <span class="mr-2">🔔</span> Your recent notifications
              </h3>

              <ul class="space-y-3 text-sm">
                <li v-for="n in notifications" :key="n.id ?? n.time" class="border-b pb-2">
                  <span class="text-gray-500">{{ n.time }}:</span> {{ n.text }}
                </li>
              </ul>
            </div>

            <div class="rounded-xl border border-blue-500 bg-white p-6 shadow-md">
              <h3 class="mb-4 flex items-center text-lg font-semibold">
                <span class="mr-2">↑</span> Recent Activity
              </h3>

              <ul class="space-y-3 text-sm">
                <li v-for="a in recentActivity" :key="a.time" class="border-b pb-2">
                  <span class="text-gray-500">{{ a.time }}</span><br />
                  {{ a.text }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>

    <div
      v-if="showGuidesModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="closeAllModals"
    >
      <div class="w-96 rounded-xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-xl font-bold">Guides Working Today</h3>

        <table class="w-full text-sm">
          <thead>
            <tr class="bg-blue-600 text-white">
              <th class="px-4 py-2 text-left">Guide Name</th>
              <th class="px-4 py-2">Working Hours</th>
              <th class="px-4 py-2">Available now?</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in guidesWorking" :key="g.name" class="border-b">
              <td class="px-4 py-2">{{ g.name }}</td>
              <td class="px-4 py-2 text-center">{{ g.working_hours }}</td>
              <td class="px-4 py-2 text-center">
                <span :class="g.is_available ? 'text-green-600' : 'text-red-600'">
                  {{ g.is_available ? 'Yes' : 'No' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <button
          class="mt-4 rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600"
          @click="closeAllModals"
        >
          Close
        </button>
      </div>
    </div>

    <div
      v-if="showAddBookingModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="closeAllModals"
    >
      <div class="w-96 rounded-xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-xl font-bold">Add new booking</h3>

        <input
          v-model="addBookingForm.customerId"
          placeholder="Customer ID"
          class="mb-3 w-full rounded border p-2"
        />
        <input
          v-model="addBookingForm.tourId"
          placeholder="Tour ID"
          class="mb-3 w-full rounded border p-2"
        />
        <input
          v-model="addBookingForm.date"
          type="date"
          class="mb-3 w-full rounded border p-2"
        />

        <div class="flex space-x-4">
          <label class="mb-1 block text-sm font-medium text-gray-700"> Adult Tickets </label>

          <input
            v-model="addBookingForm.adultTickets"
            type="number"
            placeholder="Adult Tickets"
            class="w-full rounded border p-2"
          />

          <label class="mb-1 block text-sm font-medium text-gray-700"> Child Tickets </label>

          <input
            v-model="addBookingForm.childTickets"
            type="number"
            placeholder="Child Tickets"
            class="w-full rounded border p-2"
          />
        </div>

        <div class="mt-4 flex justify-end space-x-3">
          <button
            class="rounded bg-gray-400 px-4 py-2 text-white hover:bg-gray-500"
            @click="closeAllModals"
          >
            Cancel
          </button>
          <button
            class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            @click="handleAddBooking"
          >
            Create
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showRescheduleModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="closeAllModals"
    >
      <div class="w-96 rounded-xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-xl font-bold">Reschedule Booking</h3>

        <input
          v-model="rescheduleForm.bookingId"
          placeholder="Enter ID"
          class="mb-3 w-full rounded border p-2"
        />
        <input
          v-model="rescheduleForm.newDate"
          type="date"
          class="mb-3 w-full rounded border p-2"
        />

        <div class="mt-4 flex justify-end space-x-3">
          <button
            class="rounded bg-gray-400 px-4 py-2 text-white hover:bg-gray-500"
            @click="closeAllModals"
          >
            Cancel
          </button>
          <button
            class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            @click="handleReschedule"
          >
            Done
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showReportIssueModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="closeAllModals"
    >
      <div class="w-96 rounded-xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-xl font-bold">Report Issue</h3>

        <textarea
          v-model="reportIssueForm.description"
          placeholder="Enter Description"
          class="h-32 w-full rounded border p-2"
        ></textarea>

        <div class="mt-4 flex justify-end space-x-3">
          <button class="rounded bg-gray-400 px-4 py-2 text-white" @click="closeAllModals">
            Go back
          </button>
          <button class="rounded bg-blue-600 px-4 py-2 text-white" @click="handleReportIssue">
            Submit
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="showCancelBookingModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="closeAllModals"
    >
      <div class="w-96 rounded-xl bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-xl font-bold">Cancel a booking</h3>

        <input
          v-model="cancelBookingForm.bookingId"
          placeholder="Booking ID"
          class="mb-3 w-full rounded border p-2"
        />

        <div class="mt-4 flex justify-end space-x-3">
          <button
            class="rounded bg-gray-400 px-4 py-2 text-white hover:bg-gray-500"
            @click="closeAllModals"
          >
            Go back
          </button>
          <button
            class="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            @click="handleCancelBooking"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
