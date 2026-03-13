// src/contexts/authContext.js
import { computed, ref } from 'vue'
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { auth, firebaseDisabled } from '../utils/firebase'
import { getCurrentAuthenticatedUser } from '../services/authService'

// Reactive references to hold auth state
const currentUser = ref(null)
const profile = ref(null)
const authLoading = ref(true)
const profileLoading = ref(false)
const authError = ref(null)
const developmentBypassEnabled =
  import.meta.env.DEV &&
  ['1', 'true', 'yes', 'on'].includes(String(import.meta.env.VITE_ENABLE_AUTH_BYPASS || '').toLowerCase())
const DEVELOPMENT_BYPASS_STORAGE_KEY = 'oceanarium-dev-auth-bypass'
const DEVELOPMENT_BYPASS_EMAIL_STORAGE_KEY = 'oceanarium-dev-auth-bypass-email'
let profileRequestId = 0
let initialAuthResolved = false
let resolveInitialAuthPromise

const initialAuthPromise = new Promise((resolve) => {
  resolveInitialAuthPromise = resolve
})

function finishInitialAuthResolution() {
  if (!initialAuthResolved) {
    initialAuthResolved = true
    resolveInitialAuthPromise?.()
  }
}

function setDevelopmentBypassStorage(enabled) {
  if (typeof window === 'undefined') return

  try {
    if (enabled) {
      window.sessionStorage.setItem(DEVELOPMENT_BYPASS_STORAGE_KEY, '1')
    } else {
      window.sessionStorage.removeItem(DEVELOPMENT_BYPASS_STORAGE_KEY)
      window.sessionStorage.removeItem(DEVELOPMENT_BYPASS_EMAIL_STORAGE_KEY)
    }
  } catch {
    // Ignore storage failures in development.
  }
}

function setDevelopmentBypassEmailStorage(email) {
  if (typeof window === 'undefined') return

  try {
    const normalizedEmail = String(email || '').trim().toLowerCase()
    if (normalizedEmail) {
      window.sessionStorage.setItem(DEVELOPMENT_BYPASS_EMAIL_STORAGE_KEY, normalizedEmail)
    } else {
      window.sessionStorage.removeItem(DEVELOPMENT_BYPASS_EMAIL_STORAGE_KEY)
    }
  } catch {
    // Ignore storage failures in development.
  }
}

