<template>
  <div class="min-h-screen bg-[#F5F7FA] text-[#1C1C1C]">
    <GuideTopbar />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import GuideTopbar from '@/components/guide/GuideTopbar.vue'
</script>
