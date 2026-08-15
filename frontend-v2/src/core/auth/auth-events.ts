import type { AuthUser } from './auth-types'

/**
 * Cầu nối một chiều http-client -> auth-store, đi qua CustomEvent thay vì import trực tiếp.
 * Lý do: auth-store gọi http-client (login/logout), nếu http-client lại import auth-store
 * thì thành vòng lặp import. Event bus nhỏ này cắt vòng đó.
 */

const USER_REFRESHED = 'erp:auth:user-refreshed'
const SESSION_EXPIRED = 'erp:auth:session-expired'

export const authEvents = {
  /** Refresh token thành công, backend trả kèm hồ sơ + phân quyền mới nhất. */
  emitUserRefreshed: (user: AuthUser) =>
    window.dispatchEvent(new CustomEvent(USER_REFRESHED, { detail: user })),

  onUserRefreshed: (handler: (user: AuthUser) => void) => {
    const listener = (e: Event) => handler((e as CustomEvent<AuthUser>).detail)
    window.addEventListener(USER_REFRESHED, listener)
    return () => window.removeEventListener(USER_REFRESHED, listener)
  },

  /** Hết phiên (refresh thất bại) — store xóa state, router đá về /login. */
  emitSessionExpired: () => window.dispatchEvent(new CustomEvent(SESSION_EXPIRED)),

  onSessionExpired: (handler: () => void) => {
    window.addEventListener(SESSION_EXPIRED, handler)
    return () => window.removeEventListener(SESSION_EXPIRED, handler)
  },
}
