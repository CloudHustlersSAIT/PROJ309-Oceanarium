<script setup>
const props = defineProps({
  label: {
    type: String,
    default: 'Save',
  },
  loadingLabel: {
    type: String,
    default: 'Saving...',
  },
  onSave: {
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
  loading: {
    type: Boolean,
    default: false,
  },
  buttonType: {
    type: String,
    default: 'button',
  },
})

const emit = defineEmits(['save'])

function handleSave(event) {
  if (props.disabled || props.loading) return

  emit('save', event)
  if (typeof props.onSave === 'function') {
    props.onSave(event)
  }
}
</script>

<template>
  <button
    :type="buttonType"
    :disabled="disabled || loading"
    :aria-label="ariaLabel || label"
    class="inline-flex items-center justify-center rounded-[7px] bg-[#0077B6] px-4 py-2 text-sm font-medium text-white transition-colors duration-150 hover:bg-[#0097E7] active:bg-[#00609A] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00B4D8]/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
    @click="handleSave"
  >
    {{ loading ? loadingLabel : label }}
  </button>
</template>
