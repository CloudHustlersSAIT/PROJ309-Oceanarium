import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

// Read env vars
const apiKey = import.meta.env.VITE_FIREBASE_API_KEY
const authDomain = import.meta.env.VITE_FIREBASE_AUTH_DOMAIN
const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID
const storageBucket = import.meta.env.VITE_FIREBASE_STORAGE_BUCKET
const messagingSenderId = import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID
const appId = import.meta.env.VITE_FIREBASE_APP_ID

let auth = null
let firebaseDisabled = false

if (!apiKey || !authDomain || !projectId || !appId) {
  // Missing configuration — avoid initializing Firebase to prevent runtime exceptions
  // This allows the app to load in environments where Firebase is optional.
  // Note: In production, ensure all VITE_FIREBASE_* environment variables are set
  // Development warning removed for production builds (auto-dropped by Vite config)
  if (import.meta.env.DEV) {
    console.warn(
      'Firebase not initialized: missing VITE_FIREBASE_* environment variables. Authentication will be disabled.',
    )
  }
  firebaseDisabled = true
} else {
  const firebaseConfig = {
    apiKey,
    authDomain,
    projectId,
    storageBucket,
    messagingSenderId,
    appId,
  }

  const app = initializeApp(firebaseConfig)
  auth = getAuth(app)
}

export { auth, firebaseDisabled }
