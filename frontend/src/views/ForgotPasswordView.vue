<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'

const router = useRouter()
const { user, passwordResetWithEmail } = useAuth()

//Watch for changes in user authentication state (used so that logged in users are redirected to home)
watch(user, (newUser) => {
  if (newUser) {
    router.push('/home')
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
  <!-- I am using some conditional rendering, refer to: https://vuejs.org/guide/essentials/conditional-->
  <div class="min-h-screen flex bg-white text-gray-500">
    <!-- Left side: video + logo -->
    <div class="relative hidden md:block md:w-[35%] lg:w-[30%] overflow-hidden">
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

      <!-- Centered logo -->
      <div class="absolute inset-0 flex items-center justify-center">
        <img
          src="/src/assets/images/logo.svg"
          alt="Company logo"
          class="h-50 w-auto drop-shadow-lg"
        />
      </div>
    </div>

    <!-- Right side: auth form -->
    <div class="flex-1 flex items-center justify-center px-4 py-8">
      <div class="w-full max-w-md space-y-6">
        <header class="space-y-2">
          <h1 class="text-2xl font-semibold tracking-tight text-black">
            <img
              src="/src/assets/images/logo-text.svg"
              alt="Company logo"
              class="h-12 mb-4 w-auto drop-shadow-lg"
            />
            Forgot your password?
          </h1>
          <p class="text-gray-400">Enter your registered email.</p>
        </header>

        <!-- Form for email input and submission -->
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="space-y-4">
            <div class="relative">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <img
                  src="/src/assets/icons/envelope.svg"
                  class="h-8 w-8 text-gray-400"
                  alt="Email icon"
                />
              </div>

              <input
                v-model="email"
                type="email"
                required
                class="w-full text-lg rounded-md border pl-14 px-4 py-5 text-base outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full rounded-md bg-[#0077B6] py-3 text-xl font-medium text-white hover:bg-[#0097e7] disabled:opacity-60 disabled:cursor-not-allowed transition"
          >
            {{ submitting ? 'Sending...' : 'Send reset link' }}
          </button>
        </form>

        <!-- Success and error messages -->
        <p
          v-if="successMessage"
          class="text-sm text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2"
        >
          {{ successMessage }}
        </p>

        <p
          v-if="localError"
          class="text-sm text-red-500 bg-red-50 border border-red-200 rounded-md px-3 py-2"
        >
          {{ localError }}
        </p>

        <!-- Back to login button -->
        <button
          type="button"
          class="text-xs text-neutral-400 underline hover:text-neutral-600"
          @click="router.push('/login')"
        >
          Back to login
        </button>
      </div>
    </div>
  </div>
</template>
