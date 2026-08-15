import { apiGet, apiPost } from '@/core/api'
import type { AuthUser, LoginCredentials, LoginResponse } from './auth-types'

/** Lời gọi API thuần của auth — không giữ state, state nằm ở `auth-store`. */
export const authService = {
  login: (credentials: LoginCredentials) =>
    apiPost<LoginResponse>('/api/auth/login', credentials, { _silent: true } as never),

  /** Ghi log đăng xuất phía server. Lỗi mạng thì kệ, client vẫn xóa token. */
  logout: () => apiPost<null>('/api/auth/logout', null, { _silent: true } as never),

  me: () => apiGet<AuthUser>('/api/auth/me'),
}
