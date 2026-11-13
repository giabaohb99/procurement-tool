import { CONCURRENT_KIND, CONCURRENT_STATUS } from '@/shared/constants/statuses'

/**
 * KIÊM NHIỆM — `tab_employee_concurrent` (duoc-CR-755; hai loại dòng ở duoc-CR-756). Khớp `ConcurrentOut` của
 * `backend/app/modules/employee/concurrent_schema.py`.
 *
 * Một dòng là MỘT trong hai loại độc lập (`kind`):
 * - **Phòng ban**: một phòng của CHÍNH công ty hiện tại của hồ sơ (`company_id` = công ty chính lúc ghi, máy chủ điền);
 * - **Công ty**: cả một công ty KHÁC công ty hiện tại (`department_id = 0`, `department_name = ""`) — người này được
 *   tính như người của công ty đó theo bậc vai trò.
 * Mỗi dòng có ngày hiệu lực, quyết định và công tắc "Tính vào phạm vi quyền".
 */
export interface EmployeeConcurrent {
  id: number
  employee_id: number
  /** Mã `ConcurrentKind` (sinh ở `CONCURRENT_KIND`): Phòng ban hoặc Công ty. Không đổi được sau khi tạo. */
  kind: number
  kind_label: string
  company_id: number
  company_name: string
  /** Loại Công ty: luôn `0`. */
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
  /** Bật = dòng còn hiệu lực mở phạm vi: loại Phòng ban thêm phòng đó, loại Công ty thêm công ty đó (theo bậc vai trò). */
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

/** Phần chung của thân `POST` / `PATCH`. `to_date` / `decision_date` bỏ trống gửi `null`, không gửi chuỗi rỗng. */
interface EmployeeConcurrentPayloadBase {
  position_id: number
  from_date: string
  to_date: string | null
  decision_no: string
  decision_date: string | null
  note: string
  counts_scope: boolean
}

/**
 * Nơi kiêm nhiệm — ĐÚNG MỘT ô theo loại. Backend `extra="forbid"`: loại Phòng ban gửi `company_id` (kể cả số 0 ở PATCH)
 * hay loại Công ty gửi `department_id` là 422/400, nên kiểu cấm luôn ô của loại kia.
 */
type EmployeeConcurrentPlace =
  | { department_id: number; company_id?: never }
  | { company_id: number; department_id?: never }

/** Thân `PATCH .../concurrents/{id}` — khớp `ConcurrentPatch`: KHÔNG có `kind` (đổi loại = xóa rồi thêm). */
export type EmployeeConcurrentUpdatePayload = EmployeeConcurrentPayloadBase & EmployeeConcurrentPlace

/** Thân `POST .../concurrents` — khớp `ConcurrentIn`: `kind` bắt buộc, kèm đúng ô nơi kiêm nhiệm của loại đó. */
export type EmployeeConcurrentCreatePayload = EmployeeConcurrentUpdatePayload & { kind: number }

/**
 * Mã loại (`backend/app/core/hr_concurrent_codes.py::ConcurrentKind`), LẤY từ bộ mã sinh sẵn `CONCURRENT_KIND` theo
 * thứ tự khai: Phòng ban, Công ty. Bài kiểm canh khớp nhãn.
 */
const [CONCURRENT_KIND_DEPARTMENT_CODE, CONCURRENT_KIND_COMPANY_CODE] = CONCURRENT_KIND.map((option) =>
  Number(option.value),
)
export const CONCURRENT_KIND_DEPARTMENT = CONCURRENT_KIND_DEPARTMENT_CODE
export const CONCURRENT_KIND_COMPANY = CONCURRENT_KIND_COMPANY_CODE

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
