// src/contexts/authContext.js
import { ref } from 'vue'
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { auth } from '../utils/firebase'

// Reactive references to hold auth state
const currentUser = ref(null)
const authLoading = ref(true)
const authError = ref(null)

// Listen for auth state changes
onAuthStateChanged(auth, (user) => {
  currentUser.value = user
  authLoading.value = false
})

/////////////////////////////////////////////////
//                                             //
// Helper functions for authentication actions //
//                                             //
/////////////////////////////////////////////////

// Login function
async function loginWithEmail(email, password) {
  authError.value = null
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
