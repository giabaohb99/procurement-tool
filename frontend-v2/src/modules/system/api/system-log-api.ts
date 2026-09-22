import { apiGet } from '@/core/api'

/**
 * NHẬT KÝ HỆ THỐNG (bao-CR-407, CR-312 P5) — ba cửa `/api/system-logs*`.
 *
 * ⚠️ **Khác `audit-log-api.ts`, đừng gộp.** Cửa kia đọc `tab_audit_log` (lớp kể
 * chuyện) và trả dòng thời gian của MỘT phiếu cho `AuditTimeline`. Cửa này lấy
 * `tab_request_log` làm xương sống: một dòng = một lượt gọi, kể cả lượt **không
 * đẻ ra dấu vết nào** — một `DELETE` ăn 403, một lượt 500 chết trước khi vào
 * service. Đó đúng là hai dòng người ta cần nhìn nhất lúc truy sự cố, và chúng
 * không tồn tại ở cửa kia.
 *
 * Hệ quả phải biết: dòng audit CŨ (ghi trước P1, chưa có `request_id`) **không
 * lên màn này**. Không phải mất — chúng vẫn đọc được ở dòng thời gian từng phiếu.
 *
 * ⚠️ **Giá trị trước/sau bị LƯỢC Ở BACKEND khi thiếu khóa `change_log`**, không
 * phải bị ẩn ở giao diện. Đọc cờ `can_read_changes` của gói chi tiết để nói cho
 * người dùng biết *"bạn không được xem"* thay vì để họ đọc nhầm thành *"lượt này
 * không đổi gì"* — hai thứ đó nếu không có cờ thì đều là một mảng rỗng.
 */

/** Nguồn sinh ra dòng nhật ký — khớp `SOURCE_*` ở `core/logging_codes.py`. */
export const LOG_SOURCE = { API: 1, CELERY: 2, SCRIPT: 3 } as const

export const LOG_SOURCE_LABEL: Record<number, string> = {
  [LOG_SOURCE.API]: 'Lời gọi API',
  [LOG_SOURCE.CELERY]: 'Việc nền',
  [LOG_SOURCE.SCRIPT]: 'Script',
}

/** Nhóm hành động — khớp `ACTION_GROUP_*`. `0` là «không rõ», không đưa vào ô lọc. */
export const ACTION_GROUP = {
  VIEW: 1,
  EDIT: 2,
  APPROVE: 3,
  DELETE: 4,
  AUTH: 5,
  EXPORT: 6,
  PERMISSION: 7,
} as const

export const ACTION_GROUP_LABEL: Record<number, string> = {
  [ACTION_GROUP.VIEW]: 'Xem',
  [ACTION_GROUP.EDIT]: 'Sửa',
  [ACTION_GROUP.APPROVE]: 'Duyệt',
  [ACTION_GROUP.DELETE]: 'Xóa',
  [ACTION_GROUP.AUTH]: 'Đăng nhập',
  [ACTION_GROUP.EXPORT]: 'Xuất dữ liệu',
  [ACTION_GROUP.PERMISSION]: 'Phân quyền',
}

/** Loại thao tác trên MỘT dòng dữ liệu — khớp `CHANGE_OP_*`. */
export const CHANGE_OP = { ADD: 1, UPDATE: 2, DELETE: 3 } as const

/**
 * Ô «Kết quả» — khớp `STATUS_*` ở `system_log/service.py`.
 *
 * ⚠️ «Bị chặn» (401/403) KHÔNG phải «lỗi» (5xx): 403 là hệ thống làm đúng việc
 * của nó. Trộn hai thứ thì câu hỏi *"hôm nay hỏng gì"* luôn bị vùi dưới hàng
 * trăm lượt 403 của người thiếu quyền.
 */
export const LOG_STATUS = { ALL: 'all', ERROR: 'error', BLOCKED: 'blocked' } as const
export type LogStatus = (typeof LOG_STATUS)[keyof typeof LOG_STATUS]

/** Một dòng trên bảng — khớp `serialize_row`. */
export interface SystemLogItem {
  /** UUID dạng chuỗi có gạch nối. Rỗng với dòng ghi trước P1. */
  request_id: string
  at: string
  user_id: number
  /** Tên nhân sự › email › `User #id`; `(chưa đăng nhập)` hoặc `hệ thống` khi `user_id = 0`. */
  user_name: string
  device: string
  ip: string
  session_id: number
  source: number
  source_label: string
  method: string
  path: string
  route: string
  http_status: number
  duration_ms: number
  error_code: string
  has_error_detail: boolean
  /** Câu tiếng Việt của dòng audit ĐẦU TIÊN; rơi về `METHOD path` khi không có. */
  summary: string
  action: string
  action_label: string
  action_group: number
  action_group_label: string
  entity: string
  entity_id: number
  doc_code: string
  audit_count: number
  change_count: number
  /** Số BẢNG khác nhau bị đụng — khác `change_count` là số TRƯỜNG. */
  change_table_count: number
}

