import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// App Trung tâm Hướng dẫn sử dụng — chạy độc lập với frontend nghiệp vụ,
// nhưng DÙNG CHUNG backend (proxy /api -> api:8000 giống frontend).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,             // cho phép host từ Cloudflare/ngrok
    watch: { usePolling: true },    // HMR nhận thay đổi qua volume trên Docker/Windows
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
})
