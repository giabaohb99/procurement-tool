// vite.config.ts
import { defineConfig } from "file:///app/node_modules/vite/dist/node/index.js";
import react from "file:///app/node_modules/@vitejs/plugin-react/dist/index.js";
import { VitePWA } from "file:///app/node_modules/vite-plugin-pwa/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      // có bản mới → hỏi user, không reload đột ngột
      includeAssets: ["logo.svg", "push-sw.js"],
      manifest: {
        name: "DEGO Thu Mua",
        short_name: "Thu Mua",
        description: "C\xF4ng c\u1EE5 mua h\xE0ng DEGO Holding",
        lang: "vi",
        theme_color: "#00aeef",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [
          { src: "pwa-192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512.png", sizes: "512x512", type: "image/png" },
          { src: "pwa-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" }
        ]
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        // chỉ precache asset tĩnh
        navigateFallbackDenylist: [/^\/api/],
        // /api không fallback về index.html
        importScripts: ["push-sw.js"],
        // nạp handler Web Push vào SW
        runtimeCaching: [
          { urlPattern: /\/api\//, handler: "NetworkOnly" }
          // data luôn realtime, KHÔNG cache
        ],
        cleanupOutdatedCaches: true
      },
      devOptions: { enabled: false }
      // SW chỉ chạy ở bản build prod, dev/HMR không đụng
    })
  ],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    // Cho phép các host từ Cloudflare/ngrok
    watch: { usePolling: true },
    // để HMR nhận thay đổi qua volume trên Docker/Windows
    proxy: {
      "/api": {
        target: "http://api:8000",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvYXBwXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvYXBwL3ZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9hcHAvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgcmVhY3QgZnJvbSAnQHZpdGVqcy9wbHVnaW4tcmVhY3QnXHJcbmltcG9ydCB7IFZpdGVQV0EgfSBmcm9tICd2aXRlLXBsdWdpbi1wd2EnXHJcblxyXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xyXG4gIHBsdWdpbnM6IFtcclxuICAgIHJlYWN0KCksXHJcbiAgICBWaXRlUFdBKHtcclxuICAgICAgcmVnaXN0ZXJUeXBlOiAncHJvbXB0JywgICAgICAgICAgICAgIC8vIGNcdTAwRjMgYlx1MUVBM24gbVx1MUVEQmkgXHUyMTkyIGhcdTFFQ0ZpIHVzZXIsIGtoXHUwMEY0bmcgcmVsb2FkIFx1MDExMVx1MUVEOXQgbmdcdTFFRDl0XHJcbiAgICAgIGluY2x1ZGVBc3NldHM6IFsnbG9nby5zdmcnLCAncHVzaC1zdy5qcyddLFxyXG4gICAgICBtYW5pZmVzdDoge1xyXG4gICAgICAgIG5hbWU6ICdERUdPIFRodSBNdWEnLFxyXG4gICAgICAgIHNob3J0X25hbWU6ICdUaHUgTXVhJyxcclxuICAgICAgICBkZXNjcmlwdGlvbjogJ0NcdTAwRjRuZyBjXHUxRUU1IG11YSBoXHUwMEUwbmcgREVHTyBIb2xkaW5nJyxcclxuICAgICAgICBsYW5nOiAndmknLFxyXG4gICAgICAgIHRoZW1lX2NvbG9yOiAnIzAwYWVlZicsXHJcbiAgICAgICAgYmFja2dyb3VuZF9jb2xvcjogJyNmZmZmZmYnLFxyXG4gICAgICAgIGRpc3BsYXk6ICdzdGFuZGFsb25lJyxcclxuICAgICAgICBzdGFydF91cmw6ICcvJyxcclxuICAgICAgICBzY29wZTogJy8nLFxyXG4gICAgICAgIGljb25zOiBbXHJcbiAgICAgICAgICB7IHNyYzogJ3B3YS0xOTIucG5nJywgc2l6ZXM6ICcxOTJ4MTkyJywgdHlwZTogJ2ltYWdlL3BuZycgfSxcclxuICAgICAgICAgIHsgc3JjOiAncHdhLTUxMi5wbmcnLCBzaXplczogJzUxMng1MTInLCB0eXBlOiAnaW1hZ2UvcG5nJyB9LFxyXG4gICAgICAgICAgeyBzcmM6ICdwd2EtbWFza2FibGUtNTEyLnBuZycsIHNpemVzOiAnNTEyeDUxMicsIHR5cGU6ICdpbWFnZS9wbmcnLCBwdXJwb3NlOiAnbWFza2FibGUnIH0sXHJcbiAgICAgICAgXSxcclxuICAgICAgfSxcclxuICAgICAgd29ya2JveDoge1xyXG4gICAgICAgIGdsb2JQYXR0ZXJuczogWycqKi8qLntqcyxjc3MsaHRtbCxzdmcscG5nLGljbyx3b2ZmMn0nXSwgIC8vIGNoXHUxRUM5IHByZWNhY2hlIGFzc2V0IHRcdTAxMjluaFxyXG4gICAgICAgIG5hdmlnYXRlRmFsbGJhY2tEZW55bGlzdDogWy9eXFwvYXBpL10sICAgICAgICAgICAgICAgICAgICAgLy8gL2FwaSBraFx1MDBGNG5nIGZhbGxiYWNrIHZcdTFFQzEgaW5kZXguaHRtbFxyXG4gICAgICAgIGltcG9ydFNjcmlwdHM6IFsncHVzaC1zdy5qcyddLCAgICAgICAgICAgICAgICAgICAgICAgICAgICAvLyBuXHUxRUExcCBoYW5kbGVyIFdlYiBQdXNoIHZcdTAwRTBvIFNXXHJcbiAgICAgICAgcnVudGltZUNhY2hpbmc6IFtcclxuICAgICAgICAgIHsgdXJsUGF0dGVybjogL1xcL2FwaVxcLy8sIGhhbmRsZXI6ICdOZXR3b3JrT25seScgfSwgICAgICAvLyBkYXRhIGx1XHUwMEY0biByZWFsdGltZSwgS0hcdTAwRDRORyBjYWNoZVxyXG4gICAgICAgIF0sXHJcbiAgICAgICAgY2xlYW51cE91dGRhdGVkQ2FjaGVzOiB0cnVlLFxyXG4gICAgICB9LFxyXG4gICAgICBkZXZPcHRpb25zOiB7IGVuYWJsZWQ6IGZhbHNlIH0sICAgICAgIC8vIFNXIGNoXHUxRUM5IGNoXHUxRUExeSBcdTFFREYgYlx1MUVBM24gYnVpbGQgcHJvZCwgZGV2L0hNUiBraFx1MDBGNG5nIFx1MDExMVx1MUVFNW5nXHJcbiAgICB9KSxcclxuICBdLFxyXG4gIHNlcnZlcjoge1xyXG4gICAgaG9zdDogdHJ1ZSxcclxuICAgIHBvcnQ6IDUxNzMsXHJcbiAgICBhbGxvd2VkSG9zdHM6IHRydWUsIC8vIENobyBwaFx1MDBFOXAgY1x1MDBFMWMgaG9zdCB0XHUxRUVCIENsb3VkZmxhcmUvbmdyb2tcclxuICAgIHdhdGNoOiB7IHVzZVBvbGxpbmc6IHRydWUgfSwgLy8gXHUwMTExXHUxRUMzIEhNUiBuaFx1MUVBRG4gdGhheSBcdTAxMTFcdTFFRDVpIHF1YSB2b2x1bWUgdHJcdTAwRUFuIERvY2tlci9XaW5kb3dzXHJcbiAgICBwcm94eToge1xyXG4gICAgICAnL2FwaSc6IHtcclxuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vYXBpOjgwMDAnLFxyXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcclxuICAgICAgfSxcclxuICAgIH0sXHJcbiAgfSxcclxufSlcclxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUE4TCxTQUFTLG9CQUFvQjtBQUMzTixPQUFPLFdBQVc7QUFDbEIsU0FBUyxlQUFlO0FBRXhCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVM7QUFBQSxJQUNQLE1BQU07QUFBQSxJQUNOLFFBQVE7QUFBQSxNQUNOLGNBQWM7QUFBQTtBQUFBLE1BQ2QsZUFBZSxDQUFDLFlBQVksWUFBWTtBQUFBLE1BQ3hDLFVBQVU7QUFBQSxRQUNSLE1BQU07QUFBQSxRQUNOLFlBQVk7QUFBQSxRQUNaLGFBQWE7QUFBQSxRQUNiLE1BQU07QUFBQSxRQUNOLGFBQWE7QUFBQSxRQUNiLGtCQUFrQjtBQUFBLFFBQ2xCLFNBQVM7QUFBQSxRQUNULFdBQVc7QUFBQSxRQUNYLE9BQU87QUFBQSxRQUNQLE9BQU87QUFBQSxVQUNMLEVBQUUsS0FBSyxlQUFlLE9BQU8sV0FBVyxNQUFNLFlBQVk7QUFBQSxVQUMxRCxFQUFFLEtBQUssZUFBZSxPQUFPLFdBQVcsTUFBTSxZQUFZO0FBQUEsVUFDMUQsRUFBRSxLQUFLLHdCQUF3QixPQUFPLFdBQVcsTUFBTSxhQUFhLFNBQVMsV0FBVztBQUFBLFFBQzFGO0FBQUEsTUFDRjtBQUFBLE1BQ0EsU0FBUztBQUFBLFFBQ1AsY0FBYyxDQUFDLHNDQUFzQztBQUFBO0FBQUEsUUFDckQsMEJBQTBCLENBQUMsUUFBUTtBQUFBO0FBQUEsUUFDbkMsZUFBZSxDQUFDLFlBQVk7QUFBQTtBQUFBLFFBQzVCLGdCQUFnQjtBQUFBLFVBQ2QsRUFBRSxZQUFZLFdBQVcsU0FBUyxjQUFjO0FBQUE7QUFBQSxRQUNsRDtBQUFBLFFBQ0EsdUJBQXVCO0FBQUEsTUFDekI7QUFBQSxNQUNBLFlBQVksRUFBRSxTQUFTLE1BQU07QUFBQTtBQUFBLElBQy9CLENBQUM7QUFBQSxFQUNIO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixjQUFjO0FBQUE7QUFBQSxJQUNkLE9BQU8sRUFBRSxZQUFZLEtBQUs7QUFBQTtBQUFBLElBQzFCLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
