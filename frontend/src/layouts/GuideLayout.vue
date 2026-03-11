<template>
  <div class="min-h-screen bg-[#F5F7FA] text-[#1C1C1C]">
    <div class="w-full md:flex">
      <GuideSidebar />
      <main class="w-full px-4 pt-20 pb-6 sm:px-6 md:pt-6 lg:px-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import GuideSidebar from "@/components/guide/GuideSidebar.vue";
</script>
