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
    localError.value = err.message || String(err)
  } finally {
    submitting.value = false
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
          <p>hi</p>
        </main>
      </div>
    </div>
  </div>
</template>
