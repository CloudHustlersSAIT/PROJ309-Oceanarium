import { computed, ref } from "vue";

const THEME_STORAGE_KEY = "oceanarium-theme";
const DARK_CLASS = "theme-dark";
const theme = ref("light");
const initialized = ref(false);

function normalizeTheme(value) {
  return value === "dark" ? "dark" : "light";
}

function detectSystemTheme() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "light";
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(nextTheme) {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  const isDark = nextTheme === "dark";
  root.classList.toggle(DARK_CLASS, isDark);
  root.setAttribute("data-theme", nextTheme);
}

function readStoredTheme() {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(THEME_STORAGE_KEY);
}

function persistTheme(nextTheme) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
}

export function initTheme() {
  if (!initialized.value) {
    const preferred = normalizeTheme(readStoredTheme() || detectSystemTheme());
    theme.value = preferred;
    initialized.value = true;
  }

  applyTheme(theme.value);
  return theme.value;
}

export function useTheme() {
  if (!initialized.value) {
    initTheme();
  }

  function setTheme(nextTheme) {
    const normalized = normalizeTheme(nextTheme);
    theme.value = normalized;
    applyTheme(normalized);
    persistTheme(normalized);
  }

  function toggleTheme() {
    setTheme(theme.value === "dark" ? "light" : "dark");
  }

  return {
    theme,
    isDark: computed(() => theme.value === "dark"),
    setTheme,
    toggleTheme,
  };
}
