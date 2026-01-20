import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5176,
    proxy: {
      '/documents': 'http://127.0.0.1:8000',
      '/results': 'http://127.0.0.1:8000',
      '/insights': 'http://127.0.0.1:8000',
      '/biomarker-info': 'http://127.0.0.1:8000',
      '/analysis/summary': 'http://127.0.0.1:8000',
      '/api': 'http://127.0.0.1:8000',
    }
  },
})
