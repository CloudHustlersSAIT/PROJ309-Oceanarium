<template>
  <div class="fixed inset-0 overflow-hidden bg-white text-black">
    <div class="h-full grid grid-cols-1 md:grid-cols-[35%_1fr] lg:grid-cols-[30%_1fr]">
      <!-- Left media panel -->
      <aside class="relative hidden md:block overflow-hidden">
        <video
          autoplay
          muted
          loop
          playsinline
          class="h-full w-full object-cover"
          src="/src/assets/videos/Oceanarium_clip2.mp4"
        >
          Your browser does not support the video tag.
        </video>

        <div class="absolute inset-0 bg-black/25"></div>

        <div class="absolute inset-0 flex items-center justify-center">
          <img
            src="/src/assets/images/logo.svg"
            alt="Oceanarium logo"
            class="h-40 lg:h-44 w-auto drop-shadow-xl"
          />
        </div>
      </aside>

      <!-- Right form panel -->
      <main class="flex items-center justify-center px-4 py-3 md:py-4 overflow-hidden">
        <div class="w-full max-w-[620px]">
          <!-- Card -->
          <div
            class="bg-white shadow-xl rounded-none border border-black/5 p-6 sm:p-7 min-h-[620px]"
          >
            <!-- Header -->
            <header class="mb-5">
              <img
                src="/src/assets/images/logo-text.svg"
                alt="Oceanarium"
                class="h-7 sm:h-8 w-auto mb-3"
              />

              <!-- Better hierarchy (smaller + consistent) -->
              <h1 class="text-3xl sm:text-3xl font-bold leading-[1.15] tracking-tight text-black">
                {{ mode === 'signup' ? 'Create an account' : 'Welcome back' }}
              </h1>

              <p class="mt-1.5 text-sm text-black/70">
                {{ mode === 'signup' ? 'Already have an account?' : "Don't have an account?" }}
                <button
                  type="button"
                  class="ml-1 font-semibold text-[#0077B6] hover:text-[#005a8a] underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 rounded-md px-3 py-1.5"
                  @click="switchMode"
                >
                  {{ mode === 'signup' ? 'Log in' : 'Sign up' }}
                </button>
              </p>
            </header>

            <!-- Dev mode notice -->
            <section
              v-if="firebaseDisabled"
              class="mb-6 rounded-2xl border border-yellow-700/30 bg-yellow-50 p-5"
            >
              <p class="text-sm text-yellow-900">
                <strong>Development Mode:</strong> Firebase is not configured.
              </p>

              <div class="mt-4">
                <p class="text-sm text-black/70 mb-2">Continue as</p>

                <!-- Role segmented control -->
                <div class="rounded-2xl border border-black/15 bg-black/[0.02] p-1 flex gap-1">
                  <button
                    type="button"
                    class="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25"
                    :class="
                      selectedRole === 'admin'
                        ? 'bg-white text-[#0077B6] shadow-sm'
                        : 'text-black/70 hover:bg-white/70'
                    "
                    @click="selectedRole = 'admin'"
                  >
                    Admin
                  </button>

                  <button
                    type="button"
                    class="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25"
                    :class="
                      selectedRole === 'guide'
                        ? 'bg-white text-[#0077B6] shadow-sm'
                        : 'text-black/70 hover:bg-white/70'
                    "
                    @click="selectedRole = 'guide'"
                  >
                    Guide
                  </button>
                </div>
              </div>

              <button
                type="button"
                class="mt-4 w-full rounded-2xl bg-[#0077B6] py-3.5 text-base font-semibold text-white hover:bg-[#0097E7] transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/30"
                @click="continueDev"
              >
                Continue
              </button>
            </section>

            <!-- Loading -->
            <p v-if="loading" class="text-sm text-black/70 mb-4">Checking auth status...</p>

            <!-- Form -->
            <form v-else-if="!firebaseDisabled" class="space-y-4" @submit.prevent="handleSubmit">
              <!-- Name row (signup only) -->
              <div v-if="mode === 'signup'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-black">First name</label>
                  <input
                    v-model="firstName"
                    type="text"
                    class="w-full rounded-2xl border border-black/15 px-4 py-2.5 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
                    placeholder="John"
                    autocomplete="given-name"
                  />
                </div>

                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-black">Last name</label>
                  <input
                    v-model="lastName"
                    type="text"
                    class="w-full rounded-2xl border border-black/15 px-4 py-2.5 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
                    placeholder="Doe"
                    autocomplete="family-name"
                  />
                </div>
              </div>

              <!-- Email -->
              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-black">Email address</label>
                <input
                  v-model="email"
                  type="email"
                  required
                  class="w-full rounded-2xl border border-black/15 px-4 py-2.5 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
                  placeholder="you@example.com"
                  autocomplete="email"
                />
              </div>

              <!-- Password -->
              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-black">Password</label>

                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    class="w-full rounded-2xl border border-black/15 px-4 py-2.5 pr-12 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20"
                    placeholder="Password"
                    :autocomplete="mode === 'signup' ? 'new-password' : 'current-password'"
                  />

                  <!-- cleaner icon button -->
                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 flex items-center justify-center w-12 text-black/60 hover:text-black transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 rounded-r-2xl"
                    aria-label="Toggle password visibility"
                    @mousedown.prevent="showPassword = true"
                    @mouseup="showPassword = false"
                    @mouseleave="showPassword = false"
                    @touchstart.prevent="showPassword = true"
                    @touchend="showPassword = false"
                    @touchcancel="showPassword = false"
                    @keydown.space.prevent="showPassword = true"
                    @keyup.space="showPassword = false"
                    @keydown.enter.prevent="showPassword = true"
                    @keyup.enter="showPassword = false"
                    @blur="showPassword = false"
                  >
                    <svg
                      v-if="!showPassword"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      class="h-5 w-5"
                      aria-hidden="true"
                    >
                      <path
                        d="M12 5c-7 0-10 7-10 7s3 7 10 7 10-7 10-7-3-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Z"
                      />
                      <path d="M12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z" />
                    </svg>

                    <svg
                      v-else
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      class="h-5 w-5"
                      aria-hidden="true"
                    >
                      <path
                        d="M3.28 2.22a.75.75 0 0 0-1.06 1.06l2.02 2.02C2.7 6.5 1.99 7.63 1.65 8.3a.75.75 0 0 0 0 .7C2.15 10 5 16 12 16c1.42 0 2.69-.25 3.8-.65l2.92 2.92a.75.75 0 1 0 1.06-1.06L3.28 2.22ZM12 14.5c-4.95 0-7.4-4.17-8.3-5.5.43-.74 1.2-1.8 2.36-2.73l1.61 1.61A5 5 0 0 0 15.1 15l-1.04-1.04c-.65.34-1.38.54-2.06.54Zm9.35-5.85c-.5 1-1.71 3.1-3.85 4.45l-1.1-1.1A5 5 0 0 0 10 5.75l-1.1-1.1C9.9 4.23 10.92 4 12 4c7 0 9.85 6 10.35 7.35a.75.75 0 0 1 0 .3Z"
                      />
                    </svg>
                  </button>
                </div>

                <!-- Password rules (signup only) -->
                <div v-if="mode === 'signup'" class="mt-2 text-xs space-y-1 text-black/70">
                  <div
                    class="flex items-center gap-2"
                    :class="
                      hasMinLen ? 'text-emerald-700 font-medium' : 'text-black/70 font-normal'
                    "
                  >
                    <span class="inline-flex h-4 w-4 items-center justify-center text-xs font-bold">
                      {{ hasMinLen ? '✓' : '•' }}
                    </span>
                    <span>At least 8 characters</span>
                  </div>
                  <div
                    class="flex items-center gap-2"
                    :class="
                      hasSpecial ? 'text-emerald-700 font-medium' : 'text-black/70 font-normal'
                    "
                  >
                    <span class="inline-flex h-4 w-4 items-center justify-center text-xs font-bold">
                      {{ hasSpecial ? '✓' : '•' }}
                    </span>
                    <span>At least 1 special character</span>
                  </div>
                </div>
              </div>

              <!-- Login as -->
              <div class="space-y-2">
                <label class="text-sm font-semibold text-black">Login as</label>

                <!-- segmented toggle (fixes "disabled" look) -->
                <div class="rounded-2xl border border-black/15 bg-black/[0.02] p-1 flex gap-1">
                  <button
                    type="button"
                    class="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25"
                    :class="
                      selectedRole === 'admin'
                        ? 'bg-white text-[#0077B6] shadow-sm'
                        : 'text-black/70 hover:bg-white/70'
                    "
                    @click="selectedRole = 'admin'"
                  >
                    Admin
                  </button>

                  <button
                    type="button"
                    class="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25"
                    :class="
                      selectedRole === 'guide'
                        ? 'bg-white text-[#0077B6] shadow-sm'
                        : 'text-black/70 hover:bg-white/70'
                    "
                    @click="selectedRole = 'guide'"
                  >
                    Guide
                  </button>
                </div>
              </div>

              <!-- Primary submit (less tall) -->
              <button
                type="submit"
                :disabled="submitting || (mode === 'signup' && !passwordIsValid)"
                :class="primaryCtaClass"
              >
                {{
                  submitting ? 'Please wait...' : mode === 'signup' ? 'Create account' : 'Sign in'
                }}
              </button>

              <!-- Forgot password -->
              <div v-if="mode === 'login'" class="text-center">
                <button
                  type="button"
                  class="text-sm font-medium text-[#0077B6] underline underline-offset-2 hover:text-[#005a8a] focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 rounded-md px-1"
                  @click="router.push('/forgot-password')"
                >
                  Forgot password?
                </button>
              </div>

              <!-- Divider -->
              <div v-if="mode === 'login'" class="flex items-center gap-3 pt-0.5">
                <div class="h-px flex-1 bg-black/10"></div>
                <span class="text-xs font-semibold tracking-wide text-black/45 uppercase">or</span>
                <div class="h-px flex-1 bg-black/10"></div>
              </div>

              <!-- Google button (less tall + consistent) -->
              <button
                v-if="mode === 'login'"
                type="button"
                class="w-full rounded-2xl border border-[#0077B6]/35 bg-[#EAF6FD] py-2.5 text-sm font-semibold text-[#005A8A] hover:bg-[#D8EEFB] transition flex items-center justify-center gap-3 focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="submittingGoogle"
                @click="handleGoogleSignIn"
              >
                <span class="inline-flex items-center justify-center h-5 w-5">
                  <svg viewBox="0 0 48 48" class="h-5 w-5" aria-hidden="true">
                    <path
                      fill="#EA4335"
                      d="M24 9.5c3.54 0 6.31 1.53 7.76 2.81l5.66-5.66C33.98 3.64 29.47 1.5 24 1.5 14.73 1.5 6.79 6.82 3.06 14.56l6.89 5.35C11.66 14.05 17.35 9.5 24 9.5z"
                    />
                    <path
                      fill="#4285F4"
                      d="M46.5 24.5c0-1.64-.15-3.21-.43-4.73H24v9.01h12.64c-.55 2.95-2.21 5.45-4.7 7.13l7.25 5.63C43.66 37.43 46.5 31.52 46.5 24.5z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M9.95 28.91c-.48-1.43-.75-2.95-.75-4.41s.27-2.98.75-4.41l-6.89-5.35C1.74 17.57 1 20.97 1 24.5s.74 6.93 2.06 9.76l6.89-5.35z"
                    />
                    <path
                      fill="#34A853"
                      d="M24 47.5c5.47 0 10.06-1.81 13.41-4.93l-7.25-5.63c-2.01 1.35-4.59 2.14-6.16 2.14-6.65 0-12.34-4.55-14.05-10.41l-6.89 5.35C6.79 42.18 14.73 47.5 24 47.5z"
                    />
                  </svg>
                </span>
                <span>{{ submittingGoogle ? 'Connecting...' : 'Continue with Google' }}</span>
              </button>

              <!-- Errors -->
              <p
                v-if="localError"
                class="text-sm text-red-900 bg-red-50 border border-red-300 rounded-2xl px-4 py-3"
              >
                {{ localError }}
              </p>

              <p
                v-else-if="error"
                class="text-sm text-red-900 bg-red-50 border border-red-300 rounded-2xl px-4 py-3"
              >
                {{ error.message || error }}
              </p>

              <!-- Small disclaimer (optional, but looks pro) -->
              <p class="text-xs text-black/50 text-center pt-0.5">
                By continuing, you agree to Oceanarium's terms and privacy policy.
              </p>
            </form>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { firebaseDisabled, auth } from '../utils/firebase'

