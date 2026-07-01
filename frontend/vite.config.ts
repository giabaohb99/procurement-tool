import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true, // Cho phép các host từ Cloudflare/ngrok
    watch: { usePolling: true }, // để HMR nhận thay đổi qua volume trên Docker/Windows
  },
})
