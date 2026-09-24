import { apiGet, apiPost } from '@/core/api'

/**
 * SỔ ĐỒNG BỘ — `/api/sync-logs` (bao-CR-449, P4 của đồng bộ app đặt xe cũ).
 *
 * Một bảng `tab_sync_log` cho MỌI hệ ngoài (app đặt xe & duyệt dấu cũ, POS365,
 * sau này là đồng bộ đơn hàng) và cho CẢ HAI hạt dữ liệu:
 *
 * - `grain = 1` (Lượt chạy) — một vòng chạy nền: con trỏ thời gian, đếm kéo/ghi/bỏ.
 * - `grain = 2` (Bản ghi)   — một phiếu đi qua, trỏ về lượt chạy qua `run_id`.
 *
 * Vì một hình dạng ôm cả hai hạt nên dòng bản ghi để trống mấy ô của lượt chạy
 * (`job`, con trỏ, ba số đếm) và ngược lại. Đừng tách thành hai kiểu: bảng, ô
 * lọc và khóa truy vấn khi đó cũng phải nhân đôi.
 *
 * ⚠️ Đây KHÔNG phải nhật ký hệ thống (`system-log-api.ts`). Màn kia ghi lượt gọi
 * người dùng bấm bên trong ERP; màn này ghi thứ hệ ngoài đẩy sang. Một phiếu đặt
 * xe hỏng lúc nhận về không để lại dòng nào bên kia.
 *
 * ⚠️ Mọi nhãn (nguồn, đối tượng, công việc, cờ cảnh báo) do BACKEND trả kèm —
 * đọc `*_label` hoặc gọi `fetchSyncLogMeta`, đừng chép bảng nhãn sang đây. Thêm
 * một hệ nguồn mới ở `registry.py` là ô lọc tự có, không phải sửa frontend.
 */

/** Hạt dữ liệu của một dòng sổ — khớp `SyncGrain` bên backend. */
export const SYNC_GRAIN = { RUN: 1, RECORD: 2 } as const

/** Chiều dữ liệu so với ERP — khớp `SyncDirection`. */
export const SYNC_DIRECTION = { INBOUND: 1, OUTBOUND: 2 } as const

/**
 * Vòng đời một dòng sổ — khớp `SyncStatus`.
 *
 * Ba mã số dưới đây là chỗ DUY NHẤT frontend được biết con số: chuông 08:00 đi
 * vào màn bằng `?status=4`, ô lọc nhanh «chưa gắn được người» cần biết đâu là
 * lỗi, và thẻ đếm tô màu theo trạng thái. Nhãn thì vẫn lấy từ backend.
 */
export const SYNC_STATUS = {
  PENDING: 1,
  RUNNING: 2,
  SUCCESS: 3,
  FAILED: 4,
  SKIPPED: 5,
} as const

/** Cờ «không tra ra nhân sự» — ô lọc nhanh *Chưa gắn được người* (P4 mục 6). */
export const WARN_NO_EMPLOYEE = 'no_employee'

/** Trạng thái bấm được nút *Chạy lại* — khớp `RETRYABLE_STATUSES` bên backend. */
export const RETRYABLE_SYNC_STATUSES: number[] = [SYNC_STATUS.FAILED, SYNC_STATUS.PENDING]

export interface SyncLogItem {
  id: number
  source: string
  source_label: string
  grain: number
  grain_label: string
  run_id: number
  job: string
  job_label: string
  direction: number
  direction_label: string
  entity: string
  entity_label: string
  action: number
  action_label: string
  legacy_id: string
  local_id: number
  status: number
  status_label: string
  /** NGUYÊN VĂN câu trả lời hoặc câu lỗi của bên kia — không diễn giải lại. */
  message: string
  content_hash: string
  event_id: string
  attempt_count: number
  last_tried_at: string
  finished_at: string
  cursor_from: string
  cursor_to: string
  fetched: number
  written: number
  skipped: number
  warnings: string[]
  warning_labels: string[]
  created_at: string
  updated_at: string
}

/**
 * Chi tiết một dòng, kèm nguyên cục dữ liệu bên kia gửi sang.
 *
 * `payload` là CHUỖI chứ không phải object: lúc hỏng thì cục đó thường không
 * phải JSON hợp lệ, mà chỗ này tồn tại chính là để nhìn thấy thứ đã thật sự
 * nhận được. Backend cố ý không `json.loads` hộ.
 */
export interface SyncLogDetail extends SyncLogItem {
  payload: string
}

export interface SyncLogOption {
  code: string
  label: string
  enabled?: boolean
}

export interface SyncLogCodeOption {
  code: number
  label: string
}

export interface SyncLogMeta {
  sources: SyncLogOption[]
  entities: SyncLogOption[]
  jobs: SyncLogOption[]
  grains: SyncLogCodeOption[]
  directions: SyncLogCodeOption[]
  actions: SyncLogCodeOption[]
  statuses: SyncLogCodeOption[]
  warnings: SyncLogOption[]
}

export interface SyncLogStats {
  days: number
  source: string
  total: number
  by_status: { status: number; label: string; count: number }[]
}

export interface SyncLogFilters {
  source?: string
  grain?: number
  job?: string
  run_id?: number
  entity?: string
  direction?: number
  status?: number
  legacy_id?: string
  local_id?: number
  /** Có cờ nào cũng được — KHÁC `warning` (một cờ cụ thể). */
  only_warning?: boolean
  /** Một cờ cụ thể, vd `no_employee`. Cờ lạ thì backend trả 400. */
  warning?: string
  days?: number
  q?: string
  page?: number
  page_size?: number
}

export interface SyncLogListResult {
  items: SyncLogItem[]
  total: number
  page: number
  page_size: number
}

export function fetchSyncLogs(params: SyncLogFilters) {
  return apiGet<SyncLogListResult>('/api/sync-logs', { params })
}

export function fetchSyncLogMeta() {
  return apiGet<SyncLogMeta>('/api/sync-logs/meta')
}

export function fetchSyncLogStats(params: { source?: string; days?: number }) {
  return apiGet<SyncLogStats>('/api/sync-logs/stats', { params })
}

export function fetchSyncLogDetail(id: number) {
  return apiGet<SyncLogDetail>(`/api/sync-logs/${id}`)
}

/**
 * Xếp hàng chạy lại MỘT dòng hỏng.
 *
 * Trả về DÒNG MỚI ở trạng thái *chờ*, không sửa dòng cũ (luật §3.2: một dòng =
 * một sự kiện). Người nhặt việc là vòng chạy nền của hệ nguồn, nên gọi xong
 * đừng chờ thấy kết quả ngay — dòng chờ sẽ đổi trạng thái ở chu kỳ sau.
 */
export function retrySyncLog(id: number) {
  return apiPost<SyncLogItem>(`/api/sync-logs/${id}/retry`, {})
}