// Google sign-in (Firebase)
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth'

const router = useRouter()
const { user, loading, error, loginWithEmail, signupWithEmail } = useAuth()

const mode = ref('login')
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const password = ref('')
const showPassword = ref(false)

const selectedRole = ref('admin') // admin | guide
const localError = ref(null)
const submitting = ref(false)
const submittingGoogle = ref(false)
const primaryCtaClass =
  'w-full rounded-2xl bg-[#0077B6] py-3.5 text-base font-bold text-white shadow-md hover:bg-[#0097E7] hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/30'

// Password rules for signup
const hasMinLen = computed(() => password.value.length >= 8)
const hasSpecial = computed(() => /[^A-Za-z0-9]/.test(password.value))
const passwordIsValid = computed(() => hasMinLen.value && hasSpecial.value)

function switchMode() {
  mode.value = mode.value === 'login' ? 'signup' : 'login'
  localError.value = null
  password.value = ''
  showPassword.value = false
}

watch(user, (newUser) => {
  if (newUser) {
    const role = localStorage.getItem('role') || selectedRole.value || 'admin'
    router.push(role === 'guide' ? '/guide/home' : '/home')
  }
})

function continueDev() {
  localStorage.setItem('role', selectedRole.value)
  router.push(selectedRole.value === 'guide' ? '/guide/home' : '/home')
}

