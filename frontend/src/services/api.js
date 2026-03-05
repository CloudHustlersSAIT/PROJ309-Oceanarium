const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' // FastAPI default port

// Generic fetch helper
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${VITE_API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    // API request failed - error will be handled by caller
    throw error
  }
}

// Get all guides
export async function getGuides() {
  return fetchAPI('/guides')
}

// Get all tours
export async function getTours() {
  return fetchAPI('/tours')
}

// Get all notifications
export async function getNotifications() {
  return fetchAPI('/notifications')
}

// Get dashboard stats
export async function getStats() {
  return fetchAPI('/stats')
}

// Get all bookings
export async function getBookings() {
  return fetchAPI('/reservations')
}

// Create a new booking
export async function createBooking(bookingData) {
  return fetchAPI('/bookings', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// Reschedule a booking
export async function rescheduleBooking(
  bookingId,
  newDate,
  startTime = '09:00:00',
  endTime = '10:00:00',
) {
  return fetchAPI(`/reservations/${bookingId}/reschedule`, {
    method: 'PATCH',
    body: JSON.stringify({
      new_date: newDate,
      start_time: startTime,
      end_time: endTime,
    }),
  })
}

// Cancel a booking
export async function cancelBooking(bookingId) {
  return fetchAPI(`/reservations/${bookingId}/cancel`, {
    method: 'PATCH',
  })
}

// Report an issue
export async function reportIssue(description) {
  return fetchAPI('/issues', {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}
