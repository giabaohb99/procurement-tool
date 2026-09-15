import { apiGet, apiPost, apiPut } from '@/core/api'
import type { AuthUser, LoginCredentials, LoginResponse } from './auth-types'

/** Lời gọi API thuần của auth — không giữ state, state nằm ở `auth-store`. */
export const authService = {
  login: (credentials: LoginCredentials) =>
    apiPost<LoginResponse>('/api/auth/login', credentials, { _silent: true } as never),

  /**
   * Đăng nhập bằng Google (bao-CR-406). `credential` là JWT do Google Identity
   * Services phát; backend tự xác thực chữ ký rồi tra email sang hồ sơ nhân sự,
   * nên ở đây không bóc token ra đọc. Cùng phong bì trả về với `login`.
   */
  loginGoogle: (credential: string) =>
    apiPost<LoginResponse>('/api/auth/google', { credential }, { _silent: true } as never),

  /** Ghi log đăng xuất phía server. Lỗi mạng thì kệ, client vẫn xóa token. */
  logout: () => apiPost<null>('/api/auth/logout', null, { _silent: true } as never),

  me: () => apiGet<AuthUser>('/api/auth/me'),

  /**
   * Tự bật/tắt EMAIL thông báo luồng duyệt của chính mình (bao-CR-349).
   * Không đòi quyền gì — mỗi người tự quyết hộp thư của mình.
   */
  setNotifyEmail: (notifyEmail: boolean) =>
    apiPut<{ notify_email: boolean }>('/api/auth/notify-email', {
      notify_email: notifyEmail,
    }),
}
