const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

    if (response.status === 204) return null

    return await response.json()
  } catch (error) {
    throw error
  }
}

// Guides
export async function getGuides() {
  return fetchAPI('/guides')
}

// Tours
export async function getTours() {
  return fetchAPI('/tours')
}

export async function createTour(tourData) {
  return fetchAPI('/tours', {
    method: 'POST',
    body: JSON.stringify(tourData),
  })
}

// Notifications
export async function getNotifications() {
  return fetchAPI('/notifications')
}

// Stats
export async function getStats() {
  return fetchAPI('/stats')
}

// Bookings
export async function getBookings(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return fetchAPI(`/bookings${query}`)
}

export async function createBooking(bookingData) {
  return fetchAPI('/bookings', {
    method: 'POST',
    body: JSON.stringify(bookingData),
  })
}

export async function rescheduleBooking(bookingId, newDate) {
  return fetchAPI(`/bookings/${bookingId}/reschedule`, {
    method: 'PATCH',
    body: JSON.stringify({ new_date: newDate }),
  })
}

export async function confirmBooking(bookingId) {
  return fetchAPI(`/bookings/${bookingId}/confirm`, {
    method: 'PATCH',
  })
}

export async function cancelBooking(bookingId) {
  return fetchAPI(`/bookings/${bookingId}/cancel`, {
    method: 'PATCH',
  })
}

// Costs
export async function getCosts(tourId) {
  const query = tourId ? `?tour_id=${tourId}` : ''
  return fetchAPI(`/costs${query}`)
}

export async function createCost(costData) {
  return fetchAPI('/costs', {
    method: 'POST',
    body: JSON.stringify(costData),
  })
}

// Schedules
export async function getSchedules(guideId) {
  const query = guideId ? `?guide_id=${guideId}` : ''
  return fetchAPI(`/schedules${query}`)
}

export async function createSchedule(scheduleData) {
  return fetchAPI('/schedules', {
    method: 'POST',
    body: JSON.stringify(scheduleData),
  })
}

// Customers
export async function getCustomers() {
  return fetchAPI('/customers')
}

export async function createCustomer(customerData) {
  return fetchAPI('/customers', {
    method: 'POST',
    body: JSON.stringify(customerData),
  })
}

// Resources
export async function getResources() {
  return fetchAPI('/resources')
}

export async function createResource(resourceData) {
  return fetchAPI('/resources', {
    method: 'POST',
    body: JSON.stringify(resourceData),
  })
}

// Surveys
export async function getSurveys() {
  return fetchAPI('/surveys')
}

export async function createSurvey(surveyData) {
  return fetchAPI('/surveys', {
    method: 'POST',
    body: JSON.stringify(surveyData),
  })
}

// Issues
export async function reportIssue(description) {
  return fetchAPI('/issues', {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}
