const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' // FastAPI default port
const RESERVATION_LANGUAGE_CACHE_KEY = 'reservation-language-cache-v1'
const RESERVATION_LANGUAGE_CACHE_MAX_ENTRIES = 500
const RESERVATION_LANGUAGE_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000

function normalizeReservationLanguageCacheEntry(entry) {
  if (typeof entry === 'string') {
    return { language: entry, updatedAt: 0 }
  }

  if (entry && typeof entry === 'object' && typeof entry.language === 'string') {
    const updatedAt = Number(entry.updatedAt)
    return {
      language: entry.language,
      updatedAt: Number.isFinite(updatedAt) ? updatedAt : 0,
    }
  }

  return null
}

function pruneReservationLanguageCache(cache) {
  const now = Date.now()
  const normalizedEntries = Object.entries(cache || {})
    .map(([reservationId, value]) => {
      const normalized = normalizeReservationLanguageCacheEntry(value)
      if (!normalized) return null
      if (!normalized.language.trim()) return null

      const age = now - normalized.updatedAt
      if (normalized.updatedAt > 0 && age > RESERVATION_LANGUAGE_CACHE_TTL_MS) return null

      return [reservationId, normalized]
    })
    .filter(Boolean)
    .sort((a, b) => b[1].updatedAt - a[1].updatedAt)
    .slice(0, RESERVATION_LANGUAGE_CACHE_MAX_ENTRIES)

  return Object.fromEntries(normalizedEntries)
}

function getReservationLanguageCache() {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(RESERVATION_LANGUAGE_CACHE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    const normalizedCache = parsed && typeof parsed === 'object' ? parsed : {}
    return pruneReservationLanguageCache(normalizedCache)
  } catch {
    return {}
  }
}

function setReservationLanguageCache(cache) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(
      RESERVATION_LANGUAGE_CACHE_KEY,
      JSON.stringify(pruneReservationLanguageCache(cache)),
    )
  } catch {
    // Ignore storage failures and keep app functional.
  }
}

function persistReservationLanguage(reservationId, language) {
  if (!reservationId || !language) return
  const cache = getReservationLanguageCache()
  cache[String(reservationId)] = {
    language: String(language),
    updatedAt: Date.now(),
  }
  setReservationLanguageCache(cache)
}

function resolveReservationId(item) {
  return item?.id ?? item?.booking_id ?? item?.bookingId ?? item?.clorian_reservation_id ?? null
}

function mapLanguageCodeToLabel(code) {
  const normalized = String(code || '')
    .trim()
    .toLowerCase()
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
    const cachedLanguage = reservationId
      ? normalizeReservationLanguageCacheEntry(cache[String(reservationId)])?.language || ''
      : ''
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
  const customerId = Number(bookingData?.customer_id)
  const scheduleId = Number(bookingData?.schedule_id)
  const adultTickets = Number(bookingData?.adult_tickets) || 0
  const childTickets = Number(bookingData?.child_tickets) || 0

  if (!Number.isInteger(customerId) || customerId <= 0) {
    throw new Error('Customer ID must be a valid positive number.')
  }

  if (!Number.isInteger(scheduleId) || scheduleId <= 0) {
    throw new Error('Schedule is required and must be valid.')
  }

  if (adultTickets < 0 || childTickets < 0) {
    throw new Error('Ticket counts cannot be negative.')
  }

  if (adultTickets + childTickets <= 0) {
    throw new Error('At least one ticket is required.')
  }

  const normalizedPayload = {
    customer_id: customerId,
    schedule_id: scheduleId,
    adult_tickets: adultTickets,
    child_tickets: childTickets,
  }

  return fetchAPI('/reservations', {
    method: 'POST',
    body: JSON.stringify(normalizedPayload),
  })
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
