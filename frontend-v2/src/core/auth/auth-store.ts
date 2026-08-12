import { create } from 'zustand'

import { queryClient, tokenStorage } from '@/core/api'
import { appConfig } from '@/core/config/app-config'
import { logger } from '@/core/telemetry/logger'
import { authService } from './auth-service'
import type { AuthUser, LoginCredentials } from './auth-types'

interface AuthState {
  user: AuthUser | null
  /** Đang xử lý login — dùng để khóa nút submit. */
  isLoggingIn: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  /** Ghi đè hồ sơ (dùng khi refresh token trả về profile mới, hoặc user tự sửa). */
  setUser: (user: AuthUser | null) => void
}

/** Đọc hồ sơ đã lưu để khỏi nháy màn hình login khi F5. */
function readStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(appConfig.storageKeys.user)
    return raw ? (JSON.parse(raw) as AuthUser) : null
  } catch (error) {
    logger.warn('Hồ sơ trong localStorage hỏng, bỏ qua', error)
    return null
  }
}

/**
 * Không dùng middleware `persist`: token phải ghi trước cả khi store khởi tạo
 * (http-client đọc token ở interceptor), nên ghi tay qua `tokenStorage` cho rõ thứ tự.
 */
export const useAuthStore = create<AuthState>((set) => ({
  user: readStoredUser(),
  isLoggingIn: false,

  login: async (credentials) => {
    set({ isLoggingIn: true })
    try {
      const { access_token, refresh_token, user } = await authService.login(credentials)
      tokenStorage.setTokens(access_token, refresh_token)
      localStorage.setItem(appConfig.storageKeys.user, JSON.stringify(user))
      set({ user })
    } finally {
      set({ isLoggingIn: false })
    }
  },

  logout: () => {
    void authService.logout().catch(() => {}) // best-effort, không chặn việc thoát
    tokenStorage.clear()
    // Xóa cache React Query: tránh người kế tiếp đăng nhập trên cùng máy
    // nhìn thấy dữ liệu của tài khoản trước trong khoảnh khắc đầu.
    queryClient.clear()
    set({ user: null })
  },

  setUser: (user) => {
    if (user) localStorage.setItem(appConfig.storageKeys.user, JSON.stringify(user))
    else localStorage.removeItem(appConfig.storageKeys.user)
    set({ user })
  },
}))
