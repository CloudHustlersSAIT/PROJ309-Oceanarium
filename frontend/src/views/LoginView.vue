<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'

const router = useRouter()
const { user, loading, error, loginWithEmail, signupWithEmail, logout } = useAuth()

const mode = ref('login') // "login" or "signup"
const email = ref('') //
const password = ref('')
const localError = ref(null)
const submitting = ref(false)

async function handleSubmit() {
  localError.value = null
  submitting.value = true
  try {
    if (mode.value === 'login') {
      await loginWithEmail(email.value, password.value)
    } else {
      await signupWithEmail(email.value, password.value)
    }
    router.push('/home')
  } catch (err) {
    localError.value = err.message || String(err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
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
          <p v-if="loading" class="text-sm text-neutral-400 mb-4">Checking auth status...</p>

          <div v-else class="space-y-4">
            <p v-if="user" class="text-sm text-emerald-400">
              Logged in as <strong>{{ user.email }}</strong>
            </p>

            <form @submit.prevent="handleSubmit" class="space-y-4">
              <div class="space-y-2">
                <label class="block text-sm font-medium">Email</label>
                <input
                  v-model="email"
                  type="email"
                  required
                  class="w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  placeholder="you@example.com"
                />
              </div>

              <div class="space-y-2">
                <label class="block text-sm font-medium">Password</label>
                <input
                  v-model="password"
                  type="password"
                  required
                  class="w-full rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                :disabled="submitting"
                class="w-full rounded-md bg-emerald-500 py-2 text-sm font-medium text-neutral-950 hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed transition"
              >
                {{ submitting ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Sign up' }}
              </button>
            </form>

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

            <div class="flex items-center justify-between text-sm text-neutral-400">
              <span>
                {{ mode === 'login' ? "Don't have an account?" : 'Already have an account?' }}
              </span>
              <button
                type="button"
                class="font-medium text-emerald-400 hover:text-emerald-300"
                @click="mode = mode === 'login' ? 'signup' : 'login'"
              >
                {{ mode === 'login' ? 'Sign up' : 'Log in' }}
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
