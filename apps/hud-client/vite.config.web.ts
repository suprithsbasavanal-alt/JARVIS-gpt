import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Web-only configuration for browser-based testing and verification
export default defineConfig({
  plugins: [
    react()
  ],
  server: {
    port: 5173,
    host: 'localhost'
  }
})
