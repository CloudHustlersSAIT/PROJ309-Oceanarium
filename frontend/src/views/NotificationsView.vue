<script setup>
import { useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const router = useRouter()

const pageTitle = 'Page under construction'
const pageDescription =
  "We're still working on this feature. Check back soon to see what's new at the Oceanarium!"
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <Sidebar />

    <main class="flex flex-1 items-center justify-center px-6 py-10">
      <div
        class="flex w-full max-w-2xl flex-col items-center rounded-3xl border border-[#CAF0F8] bg-white px-8 py-10 text-center shadow-lg"
      >
        <div class="mb-6 h-48 w-60">
          <img
            src="/src/assets/images/construction.jpg"
            alt="Page under construction illustration"
            class="h-full w-full object-contain"
          />
        </div>

        <h1 class="mb-2 text-2xl font-semibold text-gray-800 md:text-3xl">
          {{ pageTitle }}
        </h1>

        <p class="mb-6 text-sm text-gray-500 md:text-base">
          {{ pageDescription }}
        </p>

        <p class="mb-6 text-xs font-medium text-[#0077B6] md:text-sm">
          Our team is swimming as fast as they can to bring this experience to life.
        </p>

        <div class="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            class="rounded-full bg-[#0077B6] px-5 py-2.5 text-sm font-medium text-white transition hover:bg-[#0097e7]"
            @click="router.push('/home')"
          >
            Back to home
          </button>

          <button
            type="button"
            class="rounded-full border border-[#00B4D8] bg-[#E0F7FF] px-5 py-2.5 text-sm font-medium text-[#0077B6] transition hover:bg-[#CAF0F8]"
            @click="router.back()"
          >
            Go back
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
