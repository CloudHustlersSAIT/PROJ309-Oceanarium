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
    class="inline-flex items-center justify-center rounded-[7px] border border-[#CBD5E1] bg-transparent px-4 py-2 text-sm font-medium text-[#475569] transition-colors duration-150 hover:border-[#94A3B8] hover:bg-[#F1F5F9] active:bg-[#E2E8F0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#94A3B8]/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
    @click="handleCancel"
  >
    {{ label }}
  </button>
</template>
