<script setup>
const props = defineProps({
  label: {
    type: String,
    default: 'Cancel',
  },
  onCancel: {
    type: Function,
    default: null,
  },
  ariaLabel: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['cancel'])

function handleCancel(event) {
  if (props.disabled) return

  emit('cancel', event)
  if (typeof props.onCancel === 'function') {
    props.onCancel(event)
  }
}
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    :aria-label="ariaLabel || label"
    class="inline-flex items-center justify-center rounded-[7px] border border-slate-200 bg-transparent px-4 py-2 text-sm font-medium text-slate-600 transition-colors duration-150 hover:border-slate-400 hover:bg-slate-100 active:bg-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:border-white/15 dark:text-slate-300 dark:hover:border-white/25 dark:hover:bg-white/5 dark:active:bg-white/10 dark:focus-visible:ring-offset-surface-card disabled:cursor-not-allowed disabled:opacity-60"
    @click="handleCancel"
  >
    {{ label }}
  </button>
</template>
