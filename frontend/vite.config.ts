import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Dev-proxy backend target. Defaults to the standard PACCA backend port.
  // Override when the backend runs elsewhere (e.g. to avoid a port collision
  // with another local service) by setting VITE_BACKEND_URL — either exported
  // in the shell or, preferably, in a gitignored frontend/.env.local:
  //   VITE_BACKEND_URL=http://localhost:8001
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_BACKEND_URL || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
        },
        '/health': {
          target,
          changeOrigin: true,
        },
      },
    },
  }
})
