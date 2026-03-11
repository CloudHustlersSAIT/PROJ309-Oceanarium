<script setup>
// Import necessary modules
import { useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const router = useRouter()


const pageTitle = 'Page under construction'
const pageDescription =
  "We're still working on this feature. Check back soon to see what's new at the Oceanarium!"
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main content -->
    <main class="flex-1 flex items-center justify-center px-6 py-10">
      <div
        class="max-w-2xl w-full bg-white rounded-3xl shadow-lg border border-[#CAF0F8] px-8 py-10 flex flex-col items-center text-center"
      >
        <!-- Image -->
        <div class="w-60 h-48 mb-6">
          <img
            src="/src/assets/images/construction.jpg"
            alt="Page under construction illustration"
            class="w-full h-full object-contain"
          />
        </div>

        <!-- Title -->
        <h1 class="text-2xl md:text-3xl font-semibold text-gray-800 mb-2">
          {{ pageTitle }}
        </h1>

        <!-- Subtitle -->
        <p class="text-sm md:text-base text-gray-500 mb-6">
          {{ pageDescription }}
        </p>

        <!-- Fun little ocean-themed line -->
        <p class="text-xs md:text-sm text-[#0077B6] font-medium mb-6">
          Our team is swimming as fast as they can to bring this experience to life. ðŸ¬
        </p>

        <!-- Actions -->
        <div class="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            class="px-5 py-2.5 rounded-full bg-[#0077B6] text-white text-sm font-medium hover:bg-[#0097e7] transition"
            @click="router.push('/home')"
          >
            Back to home
          </button>

          <button
            type="button"
            class="px-5 py-2.5 rounded-full border border-[#00B4D8] text-[#0077B6] text-sm font-medium bg-[#E0F7FF] hover:bg-[#CAF0F8] transition"
            @click="router.back()"
          >
            Go back
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

