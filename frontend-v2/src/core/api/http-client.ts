import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { toast } from 'sonner'

import { authEvents } from '@/core/auth/auth-events'
import { env } from '@/core/config/env'
import { tokenStorage } from './token-storage'
import { extractErrorMessage, type SuccessEnvelope } from './response-envelope'

/** Cờ nội bộ gắn thêm vào config của từng request. */
interface RequestConfig extends InternalAxiosRequestConfig {
  /** Đã thử refresh token cho request này rồi — không thử lại lần hai. */
  _retry?: boolean
  /** Tự xử lý lỗi, đừng bật toast tự động. */
  _silent?: boolean
}

export const httpClient = axios.create({
  baseURL: env.apiUrl,
  // indexes: null -> mảng serialize thành `key=a&key=b` (LẶP key, không có `[]`).
  // Backend đọc bằng request.query_params.multi_items() nên cần đúng dạng này
  // khi một cột có nhiều điều kiện lọc.
  paramsSerializer: { indexes: null },
})

httpClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/**
 * Gộp các lần refresh đồng thời vào MỘT request. Nhiều query chạy song song cùng
 * dính 401 thì chỉ gọi /auth/refresh một lần rồi cùng chờ kết quả đó.
 */
let refreshPromise: Promise<string> | null = null

function refreshAccessToken(refreshToken: string): Promise<string> {
  refreshPromise ??= axios
    .post<SuccessEnvelope<{ access_token: string; user?: unknown }>>(
      `${env.apiUrl}/api/auth/refresh`,
      { refresh_token: refreshToken },
    )
    .then((res) => {
      const { access_token, user } = res.data.data
      // Backend trả kèm hồ sơ + phân quyền mới nhất trong chính response refresh
      // (khoảng 60 phút/lần, đúng nhịp access token hết hạn) nên không cần gọi
      // thêm /auth/me: đổi tên, đổi phòng ban hay sửa quyền có hiệu lực ngay.
      if (user) authEvents.emitUserRefreshed(user as never)
      tokenStorage.setTokens(access_token)
      return access_token
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RequestConfig | undefined

    // 401 -> thử refresh đúng MỘT lần. Bỏ qua chính các route /auth/ để tránh đệ quy.
    const canRetry =
      error.response?.status === 401 &&
      config &&
      !config._retry &&
      !config.url?.includes('/auth/')

    if (canRetry) {
      const refreshToken = tokenStorage.getRefreshToken()
      if (!refreshToken) {
        authEvents.emitSessionExpired()
        return Promise.reject(error)
      }

      config._retry = true
      try {
        const newToken = await refreshAccessToken(refreshToken)
        config.headers.Authorization = `Bearer ${newToken}`
        return httpClient(config)
      } catch {
        authEvents.emitSessionExpired()
        return Promise.reject(error)
      }
    }

    // Toast tự động cho HÀNH ĐỘNG của người dùng (POST/PATCH/PUT/DELETE).
    // GET là nạp nền — để màn hình tự hiển thị trạng thái lỗi của nó.
    const method = (config?.method ?? 'get').toLowerCase()
    if (method !== 'get' && !config?._silent) {
      toast.error(extractErrorMessage(error))
    }

    return Promise.reject(error)
  },
)
