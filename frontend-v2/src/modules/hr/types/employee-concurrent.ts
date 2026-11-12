import { CONCURRENT_STATUS } from '@/shared/constants/statuses'

/**
 * KIÊM NHIỆM — `tab_employee_concurrent` (duoc-CR-755). Khớp `ConcurrentOut` của
 * `backend/app/modules/employee/concurrent_schema.py`.
 *
 * Một dòng = một (phòng, công ty) người này phụ trách THÊM ngoài vị trí chính, có ngày
 * hiệu lực, quyết định và công tắc "Tính vào phạm vi quyền". Công ty có thể KHÁC công ty
 * chính của hồ sơ.
 */
export interface EmployeeConcurrent {
  id: number
  employee_id: number
  company_id: number
  company_name: string
  department_id: number
  department_name: string
  /** `0` = chưa gán chức vụ. */
  position_id: number
  /** Nhãn chức vụ CHỤP lúc lưu dòng. */
  position_label: string
  /** Chỉ dòng chép từ dữ liệu cũ mới để trống (coi như đã hiệu lực từ trước). */
  from_date: string | null
  to_date: string | null
  decision_no: string
  decision_date: string | null
  note: string
  /** Bật = dòng còn hiệu lực mở phạm vi dữ liệu đúng cặp (phòng, công ty) theo vai trò đang có. */
  counts_scope: boolean
  /** `> 0` = dòng sinh ra từ nút Áp của một dòng quá trình công tác loại Kiêm nhiệm. */
  work_history_id: number
  /** Mã DẪN XUẤT `ConcurrentStatus` (1 Sắp tới · 2 Đang hiệu lực · 3 Đã hết), không phải cột lưu. */
  status: number
  status_label: string
  /** Luôn trả kể cả khi `can_open_files = false` — chỉ là SỐ, không lộ tên tệp. */
  file_count: number
}

/** Trả về của `GET /api/employees/{eid}/concurrents`. */
export interface EmployeeConcurrentListResult {
  items: EmployeeConcurrent[]
  /** Backend tính: có `employee.write` đúng phạm vi VÀ không phải hồ sơ của chính mình (L1, kể cả quản trị). */
  can_edit: boolean
  /** = quyền xem nhạy cảm của hồ sơ này (đã gồm chính chủ). */
  can_open_files: boolean
}

/**
 * Thân `POST` / `PATCH` — khớp `ConcurrentIn` / `ConcurrentPatch` (`extra="forbid"`).
 * `to_date` / `decision_date` bỏ trống gửi `null`, không gửi chuỗi rỗng.
 */
export interface EmployeeConcurrentPayload {
  company_id: number
  department_id: number
  position_id: number
  from_date: string
  to_date: string | null
  decision_no: string
  decision_date: string | null
  note: string
  counts_scope: boolean
}

/**
 * Mã trạng thái dẫn xuất (`backend/app/core/hr_concurrent_codes.py::ConcurrentStatus`), LẤY từ bộ mã sinh sẵn
 * `CONCURRENT_STATUS` (`shared/constants/statuses.ts`, do `gen_status_ts.py` sinh) theo thứ tự khai: Sắp tới,
 * Đang hiệu lực, Đã hết — backend đổi số thì bản sinh đổi theo, không còn số gõ tay. Bài kiểm canh khớp nhãn.
 */
const [CONCURRENT_UPCOMING_CODE, CONCURRENT_ACTIVE_CODE, CONCURRENT_ENDED_CODE] = CONCURRENT_STATUS.map(
  (option) => Number(option.value),
)
export const CONCURRENT_UPCOMING = CONCURRENT_UPCOMING_CODE
export const CONCURRENT_ACTIVE = CONCURRENT_ACTIVE_CODE
export const CONCURRENT_ENDED = CONCURRENT_ENDED_CODE