function validateForSignup() {
  if (mode.value !== 'signup') return true

  if (!passwordIsValid.value) {
    localError.value =
      'Password must be at least 8 characters and include at least 1 special character.'
    return false
  }

  return true
}

async function handleSubmit() {
  localError.value = null

  if (!validateForSignup()) return

  submitting.value = true
  try {
    if (mode.value === 'login') {
      await loginWithEmail(email.value, password.value)
    } else {
      await signupWithEmail(email.value, password.value)
    }

    localStorage.setItem('role', selectedRole.value)
    router.push(selectedRole.value === 'guide' ? '/guide/home' : '/home')
  } catch (err) {
    const code = err?.code || ''

    if (code === 'auth/user-not-found') localError.value = 'No account found with this email.'
    else if (code === 'auth/email-already-in-use')
      localError.value = 'An account with this email already exists.'
    else if (code === 'auth/invalid-email') localError.value = 'Please enter a valid email address.'
    else if (code === 'auth/weak-password')
      localError.value = 'Password is too weak. Please use a stronger password.'
    else if (code === 'auth/invalid-credential' || code === 'auth/wrong-password')
      localError.value = 'Incorrect email or password.'
    else localError.value = 'An error occurred. Please try again.'
  } finally {
    submitting.value = false
  }
}

async function handleGoogleSignIn() {
  localError.value = null

  if (firebaseDisabled || !auth) {
    localError.value = 'Google sign-in is unavailable because Firebase is not configured.'
    return
  }

  submittingGoogle.value = true
  try {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)

    localStorage.setItem('role', selectedRole.value)
    router.push(selectedRole.value === 'guide' ? '/guide/home' : '/home')
  } catch (err) {
    const code = err?.code || ''
    if (code === 'auth/popup-closed-by-user')
      localError.value = 'Google sign-in was closed before finishing.'
    else if (code === 'auth/operation-not-allowed')
      localError.value = 'Google sign-in is not enabled in Firebase Console.'
    else localError.value = 'Google sign-in failed. Please try again.'
  } finally {
    submittingGoogle.value = false
  }
}
</script>
