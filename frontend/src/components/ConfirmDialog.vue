<script setup>
import CancelButton from './CancelButton.vue'
import SaveButton from './SaveButton.vue'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Confirm action',
  },
  message: {
    type: String,
    default: 'Do you want to proceed?',
  },
  confirmLabel: {
    type: String,
    default: 'Yes, proceed',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[60] bg-black/50 p-4 flex items-center justify-center"
    @click.self="emit('cancel')"
  >
    <div class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-5 shadow-xl">
      <h4 class="typo-modal-title">{{ title }}</h4>
      <p class="mt-2 typo-body">{{ message }}</p>
      <div class="mt-5 flex items-center justify-end gap-2">
        <CancelButton @cancel="emit('cancel')" />
        <SaveButton
          :label="confirmLabel"
          :loading="loading"
          :disabled="disabled"
          @save="emit('confirm')"
        />
      </div>
    </div>
  </div>
</template>