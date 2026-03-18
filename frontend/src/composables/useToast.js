/**
 * useToast — singleton composable for global toast notifications.
 *
 * Module-level refs ensure all component instances share the same queue.
 */
import { ref } from 'vue'

const MAX_TOASTS = 5

let _nextId = 0
const toasts = ref([])
const _timers = new Map()

function addToast(message, { type = 'info', duration = 5000 } = {}) {
  const id = ++_nextId

  if (toasts.value.length >= MAX_TOASTS) {
    const oldest = toasts.value[0]
    removeToast(oldest.id)
  }

  toasts.value.push({ id, message, type, duration })

  if (duration > 0) {
    const timer = setTimeout(() => removeToast(id), duration)
    _timers.set(id, timer)
  }

  return id
}

function removeToast(id) {
  const timer = _timers.get(id)
  if (timer) {
    clearTimeout(timer)
    _timers.delete(id)
  }
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

export function useToast() {
  return { toasts, addToast, removeToast }
}
