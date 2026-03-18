/**
 * useNotificationPoller — polls /notifications/summary to detect new notifications.
 *
 * When the unread count increases, a toast is shown and stores/badges are updated.
 * Pauses automatically when the browser tab is hidden.
 */
import { ref, onBeforeUnmount } from 'vue'
import { getNotificationSummary } from '@/services/api'
import { useNotificationStore } from '@/stores/notification'
import { useToast } from './useToast'

const POLL_INTERVAL_MS = 30_000

export function useNotificationPoller() {
  const polling = ref(false)
  let intervalId = null
  let lastUnread = null

  const store = useNotificationStore()
  const { addToast } = useToast()

  async function _poll() {
    try {
      const data = await getNotificationSummary()
      const currentUnread = data?.unread ?? 0

      store.summary = {
        total: data.total ?? 0,
        unread: currentUnread,
        action_required: data.action_required ?? 0,
        by_priority: data.by_priority ?? { urgent: 0, high: 0, normal: 0, low: 0 },
        by_event_type: data.by_event_type ?? {},
      }

      if (lastUnread !== null && currentUnread > lastUnread) {
        const diff = currentUnread - lastUnread
        addToast(
          diff === 1 ? 'You have a new notification' : `You have ${diff} new notifications`,
          { type: 'info', duration: 5000 },
        )
      }

      lastUnread = currentUnread
    } catch {
      // Network errors are non-critical; keep polling
    }
  }

  function _onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      _clearInterval()
    } else if (polling.value) {
      _poll()
      _setInterval()
    }
  }

  function _setInterval() {
    _clearInterval()
    intervalId = setInterval(_poll, POLL_INTERVAL_MS)
  }

  function _clearInterval() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function startPolling() {
    if (polling.value) return
    polling.value = true
    _poll()
    _setInterval()
    document.addEventListener('visibilitychange', _onVisibilityChange)
  }

  function stopPolling() {
    polling.value = false
    _clearInterval()
    document.removeEventListener('visibilitychange', _onVisibilityChange)
  }

  onBeforeUnmount(() => {
    stopPolling()
  })

  return { polling, startPolling, stopPolling }
}
