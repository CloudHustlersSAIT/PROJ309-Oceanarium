<script setup>
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  to: { type: String, required: true }, // route name or path
  icon: { type: String, required: true }, // icon path
})

const router = useRouter()
const route = useRoute()

// Check if the current button represents the active page.
const isActive = computed(() => {
  // If "to" is a route name
  if (router.hasRoute(props.to)) {
    return route.name === props.to
  }

  // If "to" is a path.
  return route.path === props.to
})

function go() {
  if (router.hasRoute(props.to)) {
    router.push({ name: props.to })
  } else {
    router.push(props.to)
  }
}
</script>

<template>
  <button
    type="button"
    class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition hover:bg-white/15 active:scale-[0.98]"
    :class="isActive ? 'bg-white/25 shadow-sm' : 'bg-white/5'"
    @click="go"
  >
    <!-- Icon -->
    <div class="flex items-center justify-center h-8 w-8 rounded-full bg-white/10">
      <img :src="icon" alt="" class="h-5 w-5" />
    </div>

    <!-- Label -->
    <span class="truncate">
      {{ label }}
    </span>
  </button>
</template>
