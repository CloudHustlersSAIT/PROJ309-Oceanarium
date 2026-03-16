<template>
  <div class="fixed inset-0 overflow-hidden bg-white text-black dark:bg-[#0F1117] dark:text-slate-100">
    <div class="h-full grid grid-cols-1 md:grid-cols-[35%_1fr] lg:grid-cols-[30%_1fr]">
      <aside class="relative hidden md:block overflow-hidden">
        <video
          autoplay
          muted
          loop
          playsinline
          class="h-full w-full object-cover"
          src="/videos/Oceanarium_clip2.mp4"
        >
          Your browser does not support the video tag.
        </video>

        <div class="absolute inset-0 bg-black/25"></div>

        <div class="absolute inset-0 flex items-center justify-center">
          <img
            src="/images/logo.svg"
            alt="Oceanarium logo"
            class="h-40 lg:h-44 w-auto drop-shadow-xl"
          />
        </div>
      </aside>

      <main class="flex items-center justify-center px-4 py-3 md:py-4 overflow-hidden">
        <div class="w-full max-w-[620px]">
          <div class="min-h-[620px] rounded-none border border-black/5 bg-white p-6 shadow-xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40 sm:p-7">
            <header class="mb-5">
              <img
                src="/images/logo-text.svg"
                alt="Oceanarium"
                class="h-7 sm:h-8 w-auto mb-3"
              />

              <h1 class="text-3xl sm:text-3xl font-bold leading-[1.15] tracking-tight text-black dark:text-slate-100">
                Welcome back
              </h1>

              <p class="mt-1.5 text-sm text-black/70 dark:text-slate-400">
                Sign in with your team-managed Oceanarium account.
              </p>
            </header>

            <section
              v-if="firebaseDisabled"
              class="mb-6 rounded-2xl border border-yellow-700/30 bg-yellow-50 p-5 dark:border-yellow-800 dark:bg-yellow-950/45"
            >
              <p class="text-sm text-yellow-900 dark:text-yellow-200">
                <strong>Authentication unavailable:</strong> Firebase is not configured.
              </p>
              <p class="mt-4 text-sm text-black/70 dark:text-slate-400">
                Public signup and client-side role selection are disabled. Configure Firebase to continue.
              </p>
            </section>

            <p v-if="loading" class="mb-4 text-sm text-black/70 dark:text-slate-400">Checking auth status...</p>

            <form v-else-if="!firebaseDisabled" class="space-y-4" @submit.prevent="handleSubmit">
              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-black dark:text-slate-100">Email address</label>
                <input
                  v-model="email"
                  type="email"
                  required
                  class="w-full rounded-2xl border border-black/15 bg-white px-4 py-2.5 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                  placeholder="you@example.com"
                  autocomplete="email"
                />
              </div>

              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-black dark:text-slate-100">Password</label>

                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    class="w-full rounded-2xl border border-black/15 bg-white px-4 py-2.5 pr-12 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                    placeholder="Password"
                    autocomplete="current-password"
                  />

                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-2xl text-black/60 transition hover:text-black focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 dark:text-slate-400 dark:hover:text-slate-100 dark:focus:ring-sky-800/50"
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
              </div>

              <button type="submit" :disabled="submitting" :class="primaryCtaClass">
                {{ submitting ? 'Please wait...' : 'Sign in' }}
              </button>

              <div class="text-center">
                <button
                  type="button"
                  class="rounded-md px-1 text-sm font-medium text-[#0077B6] underline underline-offset-2 hover:text-[#005a8a] focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 dark:text-sky-300 dark:hover:text-sky-200 dark:focus:ring-sky-800/50"
                  @click="router.push('/forgot-password')"
                >
                  Forgot password?
                </button>
              </div>

              <p
                v-if="localError"
                class="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-800 dark:bg-red-950/50 dark:text-red-300"
              >
                {{ localError }}
              </p>

              <p
                v-else-if="error"
                class="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-800 dark:bg-red-950/50 dark:text-red-300"
              >
                {{ error.message || error }}
              </p>

              <p class="pt-0.5 text-center text-xs text-black/50 dark:text-slate-500">
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
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { firebaseDisabled } from '../utils/firebase'
import { getDefaultRouteForRole } from '../services/authService'

const router = useRouter()
const { role, loading, error, loginWithEmail } = useAuth()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const localError = ref(null)
const submitting = ref(false)
const primaryCtaClass =
  'w-full rounded-2xl bg-[#0077B6] py-3.5 text-base font-bold text-white shadow-md hover:bg-[#0097E7] hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/30'

watch(role, (newRole) => {
  if (newRole) {
    router.push(getDefaultRouteForRole(newRole))
  }
})

async function handleSubmit() {
  localError.value = null
  submitting.value = true

  try {
    await loginWithEmail(email.value, password.value)
  } catch (err) {
    const code = err?.code || ''
    const message = String(err?.message || '')

    if (code === 'auth/user-not-found')
      localError.value = 'No account found with this email.'
    else if (code === 'auth/invalid-email') localError.value = 'Please enter a valid email address.'
    else if (code === 'auth/invalid-credential' || code === 'auth/wrong-password')
      localError.value = 'Incorrect email or password.'
    else if (err?.status === 403 || message.toLowerCase().includes('not mapped'))
      localError.value = 'This Firebase account is not assigned to an Oceanarium role in the backend.'
    else localError.value = 'An error occurred. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
