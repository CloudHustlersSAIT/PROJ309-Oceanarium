<script setup>
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  to: { type: String, required: true },
  icon: { type: String, required: true },
  badge: { type: Number, default: 0 },
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
    :class="isActive ? 'bg-white/25 shadow-sm dark:bg-white/12' : 'bg-white/5 dark:bg-white/4'"
    @click="go"
  >
    <div class="relative flex items-center justify-center h-8 w-8 rounded-full bg-white/10">
      <img :src="icon" alt="" class="h-5 w-5 brightness-0 invert" />
      <span
        v-if="badge > 0"
        class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold leading-none text-white shadow-sm"
      >
        {{ badge > 99 ? '99+' : badge }}
      </span>
    </div>

    <span class="truncate">
      {{ label }}
    </span>
  </button>
</template>
