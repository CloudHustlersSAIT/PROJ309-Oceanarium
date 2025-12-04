<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'
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

const router = useRouter()
const { user, logout } = useAuth()

// Reactive state for modals
const showGuidesModal = ref(false)
const showAddBookingModal = ref(false)
const showRescheduleModal = ref(false)
const showReportIssueModal = ref(false)
const showCancelBookingModal = ref(false)

// Form data
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

// Data from database
const guidesWorking = ref([])
const tours = ref([])
const notifications = ref([])
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

// Close all modals
const closeAllModals = () => {
  showGuidesModal.value = false
  showAddBookingModal.value = false
  showRescheduleModal.value = false
  showReportIssueModal.value = false
  showCancelBookingModal.value = false
}

// Load data from database
async function loadData() {
  try {
    guidesWorking.value = await getGuides()
    tours.value = await getTours()
    notifications.value = await getNotifications()
    stats.value = await getStats()
    console.log('Data loaded successfully')
  } catch (error) {
    console.error('Failed to load data:', error)
    alert(
      'Failed to load data from database. Make sure backend is running on http://localhost:8000',
    )
  }
}

// Handle add booking
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
    await loadData() // Reload stats

    // Reset form
    addBookingForm.value = {
      customer_id: '',
      tour_id: '',
      date: '',
      adult_tickets: 0,
      child_tickets: 0,
    }
  } catch (error) {
    console.error('Failed to create booking:', error)
    alert('Failed to create booking')
  }
}

// Handle reschedule
async function handleReschedule() {
  try {
    await rescheduleBooking(rescheduleForm.value.bookingId, rescheduleForm.value.newDate)

    alert('Booking rescheduled successfully!')
    closeAllModals()

    // Reset form
    rescheduleForm.value = {
      bookingId: '',
      newDate: '',
    }
  } catch (error) {
    console.error('Failed to reschedule booking:', error)
    alert('Failed to reschedule booking')
  }
}

// Handle cancel booking
async function handleCancelBooking() {
  try {
    await cancelBooking(cancelBookingForm.value.bookingId)

    alert('Booking cancelled successfully!')
    closeAllModals()
    await loadData() // Reload stats

    // Reset form
    cancelBookingForm.value = {
      bookingId: '',
    }
  } catch (error) {
    console.error('Failed to cancel booking:', error)
    alert('Failed to cancel booking')
  }
}

// Handle report issue
async function handleReportIssue() {
  try {
    await reportIssue(reportIssueForm.value.description)

    alert('Issue reported successfully!')
    closeAllModals()

    // Reset form
    reportIssueForm.value = {
      description: '',
    }
  } catch (error) {
    console.error('Failed to report issue:', error)
    alert('Failed to report issue')
  }
}

// Greeting based on time
const greeting = ref('')
onMounted(async () => {
  const hour = new Date().getHours()
  if (hour < 12) greeting.value = 'Good Morning'
  else if (hour < 18) greeting.value = 'Good Afternoon'
  else greeting.value = 'Good Evening'

  // Load all data from database
  await loadData()
})

// Function to handle user logout
async function handleLogout() {
  try {
    await logout()
    router.push('/login')
  } catch (err) {
    console.error('Error logging out:', err)
  }
}
</script>

