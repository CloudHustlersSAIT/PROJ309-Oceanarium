<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'

const router = useRouter()
const { user, loading, error, loginWithEmail, signupWithEmail, logout } = useAuth()

//Watch for changes in user authentication state (used so that logged in users are redirected to home)
watch(user, (newUser) => {
  if (newUser) {
    router.push('/home')
  }
})

const mode = ref('login') // "login" or "signup" (login is default)
const email = ref('') //User email input (empty by default)
const password = ref('') //User password input (empty by default)
const localError = ref(null) //Local error state for displaying errors
const submitting = ref(false) //Submission state to disable button while processing

//Function to handle form submission for login/signup
async function handleSubmit() {
  localError.value = null //Reset local error
  submitting.value = true //Set submitting state to true

  //Try to login or signup based on the current mode
  try {
    if (mode.value === 'login') {
      await loginWithEmail(email.value, password.value)
    } else {
      await signupWithEmail(email.value, password.value)
    }
    router.push('/home') //Navigate to home on success
  } catch (err) {
    // Prefer the error code instead of parsing the message
    const code = err.code || ''

    // Map error codes to user-friendly messages
    if (code === 'auth/user-not-found') {
      localError.value = 'No account found with this email.'
    } else if (code === 'auth/email-already-in-use') {
      localError.value = 'An account with this email already exists.'
    } else if (code === 'auth/invalid-email') {
      localError.value = 'Please enter a valid email address.'
    } else if (code === 'auth/invalid-credential' || code === 'auth/wrong-password') {
      localError.value = 'Incorrect email or password.'
    } else {
      // Fallback
      localError.value = 'An error occurred. Please try again.'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <!-- I am using some conditional rendering, refer to: https://vuejs.org/guide/essentials/conditional-->
  <div class="min-h-screen flex text-gray-500">
    <!-- Left side: video + logo -->
    <div class="relative hidden  md:block md:w-[35%] lg:w-[30%] overflow-hidden">
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
            {{ mode === 'login' ? 'Welcome back' : 'Create your account' }}
          </h1>
          <p class="text-sm text-neutral-400">
            {{
              mode === 'login'
                ? 'Sign in with your email and password.'
                : 'Sign up with your email and password.'
            }}
          </p>
        </header>

        <main>
          <p v-if="loading" class="text-sm text-neutral-400 mb-4">Checking auth status...</p>

          <div v-else class="space-y-4">
            <!-- Extra precaution, if user is logged in
             and somehow reached the login/signup page
              show their email and logout option.
             -->
            <p v-if="user" class="text-sm text-emerald-400">
              Logged in as <strong>{{ user.email }}</strong>
            </p>

            <form @submit.prevent="handleSubmit" class="space-y-4">
              <div class="space-y-2">
                <!--Label for Email-->
                <label class="block text-xl font-medium">Email</label>
                <div class="relative">
                  <!--Icon for User-->
                  <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <img
                      src="/src/assets/icons/user.svg"
                      class="h-8 w-8 text-gray-400"
                      alt="Email icon"
                    />
                  </div>
                  <!--Input field For Email-->
                  <input
                    v-model="email"
                    type="email"
                    required
                    class="w-full text-lg rounded-md border pl-12 px-4 py-5 text-base outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <label class="block text-xl font-medium">Password</label>
                <div class="relative">
                  <!--Icon for Lock-->
                  <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <img
                      src="/src/assets/icons/lock.svg"
                      class="h-8 w-8 text-gray-400"
                      alt="Email icon"
                    />
                  </div>
                  <!--Input field For Password-->
                  <input
                    v-model="password"
                    type="password"
                    required
                    class="w-full text-lg rounded-md border pl-12 px-4 py-5 text-base outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <!-- Button for submitting the form -->
              <button
                type="submit"
                :disabled="submitting"
                class="w-full rounded-md bg-[#0077B6] py-3 text-2xl font-medium text-white hover:bg-[#0097e7] disabled:opacity-60 disabled:cursor-not-allowed transition"
              >
                {{ submitting ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Sign up' }}
              </button>
            </form>

            <!-- Forgot password button-->
            <div>
              <button
                type="button"
                class="text-xs text-neutral-400 underline hover:text-neutral-200"
                @click="router.push('/forgot-password')"
              >
                Forgot password?
              </button>
            </div>

            <p
              v-if="localError"
              class="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2"
            >
              {{ localError }}
            </p>

            <p
              v-if="error && !localError"
              class="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2"
            >
              {{ error.message || error }}
            </p>

            <!-- Sign in or Sign up section -->
            <div class="flex items-center justify-between text-sm text-neutral-400">
              <span>
                {{ mode === 'login' ? "Don't have an account?" : 'Already have an account?' }}
              </span>
              <button
                type="button"
                class="font-medium text-[#00B4D8] hover:text-[#CAF0F8]"
                @click="mode = mode === 'login' ? 'signup' : 'login'"
              >
                {{ mode === 'login' ? 'Sign up' : 'Sign in' }}
              </button>
            </div>

            <div v-if="user" class="pt-2">
              <button
                type="button"
                class="text-xs text-neutral-400 underline hover:text-neutral-200"
                @click="logout"
              >
                Logout
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>
