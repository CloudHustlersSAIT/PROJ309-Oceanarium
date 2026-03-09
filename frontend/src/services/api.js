const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' // FastAPI default port
const RESERVATION_LANGUAGE_CACHE_KEY = 'reservation-language-cache-v1'

function getReservationLanguageCache() {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(RESERVATION_LANGUAGE_CACHE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function setReservationLanguageCache(cache) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(RESERVATION_LANGUAGE_CACHE_KEY, JSON.stringify(cache))
  } catch {
    // Ignore storage failures and keep app functional.
  }
}

function persistReservationLanguage(reservationId, language) {
  if (!reservationId || !language) return
  const cache = getReservationLanguageCache()
  cache[String(reservationId)] = String(language)
  setReservationLanguageCache(cache)
}

function resolveReservationId(item) {
  return item?.id ?? item?.booking_id ?? item?.bookingId ?? item?.clorian_reservation_id ?? null
}

function mapLanguageCodeToLabel(code) {
  const normalized = String(code || '').trim().toLowerCase()
  if (normalized === 'en') return 'English'
  if (normalized === 'pt') return 'Portuguese'
  if (normalized === 'es') return 'Spanish'
  if (normalized === 'fr') return 'French'
  if (normalized === 'zh') return 'Chinese'
  return ''
}

function formatApiErrorDetail(detail) {
  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const loc = Array.isArray(item.loc) ? item.loc.join('.') : ''
          const msg = item.msg || JSON.stringify(item)
          return loc ? `${loc}: ${msg}` : msg
        }
        return String(item)
      })
      .join('; ')
  }

  if (detail && typeof detail === 'object') {
    return detail.message || JSON.stringify(detail)
  }

  return ''
}

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
      let message = `API Error: ${response.status} ${response.statusText}`
      try {
        const errorBody = await response.clone().json()
        if (errorBody?.detail) {
          const detailMessage = formatApiErrorDetail(errorBody.detail)
          if (detailMessage) message = detailMessage
        }
      } catch {
        try {
          const errorText = await response.text()
          if (errorText) message = errorText
        } catch {
          // Keep fallback message when response body cannot be parsed.
        }
      }
      throw new Error(message)
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

// Get schedule events (calendar source-of-truth)
export async function getSchedules(filters = {}) {
  const params = new URLSearchParams()
  if (filters.startDate) params.set('start_date', filters.startDate)
  if (filters.endDate) params.set('end_date', filters.endDate)
  if (filters.status) params.set('status', filters.status)

  const query = params.toString()
  return fetchAPI(query ? `/schedules?${query}` : '/schedules')
}

// Get all bookings
export async function getBookings() {
  const data = await fetchAPI('/reservations')
  if (!Array.isArray(data)) return data

  const cache = getReservationLanguageCache()
  return data.map((item) => {
    const reservationId = resolveReservationId(item)
    const cachedLanguage = reservationId ? cache[String(reservationId)] : ''
    const languageFromCode = mapLanguageCodeToLabel(item?.language_code ?? item?.languageCode)
    const language = item?.language || languageFromCode || cachedLanguage || 'English'

    if (reservationId && language) {
      persistReservationLanguage(reservationId, language)
    }

    return {
      ...item,
      language,
    }
  })
}

// Create a new booking
export async function createBooking(bookingData) {
  if (bookingData?.schedule_id != null) {
    const normalizedPayload = {
      customer_id: Number(bookingData?.customer_id),
      schedule_id: Number(bookingData?.schedule_id),
      adult_tickets: Number(bookingData?.adult_tickets) || 0,
      child_tickets: Number(bookingData?.child_tickets) || 0,
    }

    return fetchAPI('/reservations', {
      method: 'POST',
      body: JSON.stringify(normalizedPayload),
    })
  }

  const normalizedPayload = {
    customer_id: String(bookingData?.customer_id ?? '').trim(),
    tour_id: Number(bookingData?.tour_id),
    language: bookingData?.language || 'English',
    date: bookingData?.date,
    start_time: bookingData?.start_time || '09:00:00',
    end_time: bookingData?.end_time || '10:00:00',
    adult_tickets: Number(bookingData?.adult_tickets) || 0,
    child_tickets: Number(bookingData?.child_tickets) || 0,
  }

  const created = await fetchAPI('/reservations', {
    method: 'POST',
    body: JSON.stringify(normalizedPayload),
  })

  const reservationId = resolveReservationId(created)
  if (reservationId) {
    persistReservationLanguage(reservationId, normalizedPayload.language)
  }

  return {
    ...created,
    language: created?.language || normalizedPayload.language,
  }
}

// Reschedule a booking
export async function rescheduleBooking(
  bookingId,
  newDate,
  startTime = '09:00:00',
  endTime = '10:00:00',
) {
  if (typeof newDate === 'number') {
    return fetchAPI(`/reservations/${bookingId}/reschedule`, {
      method: 'PATCH',
      body: JSON.stringify({
        new_schedule_id: newDate,
      }),
    })
  }

  if (newDate && typeof newDate === 'object' && newDate.new_schedule_id != null) {
    return fetchAPI(`/reservations/${bookingId}/reschedule`, {
      method: 'PATCH',
      body: JSON.stringify({
        new_schedule_id: Number(newDate.new_schedule_id),
      }),
    })
  }

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
