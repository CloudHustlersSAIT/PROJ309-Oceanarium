import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(async () => {
  const plugins = [vue(), vueDevTools()]

  // Allow app startup even if @tailwindcss/vite is not installed locally.
  try {
    const { default: tailwindcss } = await import('@tailwindcss/vite')
    plugins.push(tailwindcss())
  } catch {
    // Tailwind Vite plugin unavailable; keep running without hard failure.
  }

  return {
    plugins,
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      // Remove console logs in production builds
      minify: 'esbuild',
      esbuild: {
        drop: ['console', 'debugger'],
      },
    },
  }
})
