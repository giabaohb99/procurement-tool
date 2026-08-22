/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_API_PROXY_TARGET?: string
  readonly VITE_APP_NAME?: string
  /** Địa chỉ app Trung tâm Hướng dẫn sử dụng (mặc định http://localhost:8082). */
  readonly VITE_HELP_URL?: string
  /**
   * `dev` = bật mấy thứ chỉ dành cho bản chạy thử (hiện có: Đổi tài khoản nhanh).
   * Dùng chung tên với bản v1 để một dòng trong `.env.dev` bật được cả hai app.
   * Bản thật để TRỐNG — xem `demo-accounts.ts`, tệp đó chứa mật khẩu.
   */
  readonly VITE_DEVELOPER_MODE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
