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
    // HMR nhận thay đổi qua volume trên Docker/Windows. Giãn nhịp hỏi vòng để
    // proxy `/api` không bị vòng quét tệp chiếm vòng lặp sự kiện — lý do đầy đủ
    // + số đo ở `frontend-v2/vite.config.ts`.
    watch: {
      usePolling: true,
      interval: 1000,
      binaryInterval: 2000,
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**'],
    },
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
})
