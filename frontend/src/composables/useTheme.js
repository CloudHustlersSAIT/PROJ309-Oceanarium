/**
 * useTheme — singleton composable for class-based dark mode.
 *
 * Applies the `dark` class to <html> — required by Tailwind's `dark:` utilities.
 * Priority: localStorage → system prefers-color-scheme → light
 */
import { computed, ref } from 'vue'

const THEME_STORAGE_KEY = 'oceanarium-theme'

// Module-level singleton so all component instances share the same state
const theme = ref('light')
let _initialized = false

function _normalize(val) {
  return val === 'dark' ? 'dark' : 'light'
}

function _apply(val) {
  if (typeof document === 'undefined') return

  // Toggle the `dark` class on <html> — this is what activates all dark: utilities
  document.documentElement.classList.toggle('dark', val === 'dark')
  document.documentElement.setAttribute('data-theme', val)
  try {
    localStorage.setItem(THEME_STORAGE_KEY, val)
  } catch {
    /* noop */
  }
}

function _init() {
  if (_initialized) return
  _initialized = true

  if (typeof window === 'undefined') {
    theme.value = 'light'
    return
  }

  let stored = null
  try {
    stored = localStorage.getItem(THEME_STORAGE_KEY)
  } catch {
    /* noop */
  }
  const system = window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  theme.value = _normalize(stored || system)
  _apply(theme.value)
}

export function useTheme() {
  _init()

  function setTheme(val) {
    const next = _normalize(val)
    theme.value = next
    _apply(next)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return {
    theme,
    isDark: computed(() => theme.value === 'dark'),
    setTheme,
    toggleTheme,
  }
}