export interface SystemLogListResult {
  items: SystemLogItem[]
  total: number
  page: number
  page_size: number
}

/** Tab «Request» — khớp `build_detail().request`. */
export interface SystemLogRequestDetail {
  request_id: string
  at: string
  user_id: number
  user_name: string
  device: string
  ip: string
  referer: string
  session_id: number
  source: number
  source_label: string
  method: string
  path: string
  route: string
  query_string: string
  http_status: number
  error_code: string
  duration_ms: number
  audit_count: number
  change_count: number
  /** Ba ô dưới đây CHỈ có khi người xem giữ khóa `change_log`.
   *
   *  ⚠️ Hai ô thân là **JSON** dưới CSDL (`Mapped[dict | None]`) và backend trả
   *  thẳng object, KHÔNG phải chuỗi — khai `string` như bản trước là làm cả trang
   *  nổ ở `.trim()`. Đọc bằng `logBodyText(...)`, đừng gọi thẳng hàm chuỗi lên
   *  chúng. `error_detail` mới thật là `Text`. */
  request_body?: unknown
  response_body?: unknown
  error_detail?: string
}

/** Tab «Tổng quan» — một dòng `tab_audit_log`. */
export interface SystemLogAuditEntry {
  id: number
  at: string
  by_id: number
  by: string
  entity: string
  entity_id: number
  action: string
  action_label: string
  action_group: number
  action_group_label: string
  message: string
  doc_code: string
  parent_entity: string
  parent_id: number
  changed_fields: string
  change_count: number
}

/** Tab «Thay đổi» — MỘT dòng cho MỘT trường (§4.3). */
export interface SystemLogChangeEntry {
  id: number
  at: string
  table_name: string
  row_id: number
  op: number
  op_label: string
  field: string
  before_value: string
  after_value: string
  snapshot_json: string
  /** Trường nhạy cảm đã bị che ở tầng ghi — giá trị hiện ra là dấu sao, không phải thật. */
  is_masked: boolean
}

/** Tab «Phiên» — `null` khi lượt gọi không gắn phiên nào (script, Celery, chưa đăng nhập). */
export interface SystemLogSessionInfo {
  id: number
  user_id: number
  ip: string
  last_seen_ip: string
  device_label: string
  os: string
  browser: string
  login_method: number
  created_at: string
  last_seen_at: string | null
  expires_at: string | null
  revoked_at: string | null
  revoke_reason: number | null
  /** Vào từ một IP, dùng tiếp từ IP khác — dấu hiệu token bị mang đi máy khác (BM-003). */
  ip_changed: boolean
}

export interface SystemLogDetail {
  request: SystemLogRequestDetail
  audit: SystemLogAuditEntry[]
  changes: SystemLogChangeEntry[]
  /** `false` = thiếu khóa `change_log`, KHÔNG phải «lượt này không đổi gì». */
  can_read_changes: boolean
  session: SystemLogSessionInfo | null
}

export interface SystemLogSummary {
  /** `hour` là chuỗi `YYYY-MM-DD HH` do backend cắt 13 ký tự đầu. */
  by_hour: { hour: string; total: number; errors: number }[]
  by_route: { route: string; total: number; failed: number }[]
  by_error: { error_code: string; total: number }[]
}

/**
 * Bộ lọc — **danh sách và biểu đồ dùng CHUNG một bộ**, cố ý.
 *
 * Cho biểu đồ ít ô lọc hơn là người dùng lọc bảng rồi đọc biểu đồ toàn hệ mà
 * tưởng là của phần đã lọc. Backend cũng khai đủ mười một ô ở cả hai cửa vì lý
 * do đó — đừng "gọn hóa" một bên.
 */
export interface SystemLogFilters {
  user_id?: number
  doc_code?: string
  route?: string
  ip?: string
  field?: string
  table?: string
  from_time?: string
  to_time?: string
  status?: LogStatus
  action_group?: number
  source?: number
}

export interface SystemLogListParams extends SystemLogFilters {
  page?: number
  page_size?: number
}

export const systemLogApi = {
  list: (params: SystemLogListParams) =>
    apiGet<SystemLogListResult>('/api/system-logs', { params }),

  summary: (params: SystemLogFilters) =>
    apiGet<SystemLogSummary>('/api/system-logs/summary', { params }),

  detail: (requestId: string) =>
    apiGet<SystemLogDetail>(`/api/system-logs/${requestId}`),
}
