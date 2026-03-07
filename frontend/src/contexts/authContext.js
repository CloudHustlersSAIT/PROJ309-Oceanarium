// src/contexts/authContext.js
import { ref } from 'vue'
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { auth, firebaseDisabled } from '../utils/firebase'

// Reactive references to hold auth state
const currentUser = ref(null)
const authLoading = ref(true)
const authError = ref(null)

// If Firebase is configured, listen for auth state changes.
// Otherwise keep user null and set loading=false so the app can render.
if (!firebaseDisabled && auth) {
  onAuthStateChanged(auth, (user) => {
    currentUser.value = user
    authLoading.value = false
  })
} else {
  currentUser.value = null
  authLoading.value = false
}

/////////////////////////////////////////////////
//                                             //
// Helper functions for authentication actions //
//                                             //
/////////////////////////////////////////////////

// Login function
async function loginWithEmail(email, password) {
  authError.value = null
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot perform login.')
    authError.value = err
    throw err
  }
  try {
    const cred = await signInWithEmailAndPassword(auth, email, password)
    return cred.user
  } catch (err) {
    authError.value = err
    throw err
  }
}

// Signup function
async function signupWithEmail(email, password) {
  authError.value = null
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot create account.')
    authError.value = err
    throw err
  }
  try {
    const cred = await createUserWithEmailAndPassword(auth, email, password)
    return cred.user
  } catch (err) {
    authError.value = err
    throw err
  }
}

// Logout function
async function logout() {
  authError.value = null
  if (!auth) {
    const err = new Error('Firebase is not configured. Cannot logout.')
    authError.value = err
    throw err
  }
  try {
    await signOut(auth)
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

// Composable-style function to use in components
export function useAuth() {
  return {
    user: currentUser,
    loading: authLoading,
    error: authError,
    loginWithEmail,
    signupWithEmail,
    logout,
    passwordResetWithEmail,
  }
}

