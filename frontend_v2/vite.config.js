import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import compression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    react(),
    // Generate gzip-compressed assets for faster delivery
    compression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 1024, // Only compress files > 1KB
    }),
  ],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  build: {
    // Better code splitting for caching
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          i18n: ['i18next', 'react-i18next'],
          charts: ['recharts'],
        },
      },
    },
    // Enable source maps for Sentry but don't ship them
    sourcemap: 'hidden',
    // Target modern browsers for smaller bundle
    target: 'es2020',
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 600,
  },
})
