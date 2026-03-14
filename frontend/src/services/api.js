import { useAuth } from '../contexts/authContext'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

if (import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL) {
  console.warn('[api] VITE_API_BASE_URL is not set — falling back to http://localhost:8000')
}
const RESERVATION_LANGUAGE_CACHE_KEY = 'reservation-language-cache-v1'
const RESERVATION_LANGUAGE_CACHE_MAX_ENTRIES = 500
const RESERVATION_LANGUAGE_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000

//Auth header builder helper function
//Author Joao Santiago
async function getAuthorizationHeader() {
  try {
    const { getIdToken, isDevelopmentBypassSession } = useAuth()

    if (isDevelopmentBypassSession()) return {}

    const token = await getIdToken()

    if (!token) return {} // No token available, return empty headers

    return {
      Authorization: `Bearer ${token}`,
    }
  } catch {
    return {} // On error (e.g., Firebase not configured), return empty headers to allow API to handle auth errors gracefully
  }
}

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

const LANGUAGE_CODE_LABELS = {
  en: 'English',
  pt: 'Portuguese',
  es: 'Spanish',
  fr: 'French',
  zh: 'Chinese',
}

function mapLanguageCodeToLabel(code) {
  const normalized = String(code || '')
    .trim()
    .toLowerCase()
  return LANGUAGE_CODE_LABELS[normalized] || ''
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

// Generic fetch helper with authorization header support
async function fetchAPI(endpoint, options = {}) {
  const { requiresAuth = false, headers: customHeaders = {}, ...fetchOptions } = options

  // Build headers with optional auth
  const authHeaders = requiresAuth ? await getAuthorizationHeader() : {}

  // Fail early for authenticated requests when no token is available,
  // so callers can prompt login instead of sending an unauthenticated request.
  const { isDevelopmentBypassSession } = useAuth()
  if (requiresAuth && !authHeaders.Authorization && !isDevelopmentBypassSession()) {
    throw new Error('Authentication required. Please sign in to continue.')
  }
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...customHeaders,
    },
    ...fetchOptions,
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
}

// Get all guides
export async function getGuides() {
  return fetchAPI('/guides')
}

export async function updateGuide(guideId, payload) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to update guide details.')
  }

  return fetchAPI(`/guides/${normalizedGuideId}`, {
    method: 'PATCH',
    requiresAuth: true,
    body: JSON.stringify(payload || {}),
  })
}

// Get all customers
export async function getCustomers() {
  return fetchAPI('/customers')
}

// Get all tours
export async function getTours() {
  return fetchAPI('/tours')
}

export async function getNotifications(filters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.channel) params.set('channel', filters.channel)
  if (filters.eventType) params.set('event_type', filters.eventType)
  if (filters.priority) params.set('priority', filters.priority)
  if (filters.unreadOnly) params.set('unread_only', 'true')
  if (filters.limit) params.set('limit', String(filters.limit))
  if (filters.offset) params.set('offset', String(filters.offset))
  const query = params.toString()
  return fetchAPI(query ? `/notifications?${query}` : '/notifications', { requiresAuth: true })
}

export async function getNotificationSummary() {
  return fetchAPI('/notifications/summary', { requiresAuth: true })
}

export async function markNotificationRead(notificationId) {
  const normalizedNotificationId = Number(notificationId)
  if (!Number.isInteger(normalizedNotificationId) || normalizedNotificationId <= 0) {
    throw new Error('Notification ID is required to mark a notification as read.')
  }

  return fetchAPI(`/notifications/${normalizedNotificationId}/read`, {
    method: 'PATCH',
    requiresAuth: true,
  })
}

export async function markAllNotificationsRead() {
  return fetchAPI('/notifications/read-all', {
    method: 'PATCH',
    requiresAuth: true,
  })
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
  if (filters.guideId != null) params.set('guide_id', String(filters.guideId))

  const query = params.toString()
  return fetchAPI(query ? `/schedules?${query}` : '/schedules')
}

// Create a new schedule
export async function createSchedule(scheduleData) {
  const tourId = Number(scheduleData?.tour_id)
  const languageCode = String(scheduleData?.language_code || '')
    .trim()
    .toLowerCase()
  const eventStartDateTime = String(scheduleData?.event_start_datetime || '').trim()
  const eventEndDateTime = String(scheduleData?.event_end_datetime || '').trim()

  if (!Number.isInteger(tourId) || tourId <= 0) {
    throw new Error('Tour is required and must be valid.')
  }

  if (!/^[a-z]{2}$/.test(languageCode)) {
    throw new Error('Language code is required and must be 2 letters (e.g., en, pt).')
  }

  if (!eventStartDateTime || !eventEndDateTime) {
    throw new Error('Start and End datetime are required.')
  }

  const startParsed = new Date(eventStartDateTime)
  const endParsed = new Date(eventEndDateTime)
  if (Number.isNaN(startParsed.getTime()) || Number.isNaN(endParsed.getTime())) {
    throw new Error('Start and End datetime must be valid ISO datetime values.')
  }

  if (endParsed <= startParsed) {
    throw new Error('End datetime must be after Start datetime.')
  }

  return fetchAPI('/schedules', {
    method: 'POST',
    body: JSON.stringify({
      tour_id: tourId,
      language_code: languageCode,
      event_start_datetime: startParsed.toISOString(),
      event_end_datetime: endParsed.toISOString(),
    }),
  })
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
    requiresAuth: true,
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
      requiresAuth: true,
      body: JSON.stringify({
        new_schedule_id: newDate,
      }),
    })
  }

  if (newDate && typeof newDate === 'object' && newDate.new_schedule_id != null) {
    return fetchAPI(`/reservations/${bookingId}/reschedule`, {
      method: 'PATCH',
      requiresAuth: true,
      body: JSON.stringify({
        new_schedule_id: Number(newDate.new_schedule_id),
      }),
    })
  }

  return fetchAPI(`/reservations/${bookingId}/reschedule`, {
    method: 'PATCH',
    requiresAuth: true,
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
    requiresAuth: true,
  })
}

