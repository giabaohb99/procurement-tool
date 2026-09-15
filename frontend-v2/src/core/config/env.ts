/**
 * Điểm truy cập DUY NHẤT tới biến môi trường. Không đọc `import.meta.env` rải rác
 * trong code — mọi biến mới khai báo ở đây để có chỗ tra cứu và ép kiểu tập trung.
 */

interface AppEnv {
  /** Rỗng = gọi tương đối qua proxy Vite (dev). Production đặt domain thật. */
  apiUrl: string
  appName: string
  /**
   * Client ID của Google Identity Services (bao-CR-406). RỖNG = máy này chưa khai
   * — màn đăng nhập phải ẩn hẳn cụm Google chứ đừng dựng nút rỗng, xem
   * `core/auth/pages/login-page.tsx`.
   */
  googleClientId: string
  isDev: boolean
  isProd: boolean
}

export const env: AppEnv = {
  apiUrl: import.meta.env.VITE_API_URL ?? '',
  appName: import.meta.env.VITE_APP_NAME ?? 'DEGO ERP',
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
}
