// src/contexts/authContext.js
import { ref } from "vue";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import { auth } from "../utils/firebase";

// Global reactive state (shared across components)
const currentUser = ref(null);
const authLoading = ref(true);
const authError = ref(null);

// Set up the auth state listener once (when this module is imported)
onAuthStateChanged(auth, (user) => {
  currentUser.value = user;
  authLoading.value = false;
});

// Simple helpers

async function loginWithEmail(email, password) {
  authError.value = null;
  try {
    const cred = await signInWithEmailAndPassword(auth, email, password);
    return cred.user;
  } catch (err) {
    authError.value = err;
    throw err;
  }
}

async function signupWithEmail(email, password) {
  authError.value = null;
  try {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    return cred.user;
  } catch (err) {
    authError.value = err;
    throw err;
  }
}

async function logout() {
  authError.value = null;
  try {
    await signOut(auth);
  } catch (err) {
    authError.value = err;
    throw err;
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
  };
}
