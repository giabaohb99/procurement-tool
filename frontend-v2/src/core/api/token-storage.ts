import { appConfig } from '@/core/config/app-config'

/**
 * Nơi DUY NHẤT đụng vào token trong localStorage.
 * Tách riêng khỏi auth-store để http-client đọc/ghi token được mà không tạo
 * vòng lặp import (http-client -> store -> http-client).
 */

const { accessToken, refreshToken, user } = appConfig.storageKeys

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(accessToken),
  getRefreshToken: () => localStorage.getItem(refreshToken),

  setTokens: (access: string, refresh?: string) => {
    localStorage.setItem(accessToken, access)
    if (refresh) localStorage.setItem(refreshToken, refresh)
  },

  clear: () => {
    localStorage.removeItem(accessToken)
    localStorage.removeItem(refreshToken)
    localStorage.removeItem(user)
  },
}
