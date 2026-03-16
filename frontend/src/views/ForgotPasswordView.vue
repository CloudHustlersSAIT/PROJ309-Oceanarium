<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { getDefaultRouteForRole } from '../services/authService'

const router = useRouter()
const { role, passwordResetWithEmail } = useAuth()

//Watch for changes in user authentication state (used so that logged in users are redirected to home)
watch(role, (newRole) => {
  if (newRole) {
    router.push(getDefaultRouteForRole(newRole))
  }
})

const email = ref('') //User email input (empty by default)
const localError = ref(null) //Local error state for displaying errors
const submitting = ref(false) //Submission state to disable button while processing
const successMessage = ref('') //Success message state

//Function to handle form submission for login/signup
async function handleSubmit() {
  localError.value = null //Reset local error
  submitting.value = true //Set submitting state to true
  successMessage.value = '' //Reset success message

  //Attempt to send password reset email
  try {
    //Call password reset function from auth context
    await passwordResetWithEmail(email.value)
    successMessage.value = 'Password reset email sent. Please check your inbox.'
  } catch (error) {
    localError.value = error.message //Set local error message
  } finally {
    submitting.value = false //Reset submitting state
  }
}
</script>

<template>
  <div class="fixed inset-0 overflow-hidden bg-white text-black dark:bg-[#0F1117] dark:text-slate-100">
    <div class="h-full grid grid-cols-1 md:grid-cols-[35%_1fr] lg:grid-cols-[30%_1fr]">
      <!-- Left media panel -->
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

      <!-- Right form panel -->
      <main class="flex items-center justify-center px-4 py-3 md:py-4 overflow-hidden">
        <div class="w-full max-w-[500px]">
          <div
            class="min-h-[620px] rounded-none border border-black/5 bg-white p-6 shadow-xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40 sm:p-7"
          >
            <header class="mb-5">
              <img
                src="/images/logo-text.svg"
                alt="Oceanarium"
                class="h-7 sm:h-8 w-auto mb-3"
              />
              <h1 class="text-3xl sm:text-3xl font-bold leading-[1.15] tracking-tight text-black dark:text-slate-100">
                Forgot your password?
              </h1>
              <p class="mt-1.5 text-sm text-black/70 dark:text-slate-400">
                Enter your registered email to receive a reset link.
              </p>
            </header>

            <form class="space-y-4" @submit.prevent="handleSubmit">
              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-black dark:text-slate-100">Email address</label>
                <div class="relative">
                  <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                    <img
                      src="/src/assets/icons/envelope.svg"
                      class="h-5 w-5 opacity-70"
                      alt="Email icon"
                    />
                  </div>
                  <input
                    v-model="email"
                    type="email"
                    required
                    class="w-full rounded-2xl border border-black/15 bg-white py-2.5 pl-12 pr-4 text-sm text-black placeholder:text-black/45 outline-none focus:border-[#0077B6] focus:ring-2 focus:ring-[#0077B6]/20 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-sky-800/50"
                    placeholder="you@example.com"
                    autocomplete="email"
                  />
                </div>
              </div>

              <button
                type="submit"
                :disabled="submitting"
                class="w-full rounded-2xl bg-[#0077B6] py-3.5 text-base font-bold text-white shadow-md hover:bg-[#0097E7] hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed transition focus:outline-none focus:ring-2 focus:ring-[#0077B6]/30"
              >
                {{ submitting ? 'Sending...' : 'Send reset link' }}
              </button>

              <p
                v-if="successMessage"
                class="rounded-2xl border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300"
              >
                {{ successMessage }}
              </p>

              <p
                v-if="localError"
                class="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-800 dark:bg-red-950/50 dark:text-red-300"
              >
                {{ localError }}
              </p>

              <button
                type="button"
                class="w-full rounded-2xl border border-[#0077B6]/35 bg-white py-2.5 text-sm font-semibold text-[#0077B6] transition hover:bg-[#0077B6]/10 focus:outline-none focus:ring-2 focus:ring-[#0077B6]/25 dark:border-sky-700/40 dark:bg-[#1C2333] dark:text-sky-300 dark:hover:bg-sky-950/50 dark:focus:ring-sky-800/50"
                @click="router.push('/login')"
              >
                Back to login
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
