<script setup>
import { useTheme } from '@/composables/useTheme'

const props = defineProps({
  iconOnly: {
    type: Boolean,
    default: false,
  },
})

const { isDark, toggleTheme } = useTheme()
</script>

<template>
  <button
    type="button"
    :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    :class="
      props.iconOnly
        ? 'inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-200 dark:hover:bg-white/5'
        : 'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-white/80 transition hover:bg-white/10 active:bg-white/15 active:scale-[0.98]'
    "
    @click="toggleTheme"
  >
    <span :class="props.iconOnly ? 'flex h-5 w-5 items-center justify-center' : 'flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10'">
      <!-- Sun icon — shown in dark mode (click to switch to light) -->
      <svg
        v-if="isDark"
        xmlns="http://www.w3.org/2000/svg"
        :class="props.iconOnly ? 'h-5 w-5' : 'h-4 w-4'"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="4" />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 2v2m0 16v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M2 12h2m16 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
        />
      </svg>
      <!-- Moon icon — shown in light mode (click to switch to dark) -->
      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        :class="props.iconOnly ? 'h-5 w-5' : 'h-4 w-4'"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"
        />
      </svg>
    </span>
    <span v-if="!props.iconOnly">{{ isDark ? 'Light mode' : 'Dark mode' }}</span>
  </button>
</template>
