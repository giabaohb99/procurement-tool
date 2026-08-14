import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// Codebase ERP v2 — dùng chung backend FastAPI với `frontend/` và `help-center/`.
// Mọi request đi đường tương đối `/api/...` rồi qua proxy dưới đây, nên không dính CORS
// khi mở từ localhost, LAN hay tunnel (Cloudflare/ngrok).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Chạy ngoài Docker -> localhost:8000. Chạy trong docker compose -> đặt http://api:8000.
  const apiTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      // fileURLToPath chứ KHÔNG phải .pathname: trên Windows .pathname trả về
      // '/D:/New%20folder/...' — có gạch chéo thừa ở đầu và dấu cách bị mã hóa.
      // Dev server bỏ qua được, nhưng `vite build` (rolldown) đọc thẳng đường dẫn
      // đó và chết ngay ở import đầu tiên (os error 123).
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      host: true,
      port: 5174, // 5173 đang dành cho `frontend/` (bản hiện tại)
      // Port bận thì DỪNG hẳn, không tự nhảy sang 5175. Nhảy port sinh ra hai
      // dev server chạy song song: tab mở ở server cũ sẽ hỏng chunk lazy ngay khi
      // server đó tắt ("error loading dynamically imported module").
      strictPort: true,
      allowedHosts: true,
      watch: { usePolling: true }, // HMR qua volume trên Docker/Windows
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
      },
    },
  }
})
