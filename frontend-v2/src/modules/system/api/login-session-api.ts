import { apiGet, apiPost } from '@/core/api'
import type { ListParams } from '@/shared/types/api'

/**
 * PHIÊN ĐĂNG NHẬP (bao-CR-395, CR-312 P3b) — một nguồn dữ liệu cho ba màn:
 *
 * - `/system/sessions`      — toàn hệ, cần khóa `login_session` (read / delete);
 * - thẻ ở hồ sơ nhân sự     — phiên + lịch sử 90 ngày của MỘT người, cùng khóa;
 * - «Thiết bị của tôi» ở /me — cửa `/api/auth/sessions*`, CHỈ đòi đăng nhập.
 *
 * Hai đường cắt phiên khác nhau về tốc độ: đá MỘT phiên đi qua `revoked_at`
 * (token cũ còn sống tối đa 60 giây vì cache hồ sơ quyền), còn «bắt đăng nhập
 * lại» tăng `token_version` nên hiệu lực tức thì. Nhãn trên nút phải nói rõ
 * điều đó, đừng hứa "đá ngay" ở nút đầu.
 */

/** Loại máy — khớp `DeviceType` (IntEnum) ở backend. */
export const DEVICE_TYPE = { DESKTOP: 1, MOBILE: 2, TABLET: 3, UNKNOWN: 9 } as const

/** Lý do phiên bị cắt — khớp `RevokeReason`. Phiên còn sống thì `null`. */
export const REVOKE_REASON = {
  SELF_LOGOUT: 1,
  ADMIN_KICK: 2,
  PASSWORD_CHANGED: 3,
  FORCE_RELOGIN: 4,
  ACCOUNT_LOCKED: 5,
} as const

/** Khớp `serialize_session` ở `login_session/schema.py`. */
export interface LoginSessionItem {
  id: number
  user_id: number
  /** Tên nhân sự › email › `User #id` — rỗng ở cửa «Thiết bị của tôi». */
  user_name: string
  ip: string
  last_seen_ip: string
  device_type: number
  device_type_label: string
  os: string
  browser: string
  /** Chuỗi gộp "Chrome trên Windows" do backend dựng. */
  device_label: string
  user_agent: string
  login_method: number
  login_method_label: string
  created_at: string
  last_seen_at: string | null
  refreshed_at: string | null
  refresh_count: number
  expires_at: string | null
  revoked_at: string | null
  revoked_by: number
  revoked_by_name: string
  revoke_reason: number | null
  revoke_reason_label: string
  /** Chưa thu hồi VÀ chưa quá hạn. */
  is_alive: boolean
  /** Câu tình trạng đã dựng sẵn: «Còn hiệu lực» · «Hết hạn» · «Đã đá bởi …». */
  ending: string
  /** Chính phiên đang gọi API — chỉ có nghĩa ở cửa «Thiết bị của tôi». */
  is_current: boolean
}

export interface LoginSessionListResult {
  items: LoginSessionItem[]
  total: number
  page: number
  page_size: number
}

/** Loại dòng lịch sử — khớp `HISTORY_KIND_LOGIN` / `HISTORY_KIND_LOGIN_FAILED`
 *  ở `backend/app/modules/login_session/schema.py`. */
export const HISTORY_KIND = { LOGIN: 1, LOGIN_FAILED: 2 } as const

/** Một dòng lịch sử: đăng nhập THÀNH CÔNG (`ok=true`, từ bảng phiên) hoặc
 *  THẤT BẠI (`ok=false`, từ `tab_audit_log`, chỉ có `at` + `ip` + `message`). */
export interface LoginHistoryItem {
  kind: number
  ok: boolean
  at: string
  session_id: number
  login_method: number
  login_method_label: string
  device_label: string
  ip: string
  ending: string
  revoked_by_name: string
  message: string
}

export interface LoginHistoryResult {
  items: LoginHistoryItem[]
  days: number
  login_count: number
  failed_count: number
}

export interface MySessionsResult {
  items: LoginSessionItem[]
  current_session_id: number
}

export interface LoginSessionListParams extends ListParams {
  /** 0 = mọi người trong phạm vi. */
  user_id?: number
  /** Mặc định backend là `true` — tab hồ sơ tắt để xem cả phiên đã kết thúc. */
  active_only?: boolean
}

export const loginSessionApi = {
  list: (params: LoginSessionListParams) =>
    apiGet<LoginSessionListResult>('/api/login-sessions', { params }),

  /** Đá MỘT phiên (`revoked_at`, lý do ADMIN_KICK) — có trễ tối đa 60 giây. */
  revoke: (sessionId: number) =>
    apiPost<null>(`/api/login-sessions/${sessionId}/revoke`, {}),

  /** Bắt một người đăng nhập lại ở MỌI thiết bị — tăng `token_version`, tức thì. */
  logoutAll: (userId: number) =>
    apiPost<{ revoked: number }>(`/api/login-sessions/users/${userId}/logout-all`, {}),

  history: (userId: number, days: number) =>
    apiGet<LoginHistoryResult>('/api/login-sessions/history', {
      params: { user_id: userId, days },
    }),

  /** Ba cửa của CHÍNH MÌNH — không cần khóa `login_session`. */
  mySessions: (activeOnly: boolean) =>
    apiGet<MySessionsResult>('/api/auth/sessions', { params: { active_only: activeOnly } }),

  revokeMine: (sessionId: number) =>
    apiPost<null>(`/api/auth/sessions/${sessionId}/revoke`, {}),

  /** Đăng xuất mọi thiết bị KHÁC — chừa phiên đang bấm. */
  revokeMyOthers: () => apiPost<{ revoked: number }>('/api/auth/sessions/revoke-others', {}),
}
