import { apiGet } from '@/core/api'

/**
 * NHẬT KÝ EMAIL — `/api/email-logs` (bao-CR-721). CHỈ ĐỌC.
 *
 * Một dòng = một thư hệ đã (định) gửi: sự kiện (mẫu email nào), người nhận, tiêu đề,
 * trạng thái, câu lỗi nguyên văn của máy chủ thư, hộp thư gửi danh nghĩa. Màn này trả
 * lời câu "đã gửi thư cho ai chưa, lỗi gì" — trước đó bảng có hơn 6.000 dòng mà không
 * ai đọc được.
 *
 * ⚠️ Mọi nhãn (sự kiện, trạng thái) do BACKEND trả kèm (`*_label`, `fetchEmailLogMeta`).
 * Thêm mẫu email mới ở `email_template_service.DEFAULTS` là ô lọc tự có.
 *
 * Không có gửi lại: thư lỗi thì sửa cấu hình / hộp thư rồi để luồng nghiệp vụ gửi lại,
 * không gửi tay từ nhật ký.
 */

/** Trạng thái là CHUỖI cũ của cột, không đổi (`pending` / `sent` / `failed` / `disabled`). */
export const EMAIL_LOG_STATUS = {
  PENDING: 'pending',
  SENT: 'sent',
  FAILED: 'failed',
  DISABLED: 'disabled',
} as const

export interface EmailLogItem {
  id: number
  event: string
  event_label: string
  to_email: string
  subject: string
  status: string
  status_label: string
  /** Nguyên văn câu lỗi của máy chủ thư — danh sách trả đủ, không cắt. */
  error: string
  sent_at: string | null
  mailbox_id: number | null
  from_email: string
  created_at: string
  created_by: number
}

export interface EmailLogListResult {
  total: number
  items: EmailLogItem[]
  page: number
  page_size: number
}

export interface EmailLogOption {
  code: string
  label: string
}

export interface EmailLogMeta {
  events: EmailLogOption[]
  statuses: EmailLogOption[]
}

export interface EmailLogStats {
  days: number
  total: number
  failed: number
  sent: number
  pending: number
  by_status: { status: string; label: string; count: number }[]
}

export interface EmailLogFilters {
  /** Người nhận chứa chuỗi này. */
  q?: string
  /** Nhiều sự kiện một lượt. */
  event?: string[]
  status?: string
  from_date?: string
  to_date?: string
  page?: number
  page_size?: number
}

const BASE_URL = '/api/email-logs'

/**
 * `event` lặp nhiều lần trên query (`?event=a&event=b`) — FastAPI đọc `list[str]`;
 * axios mặc định ghi `event[]=a` nên tự ghép chuỗi ở đây.
 */
function buildQuery(filters: EmailLogFilters): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === '' || value === null) continue
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((v) => params.append(key, v))
    } else {
      params.set(key, String(value))
    }
  }
  const text = params.toString()
  return text ? `?${text}` : ''
}

export function fetchEmailLogs(filters: EmailLogFilters) {
  return apiGet<EmailLogListResult>(`${BASE_URL}${buildQuery(filters)}`)
}

export function fetchEmailLogDetail(id: number) {
  return apiGet<EmailLogItem>(`${BASE_URL}/${id}`)
}

export function fetchEmailLogMeta() {
  return apiGet<EmailLogMeta>(`${BASE_URL}/meta`)
}

export function fetchEmailLogStats(days: number) {
  return apiGet<EmailLogStats>(`${BASE_URL}/stats?days=${days}`)
}
