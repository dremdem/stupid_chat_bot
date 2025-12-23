/* eslint-env node */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend host - 'localhost' for local dev, 'backend' for Docker
const backendHost = process.env.VITE_BACKEND_HOST || 'localhost'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://${backendHost}:8000`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://${backendHost}:8000`,
        ws: true,
      },
    },
  },
})
