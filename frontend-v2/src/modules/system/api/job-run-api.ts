import { apiGet } from '@/core/api'

/**
 * VIỆC CHẠY NGẦM — `/api/system/jobs` (bao-CR-703).
 *
 * Mỗi dòng là MỘT việc nền theo lịch của Celery beat (sao lưu, dọn nhật ký, gộp trùng hải quan, nhắc việc, thống kê…),
 * kèm lần chạy gần nhất; bấm một việc thì mở lịch sử các lần chạy (`tab_job_run`). Chỉ đọc — đợt này không có nút chạy
 * tay. Gác `setting.read` ở máy chủ.
 *
 * ⚠️ Tên tiếng Việt, mục đích, nhóm, lịch dạng chữ và nhãn trạng thái đều do MÁY CHỦ trả (sổ mô tả việc nền) — đừng chép
 * bảng nhãn sang đây. Thêm một việc nền mới ở máy chủ là màn tự có dòng mới.
 */

/**
 * Trạng thái một lần chạy — khớp IntEnum bên máy chủ. Frontend chỉ cần biết con số để TÔ MÀU và để biết lần nào còn
 * đang chạy; nhãn luôn đọc `status_label`.
 */
export const JOB_RUN_STATUS = {
  RUNNING: 1,
  SUCCESS: 2,
  FAILED: 3,
  SKIPPED: 4,
} as const

/** Một lần chạy của một việc nền. */
export interface JobRun {
  id: number
  job_code: string
  started_at: string
  /** `null` khi còn đang chạy (hoặc tiến trình chết giữa chừng, không ghi được giờ xong). */
  finished_at: string | null
  duration_ms: number | null
  status: number
  status_label: string
  /** Kết quả tóm tắt một dòng, vd "xóa 1.204 dòng nhật ký". */
  summary: string
  /** Câu lỗi / dòng cuối traceback; rỗng khi thành công. */
  error: string
}

/** Một việc nền theo lịch. */
export interface JobItem {
  /** Tên task Celery — khóa ổn định, dùng làm id dòng và đường lịch sử. */
  code: string
  name: string
  /** Một câu: việc này để làm gì. */
  purpose: string
  group: string
  group_label: string
  /** Lịch viết cho người đọc, vd "02:45 mỗi đêm", "mỗi 15 phút". */
  schedule_label: string
  enabled: boolean
  next_run_at: string | null
  /** `null` = chưa chạy lần nào kể từ khi bắt đầu ghi sổ. */
  last_run: JobRun | null
  avg_duration_ms_7d: number | null
  runs_7d: number
  failed_7d: number
}

export interface JobOption {
  code: string
  label: string
}

export interface JobStatusOption {
  code: number
  label: string
}

export interface JobListResult {
  items: JobItem[]
  groups: JobOption[]
  statuses: JobStatusOption[]
}

/** Giá trị lọc "chưa chạy lần nào" của danh sách việc — máy chủ hiểu `status=0`, không nằm trong `statuses`. */
export const JOB_NEVER_RAN = 0

export interface JobListFilters {
  group?: string
  /** Lọc theo trạng thái LẦN CHẠY GẦN NHẤT; `JOB_NEVER_RAN` (0) = chưa chạy lần nào. */
  status?: number
  /** Tìm theo tên tiếng Việt hoặc mã việc. */
  q?: string
}

export interface JobRunFilters {
  status?: number
  page?: number
  page_size?: number
}

export interface JobRunListResult {
  items: JobRun[]
  total: number
  page: number
  page_size: number
}

export function fetchJobs(params: JobListFilters) {
  return apiGet<JobListResult>('/api/system/jobs', { params })
}

/** `code` là tên task Celery, có dấu chấm (vd `customs.cleanup_row_logs`) — mã hóa để ký tự lạ không vỡ đường. */
export function fetchJobRuns(code: string, params: JobRunFilters) {
  return apiGet<JobRunListResult>(`/api/system/jobs/${encodeURIComponent(code)}/runs`, { params })
}
