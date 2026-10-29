import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // duoc-CR-685: SW mới tự kích hoạt ngay, không chờ người dùng bấm. Tab bản mới tự hiện
      // popup + tải lại lúc 0h (PwaReloadPrompt); tab bản cũ bị sw-update-old-clients.js tải lại.
      registerType: 'autoUpdate',
      includeAssets: ['logo.svg', 'push-sw.js', 'sw-update-old-clients.js'],
      manifest: {
        name: 'DEGO Thu Mua',
        short_name: 'Thu Mua',
        description: 'Công cụ mua hàng DEGO Holding',
        lang: 'vi',
        theme_color: '#00aeef',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],  // chỉ precache asset tĩnh
        navigateFallbackDenylist: [/^\/api/],                     // /api không fallback về index.html
        importScripts: ['push-sw.js', 'sw-update-old-clients.js'], // Web Push + ép tab bản cũ lên bản mới
        skipWaiting: true,
        clientsClaim: true,
        runtimeCaching: [
          { urlPattern: /\/api\//, handler: 'NetworkOnly' },      // data luôn realtime, KHÔNG cache
        ],
        cleanupOutdatedCaches: true,
      },
      devOptions: { enabled: false },       // SW chỉ chạy ở bản build prod, dev/HMR không đụng
    }),
  ],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true, // Cho phép các host từ Cloudflare/ngrok
    // HMR nhận thay đổi qua volume trên Docker/Windows. Nhịp hỏi vòng mặc định
    // (100ms) ngốn hết vòng lặp sự kiện của Node, mà proxy `/api` chạy chung vòng
    // lặp đó nên MỌI lượt gọi API ở chế độ dev bị om ~200ms và xếp hàng nối đuôi.
    // Lý do đầy đủ + số đo ở `frontend-v2/vite.config.ts`.
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
