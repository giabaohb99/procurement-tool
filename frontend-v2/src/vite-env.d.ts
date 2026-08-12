/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_API_PROXY_TARGET?: string
  readonly VITE_APP_NAME?: string
  /** Địa chỉ app Trung tâm Hướng dẫn sử dụng (mặc định http://localhost:8082). */
  readonly VITE_HELP_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
