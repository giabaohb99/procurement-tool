/**
 * Quá trình công tác / Quyết định bổ nhiệm — `tab_employee_work_history`
 * (kế hoạch `261003-0837-qua-trinh-lam-viec-nhan-su`, phase 02 + 04).
 *
 * Lịch sử ghi tay THEO NGƯỜI: tuyển dụng, điều chuyển, bổ nhiệm, kiêm nhiệm,
 * miễn nhiệm, thôi việc. Khớp `WorkHistoryOut` của backend.
 */
export interface EmployeeWorkHistory {
  id: number
  employee_id: number
  /** Mã số — tra nhãn bằng `labelOf(WORK_EVENT_TYPE, String(event_type))`. */
  event_type: number
  /** Ngày HIỆU LỰC (Q1 — gộp với "ngày hiệu lực", khác `decision_date` là ngày ký QĐ). */
  from_date: string
  to_date: string | null
  company_id: number
  company_name: string
  department_id: number
  department_name: string
  /** `0` = chưa gán chức vụ ở dòng này. */
  position_id: number
  /** NHÃN chức vụ tại thời điểm ghi dòng — khác chức vụ hiện tại của hồ sơ. */
  position_label: string
  decision_no: string
  decision_date: string | null
  note: string
  /** `null` = dòng chưa áp vào hồ sơ. */
  applied_at: string | null
  /** Luôn trả kể cả khi `can_open_files=false` (Q4) — chỉ là SỐ, không lộ tên tệp. */
  file_count: number
  /** `to_date is None or to_date >= hôm nay VN`. */
  is_current: boolean
  /** Loại ∈ `APPLICABLE` và qua các chốt áp — KHÔNG xét quyền (xem `can_edit` riêng). */
  can_apply: boolean
}

/** Trả về của hai đường đọc danh sách (`/{eid}/work-history` và `/me/work-history`). */
export interface EmployeeWorkHistoryListResult {
  items: EmployeeWorkHistory[]
  /** A9 — BACKEND tính: có `employee.write` (scope write) VÀ không phải hồ sơ của
   *  chính mình (trừ `is_system_admin`). FE không tự ghép lại luật này. */
  can_edit: boolean
  /** A9 — `can_read_sensitive(profile, eid)`, đã gồm chính chủ. */
  can_open_files: boolean
}

/** Trả về của POST/PATCH một dòng — kèm cảnh báo không chặn và các thay đổi đã áp. */
export interface EmployeeWorkHistorySaveResult {
  item: EmployeeWorkHistory
  warnings: string[]
  applied_changes: string[]
}

/** Trả về của `/apply`. */
export interface EmployeeWorkHistoryApplyResult {
  item: EmployeeWorkHistory
  applied_changes: string[]
}

/**
 * Payload gửi lên `POST`/`PATCH` — khớp `WorkHistoryIn` (`extra="forbid"`).
 *
 * `to_date` / `decision_date` là `null` khi bỏ trống, KHÔNG gửi chuỗi rỗng —
 * cùng quy ước với `employee-api.ts::toEmployeePayload` cho các cột `DATE NULL`.
 */
export interface EmployeeWorkHistoryPayload {
  event_type: number
  from_date: string
  to_date: string | null
  company_id: number
  department_id: number
  position_id: number
  decision_no: string
  decision_date: string | null
  note: string
  close_open_main?: boolean
  apply_to_profile?: boolean
}

/** Một liên kết tệp đính kèm của dòng quá trình công tác — khớp `_link_out`. */
export interface WorkHistoryFile {
  /** ID của LIÊN KẾT, không phải của tệp. */
  id: number
  file_id: number
  filename: string
  /** ⚠️ LUÔN RỖNG — `employee_work_history` là entity RIÊNG TƯ (A6). Xem qua `/view`, tải qua `/download`. */
  url: string
  content_type: string
  size: number
}