function hasDevelopmentBypassStorage() {
  if (typeof window === 'undefined') return false

  try {
    return window.sessionStorage.getItem(DEVELOPMENT_BYPASS_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

function getDevelopmentBypassEmailStorage() {
  if (typeof window === 'undefined') return null

  try {
    const email = window.sessionStorage.getItem(DEVELOPMENT_BYPASS_EMAIL_STORAGE_KEY)
    return email ? String(email).trim().toLowerCase() : null
  } catch {
    return null
  }
}

function buildDevelopmentBypassUser(authenticatedProfile) {
  return {
    uid: authenticatedProfile?.uid || 'local-dev-user',
    email: authenticatedProfile?.email || null,
    isDevelopmentBypass: true,
    async getIdToken() {
      return null
    },
  }
}

async function syncAuthenticatedProfile(user) {
  const requestId = ++profileRequestId

  if (!user) {
    profile.value = null
    profileLoading.value = false
    return null
  }

  profileLoading.value = true

  try {
    const idToken = await user.getIdToken()
    const authenticatedProfile = await getCurrentAuthenticatedUser(idToken)

    if (requestId === profileRequestId) {
      profile.value = authenticatedProfile
    }

    return authenticatedProfile
  } catch (err) {
    if (requestId === profileRequestId) {
      profile.value = null
      authError.value = err
    }
    throw err
  } finally {
    if (requestId === profileRequestId) {
      profileLoading.value = false
    }
  }
}

async function syncDevelopmentBypassProfile(emailOverride = null) {
  const requestId = ++profileRequestId
  profileLoading.value = true

  try {
    const bypassEmail = String(emailOverride || getDevelopmentBypassEmailStorage() || '').trim().toLowerCase()
    const authenticatedProfile = await getCurrentAuthenticatedUser(null, bypassEmail || null)

    if (requestId === profileRequestId) {
      profile.value = authenticatedProfile
      currentUser.value = buildDevelopmentBypassUser(authenticatedProfile)
      authError.value = null
      setDevelopmentBypassStorage(true)
      setDevelopmentBypassEmailStorage(authenticatedProfile?.email || bypassEmail)
    }

    return authenticatedProfile
  } catch (err) {
    if (requestId === profileRequestId) {
      currentUser.value = null
      profile.value = null
      authError.value = err
      setDevelopmentBypassStorage(false)
      setDevelopmentBypassEmailStorage(null)
    }
    throw err
  } finally {
    if (requestId === profileRequestId) {
      profileLoading.value = false
    }
  }
}

// If Firebase is configured, listen for auth state changes.
// Otherwise keep user null and set loading=false so the app can render.
if (developmentBypassEnabled && hasDevelopmentBypassStorage()) {
  syncDevelopmentBypassProfile()
    .catch(() => {
      // Keep the app on the login page when bypass restore fails.
    })
    .finally(() => {
      authLoading.value = false
      finishInitialAuthResolution()
    })
} else if (!firebaseDisabled && auth) {
  onAuthStateChanged(auth, async (user) => {
    currentUser.value = user
    authError.value = null

    try {
      await syncAuthenticatedProfile(user)
    } catch {
      // Keep the Firebase session visible so callers can surface the backend mapping error.
    } finally {
      authLoading.value = false
      finishInitialAuthResolution()
    }
  })
} else {
  currentUser.value = null
  profile.value = null
  authLoading.value = false
  profileLoading.value = false
  finishInitialAuthResolution()
}

/////////////////////////////////////////////////
//                                             //
// Helper functions for authentication actions //
//                                             //
/////////////////////////////////////////////////

// Login function
async function loginWithEmail(email, password) {
  authError.value = null
  if (developmentBypassEnabled) {
    return syncDevelopmentBypassProfile(email)
  }
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot perform login.')
    authError.value = err
    throw err
  }
  try {
    const cred = await signInWithEmailAndPassword(auth, email, password)
    await syncAuthenticatedProfile(cred.user)
    return cred.user
  } catch (err) {
    if (auth.currentUser) {
      await signOut(auth)
    }
    currentUser.value = null
    profile.value = null
    authError.value = err
    throw err
  }
}

// Logout function
async function logout() {
  authError.value = null
  profile.value = null
  setDevelopmentBypassStorage(false)
  if (currentUser.value?.isDevelopmentBypass) {
    currentUser.value = null
    return
  }
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot logout.')
    authError.value = err
    throw err
  }
  try {
    await signOut(auth)
    currentUser.value = null
  } catch (err) {
    authError.value = err
    throw err
  }
}

// Password reset function
async function passwordResetWithEmail(email) {
  authError.value = null
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot reset password.')
    authError.value = err
    throw err
  }
  try {
    await sendPasswordResetEmail(auth, email)
  } catch (err) {
    authError.value = err
    throw err
  }
}

//Token helper
async function getIdToken() {
  authError.value = null
  if (!auth || !currentUser.value) {
    return null
  }

  try {
    return await currentUser.value.getIdToken()
  } catch (err) {
    authError.value = err
    throw err
  }
}

async function ensureAuthReady() {
  if (!initialAuthResolved) {
    await initialAuthPromise
  }

  if (currentUser.value?.isDevelopmentBypass && !profile.value && !profileLoading.value) {
    await syncDevelopmentBypassProfile()
  }

  if (currentUser.value && !profile.value && !profileLoading.value) {
    await syncAuthenticatedProfile(currentUser.value)
  }

  return profile.value
}

function isDevelopmentBypassSession() {
  return currentUser.value?.isDevelopmentBypass === true
}

// Composable-style function to use in components
export function useAuth() {
  return {
    user: currentUser,
    profile,
    role: computed(() => profile.value?.role || null),
    loading: authLoading,
    profileLoading,
    error: authError,
    loginWithEmail,
    logout,
    passwordResetWithEmail,
    getIdToken,
    ensureAuthReady,
    isDevelopmentBypassSession,
  }
}