// Report an issue
export async function reportIssue(description) {
  return fetchAPI('/issues', {
    method: 'POST',
    requiresAuth: true,
    body: JSON.stringify({ description }),
  })
}

export async function getGuideSwapRequests(guideId) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to load swap requests.')
  }

  return fetchAPI(`/guide/swap-requests?guide_id=${normalizedGuideId}`)
}

export async function getGuideDashboard(guideId) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to load the dashboard.')
  }

  return fetchAPI(`/guide/dashboard?guide_id=${normalizedGuideId}`)
}

export async function getGuideSwapCandidates(scheduleId) {
  const normalizedScheduleId = Number(scheduleId)
  if (!Number.isInteger(normalizedScheduleId) || normalizedScheduleId <= 0) {
    throw new Error('Schedule ID is required to load swap candidates.')
  }

  return fetchAPI(`/guide/swap-candidates?schedule_id=${normalizedScheduleId}`)
}

export async function createGuideSwapRequest(scheduleId, guideId, requestingGuideId) {
  const normalizedScheduleId = Number(scheduleId)
  const normalizedGuideId = Number(guideId)
  const normalizedRequestingGuideId = Number(requestingGuideId)

  if (!Number.isInteger(normalizedScheduleId) || normalizedScheduleId <= 0) {
    throw new Error('Schedule ID is required to create a swap request.')
  }

  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to create a swap request.')
  }

  if (!Number.isInteger(normalizedRequestingGuideId) || normalizedRequestingGuideId <= 0) {
    throw new Error('Requesting guide ID is required to create a swap request.')
  }

  return fetchAPI(
    `/guide/swap-request?schedule_id=${normalizedScheduleId}&guide_id=${normalizedGuideId}&requesting_guide_id=${normalizedRequestingGuideId}`,
    {
      method: 'POST',
    },
  )
}

export async function acceptGuideSwapRequest(swapRequestId, guideId) {
  const normalizedSwapRequestId = Number(swapRequestId)
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedSwapRequestId) || normalizedSwapRequestId <= 0) {
    throw new Error('Swap request ID is required to accept a request.')
  }

  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to accept a request.')
  }

  return fetchAPI(
    `/guide/swap-accept?swap_request_id=${normalizedSwapRequestId}&guide_id=${normalizedGuideId}`,
    {
      method: 'POST',
    },
  )
}

export async function rejectGuideSwapRequest(swapRequestId, guideId) {
  const normalizedSwapRequestId = Number(swapRequestId)
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedSwapRequestId) || normalizedSwapRequestId <= 0) {
    throw new Error('Swap request ID is required to reject a request.')
  }

  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to reject a request.')
  }

  return fetchAPI(
    `/guide/swap-reject?swap_request_id=${normalizedSwapRequestId}&guide_id=${normalizedGuideId}`,
    {
      method: 'POST',
    },
  )
}

export async function getLanguages() {
  return fetchAPI('/languages')
}

export async function getGuideAvailability(guideId) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to load availability.')
  }

  return fetchAPI(`/guide/profile/availability?guide_id=${normalizedGuideId}`)
}

export async function updateGuideAvailability(guideId, payload) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to update availability.')
  }

  return fetchAPI(`/guide/profile/availability?guide_id=${normalizedGuideId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      slots: Array.isArray(payload?.slots) ? payload.slots : [],
      timezone: payload?.timezone || undefined,
    }),
  })
}

export async function getGuideLanguages(guideId) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to load languages.')
  }

  return fetchAPI(`/guide/profile/languages?guide_id=${normalizedGuideId}`)
}

export async function updateGuideLanguages(guideId, payload) {
  const normalizedGuideId = Number(guideId)
  if (!Number.isInteger(normalizedGuideId) || normalizedGuideId <= 0) {
    throw new Error('Guide ID is required to update languages.')
  }

  const languageIds = Array.isArray(payload?.language_ids) ? payload.language_ids.map(Number) : []

  return fetchAPI(`/guide/profile/languages?guide_id=${normalizedGuideId}`, {
    method: 'PATCH',
    body: JSON.stringify({ language_ids: languageIds }),
  })
}
