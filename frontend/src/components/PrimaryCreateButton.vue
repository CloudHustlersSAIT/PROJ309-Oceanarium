<script setup>
const props = defineProps({
  label: {
    type: String,
    default: '+ Create',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  ariaLabel: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['create'])

function handleCreate(event) {
  if (props.disabled) return
  emit('create', event)
}
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    :aria-label="ariaLabel || label"
    class="px-3 py-1.5 rounded bg-blue-600 text-white border border-blue-600 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
    @click="handleCreate"
  >
    {{ label }}
  </button>
</template>