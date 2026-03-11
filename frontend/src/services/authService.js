const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function formatApiErrorDetail(detail) {
  if (typeof detail === 'string' && detail.trim()) return detail

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

export async function getCurrentAuthenticatedUser(idToken) {
  const headers = {
    'Content-Type': 'application/json',
  }

  if (idToken) {
    headers.Authorization = `Bearer ${idToken}`
  }

  const response = await fetch(`${VITE_API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    let message = 'Failed to resolve the authenticated user.'
    try {
      const errorBody = await response.json()
      const detail = formatApiErrorDetail(errorBody?.detail)
      if (detail) message = detail
    } catch {
      // Keep fallback when the response body is not JSON.
    }

    const error = new Error(message)
    error.status = response.status
    throw error
  }

  return response.json()
}

export function getDefaultRouteForRole(role) {
  return role === 'guide' ? '/guide/home' : '/home'
}