<!--Template for the home page-->
<template>
  <div class="flex min-h-screen">
    <Sidebar />
    <!-- Main Content -->
    <main class="flex-1">
      <div class="p-8">
        <h1 class="text-3xl font-bold text-gray-800">{{ greeting }}, Lucas!</h1>
        <p class="text-lg text-gray-600 mt-1">Here's what's happening at the Oceanarium Today</p>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
          <!-- Column 1: Today's Schedule -->
          <div class="bg-white rounded-xl shadow-md p-6 border-1 border-blue-500">
            <h2 class="text-xl font-semibold flex items-center">
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

          <!-- Column 2: Quick KPIs and Quick Actions -->
          <div class="space-y-6">
            <!-- KPIs -->
            <div class="bg-white rounded-xl shadow-md p-6 border-1 border-blue-500">
              <h3 class="text-lg font-semibold mb-4">Quick KPIs</h3>
              <div class="grid grid-cols-3 gap-4">
                <!-- Top row: 3 equal columns -->
                <div class="bg-blue-100 rounded-lg p-4 text-center">
                  <p class="text-sm text-gray-600">Tours Today</p>
                  <p class="text-3xl font-bold text-blue-800">14</p>
                </div>
                <div class="bg-blue-100 rounded-lg p-4 text-center">
                  <p class="text-sm text-gray-600">Customers Today</p>
                  <p class="text-3xl font-bold text-blue-800">84</p>
                </div>
                <div class="bg-blue-100 rounded-lg p-4 text-center">
                  <p class="text-sm text-gray-600">Cancellations</p>
                  <p class="text-3xl font-bold text-blue-800">2</p>
                </div>
                <!-- Bottom row: full width single column -->
                <div class="bg-blue-100 rounded-lg p-4 text-center col-span-3">
                  <p class="text-sm text-gray-600">Avg Guide Rating</p>
                  <p class="text-3xl font-bold text-blue-800">5.0</p>
                </div>
              </div>
            </div>

            <!-- Quick Actions -->
            <div class="bg-white rounded-xl shadow-md p-6 border-1 border-blue-500">
              <h3 class="text-lg font-semibold mb-4">Your Quick Actions</h3>
              <div class="grid grid-cols-3 gap-4 text-center">
                <button
                  @click="showAddBookingModal = true"
                  class="bg-yellow-400 hover:bg-yellow-500 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <span class="text-2xl">+</span>
                  <span class="text-xs mt-1">Add Booking</span>
                </button>

                <button
                  @click="showGuidesModal = true"
                  class="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 4.354a4 4 0 110 5.292M15 21H9v-1c0-2.21 1.79-4 4-4h2c2.21 0 4 1.79 4 4v1z"
                    />
                  </svg>
                  <span class="text-xs mt-1">View Guides</span>
                </button>

                <button
                  @click="showRescheduleModal = true"
                  class="bg-green-500 hover:bg-green-600 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <span class="text-2xl">↻</span>
                  <span class="text-xs mt-1">Reschedule</span>
                </button>

                <button
                  @click="showCancelBookingModal = true"
                  class="bg-red-500 hover:bg-red-600 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <span class="text-2xl">✕</span>
                  <span class="text-xs mt-1">Cancel Booking</span>
                </button>

                <button
                  @click="showReportIssueModal = true"
                  class="bg-orange-500 hover:bg-orange-600 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <span class="text-2xl">!</span>
                  <span class="text-xs mt-1">Report Issue</span>
                </button>

                <button
                  class="bg-gray-600 hover:bg-gray-700 text-white rounded-lg p-4 flex flex-col items-center"
                >
                  <span class="text-2xl">↓</span>
                  <span class="text-xs mt-1">Export</span>
                </button>
              </div>
            </div>
          </div>
          <!-- End of Column 2 -->

          <!-- Column 3: Notifications and Recent Activity -->
          <div class="space-y-6">
            <!-- Notifications -->
            <div class="bg-white rounded-xl shadow-md p-6 border-1 border-blue-500">
              <h3 class="text-lg font-semibold flex items-center mb-4">
                <span class="mr-2">🔔</span> Your recent notifications
              </h3>
              <ul class="space-y-3 text-sm">
                <li v-for="n in notifications" :key="n.time" class="border-b pb-2">
                  <span class="text-gray-500">{{ n.time }}:</span> {{ n.text }}
                </li>
              </ul>
            </div>

            <!-- Recent Activity -->
            <div class="bg-white rounded-xl shadow-md p-6 border-1 border-blue-500">
              <h3 class="text-lg font-semibold flex items-center mb-4">
                <span class="mr-2">↑</span> Recent Activity
              </h3>
              <ul class="space-y-3 text-sm">
                <li v-for="a in recentActivity" :key="a.time" class="border-b pb-2">
                  <span class="text-gray-500">{{ a.time }}</span
                  ><br />
                  {{ a.text }}
                </li>
              </ul>
            </div>
          </div>
          <!-- End of Column 3 -->
        </div>
        <!-- End of grid -->
      </div>
    </main>

    <!-- Modals -->
    <!-- View Guides Modal-->
    <div
      v-if="showGuidesModal"
      class="fixed inset-0 flex items-center justify-center z-50"
      @click.self="closeAllModals"
    >
      <div class="bg-white rounded-xl shadow-xl p-6 w-96">
        <h3 class="text-xl font-bold mb-4">Guides Working Today</h3>
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-blue-600 text-white">
              <th class="py-2 px-4 text-left">Guide Name</th>
              <th class="py-2 px-4">Working Hours</th>
              <th class="py-2 px-4">Available now?</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in guidesWorking" :key="g.name" class="border-b">
              <td class="py-2 px-4">{{ g.name }}</td>
              <td class="py-2 px-4 text-center">{{ g.working_hours }}</td>
              <td class="py-2 px-4 text-center">
                <span :class="g.is_available ? 'text-green-600' : 'text-red-600'">{{
                  g.is_available ? 'Yes' : 'No'
                }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <button
          @click="closeAllModals"
          class="mt-4 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
        >
          Close
        </button>
      </div>
    </div>

    <!-- Add Booking Modal -->
    <div
      v-if="showAddBookingModal"
      class="fixed inset-0 flex items-center justify-center z-50"
      @click.self="closeAllModals"
    >
      <div class="bg-white rounded-xl shadow-xl p-6 w-96">
        <h3 class="text-xl font-bold mb-4">Add new booking</h3>
        <input
          v-model="addBookingForm.customerId"
          placeholder="Customer ID"
          class="w-full border p-2 mb-3 rounded"
        />
        <input
          v-model="addBookingForm.tourId"
          placeholder="Tour ID"
          class="w-full border p-2 mb-3 rounded"
        />
        <input type="date" v-model="addBookingForm.date" class="w-full border p-2 mb-3 rounded" />
        <div class="flex space-x-4">
          <label class="block text-sm font-medium text-gray-700 mb-1"> Adult Tickets </label>

          <input
            type="number"
            v-model="addBookingForm.adultTickets"
            placeholder="Adult Tickets"
            class="w-full border p-2 rounded"
          />
          <label class="block text-sm font-medium text-gray-700 mb-1"> Child Tickets </label>
          <input
            type="number"
            v-model="addBookingForm.childTickets"
            placeholder="Child Tickets"
            class="w-full border p-2 rounded"
          />
        </div>
        <div class="mt-4 flex justify-end space-x-3">
          <button
            @click="closeAllModals"
            class="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500"
          >
            Cancel
          </button>
          <button
            @click="handleAddBooking"
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Create
          </button>
        </div>
      </div>
    </div>

    <!-- Reschedule Modal -->
    <div
      v-if="showRescheduleModal"
      class="fixed inset-0 flex items-center justify-center z-50"
      @click.self="closeAllModals"
    >
      <div class="bg-white rounded-xl shadow-xl p-6 w-96">
        <h3 class="text-xl font-bold mb-4">Reschedule Booking</h3>
        <input
          v-model="rescheduleForm.bookingId"
          placeholder="Enter ID"
          class="w-full border p-2 mb-3 rounded"
        />
        <input
          type="date"
          v-model="rescheduleForm.newDate"
          class="w-full border p-2 mb-3 rounded"
        />
        <div class="mt-4 flex justify-end space-x-3">
          <button
            @click="closeAllModals"
            class="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500"
          >
            Cancel
          </button>
          <button
            @click="handleReschedule"
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Done
          </button>
        </div>
      </div>
    </div>

    <!-- Report Issue Modal -->
    <div
      v-if="showReportIssueModal"
      class="fixed inset-0 flex items-center justify-center z-50"
      @click.self="closeAllModals"
    >
      <div class="bg-white rounded-xl shadow-xl p-6 w-96">
        <h3 class="text-xl font-bold mb-4">Report Issue</h3>
        <textarea
          v-model="reportIssueForm.description"
          placeholder="Enter Description"
          class="w-full border p-2 h-32 rounded"
        ></textarea>
        <div class="mt-4 flex justify-end space-x-3">
          <button @click="closeAllModals" class="bg-gray-400 text-white px-4 py-2 rounded">
            Go back
          </button>
          <button @click="handleReportIssue" class="bg-blue-600 text-white px-4 py-2 rounded">
            Submit
          </button>
        </div>
      </div>
    </div>

    <!-- Cancel Booking Modal -->
    <div
      v-if="showCancelBookingModal"
      class="fixed inset-0 flex items-center justify-center z-50"
      @click.self="closeAllModals"
    >
      <div class="bg-white rounded-xl shadow-xl p-6 w-96">
        <h3 class="text-xl font-bold mb-4">Cancel a booking</h3>
        <input
          v-model="cancelBookingForm.bookingId"
          placeholder="Booking ID"
          class="w-full border p-2 mb-3 rounded"
        />
        <div class="mt-4 flex justify-end space-x-3">
          <button
            @click="closeAllModals"
            class="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500"
          >
            Go back
          </button>
          <button
            @click="handleCancelBooking"
            class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
