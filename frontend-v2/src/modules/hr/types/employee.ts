import { EMPLOYEE_STATUS, labelOf } from '@/shared/constants/statuses'

/** Nhân viên — khớp `EmployeeOut` của backend. */
export interface Employee {
  id: number
  code: string
  full_name: string
  email: string
  phone: string
  company_id: number
  /** Tên pháp nhân, backend trả kèm (`EmployeeOut.company_name`). */
  company_name?: string | null
  department_id: number
  /** Vị trí / chức vụ — CHỈ là chữ, không liên quan tới phân quyền. */
  position: string
  /**
   * ⚠️ Cột cũ, KHÔNG còn dùng để cấp quyền (CR-022). Quyền nay chỉ gán ở màn
   * "Phân quyền tài khoản". Giữ lại vì dữ liệu cũ vẫn còn.
   */
  role_name: string
  /** MÃ tiếng Anh (B-03): `official` | `collaborator` | `maternity_leave` | `resigned`. */
  status: string
  /** Nhãn tiếng Việt của `status`, backend gửi kèm. Rỗng khi mã lạ. */
  status_label: string
  is_active: boolean
  /**
   * NGÀY VÀO LÀM (`YYYY-MM-DD`) — mốc tính THÂM NIÊN, tức số ngày phép cộng
   * thêm. `null` = chưa khai, và lúc đó thâm niên tính bằng **0 năm**: hồ sơ
   * thiếu ô này thì người đó mất phần phép cộng thêm mà không ai báo.
   */
  hire_date?: string | null
  /** `0` chưa khai · `1` nam · `2` nữ. Dùng để lọc loại nghỉ (thai sản). */
  gender: number
  department_name?: string | null
  manager_name?: string | null
  /** Lấy từ tài khoản đăng nhập (`tab_user.avatar`) — nguồn ảnh duy nhất. */
  avatar: string
  /** Ảnh chữ ký, cũng từ tài khoản đăng nhập (`tab_user.signature`). */
  signature: string
  /** Lần sửa gần nhất — cột "Ngày cập nhật" (bao-CR-300, ticket 21). */
  updated_at?: string
}

/** Bản chi tiết — kèm id tài khoản đăng nhập (0 = nhân sự chưa được cấp tài khoản). */
export interface EmployeeDetail extends Employee {
  user_id: number
}

/**
 * Giới tính của HỒ SƠ NHÂN SỰ — khớp `leave/constants.py` (`GENDER_*`).
 *
 * ⚠️ Khác `GENDER_LABELS` ở `types/leave.ts`: bên đó `0` là *«Mọi giới»* vì nó
 * mô tả một LOẠI NGHỈ áp cho ai. Ở đây `0` là *«Chưa khai»* — nó mô tả một con
 * người, và một người thì không thể "mọi giới". Dùng nhầm bảng nhãn là màn hồ sơ
 * hiện «Mọi giới» cho người chưa nhập, đọc ra như đã khai xong.
 */
export const EMPLOYEE_GENDER_OPTIONS = [
  { value: 0, label: 'Chưa khai' },
  { value: 1, label: 'Nam' },
  { value: 2, label: 'Nữ' },
] as const

export function employeeGenderLabel(value?: number | null): string {
  return EMPLOYEE_GENDER_OPTIONS.find((item) => item.value === (value ?? 0))?.label ?? ''
}

/**
 * Tình trạng làm việc — B-03: cột lưu MÃ tiếng Anh, tiếng Việt chỉ còn ở nhãn.
 *
 * Bộ mã sinh từ `backend/app/core/status_codes.py`, KHÔNG khai lại ở đây: khai tay là
 * sớm muộn lệch với bộ backend đang chặn, mà lệch kiểu đó chỉ lộ ra khi người dùng bấm
 * lưu và ăn 422.
 */
export const EMPLOYEE_STATUS_OPTIONS = EMPLOYEE_STATUS.map(({ value, label }) => ({
  value,
  label,
}))

/** Nhãn của một mã tình trạng. Mã lạ thì trả NGUYÊN mã, không trả rỗng. */
export function employeeStatusLabel(value?: string | null): string {
  const v = (value ?? '').trim()
  if (!v) return ''
  return labelOf(EMPLOYEE_STATUS, v) || v
}

/**
 * Options cho ô chọn Tình trạng, kèm giá trị hiện tại nếu nó nằm NGOÀI bộ mã.
 *
 * Giá trị lạ = dòng chưa chạy migration B-03 (hoặc do nơi khác ghi vào). Vẫn phải hiện
 * ra: bỏ đi thì mở form lên ô trống, người dùng không biết hồ sơ đang mang trạng thái
 * gì. Chọn lại đúng nó rồi lưu thì backend trả 422 — cố ý, vì giá trị đó không còn ghi
 * xuống được nữa; câu lỗi nói rõ hơn là im lặng ghi đè.
 */
export function employeeStatusOptions(current?: string | null) {
  const v = (current ?? '').trim()
  if (!v || EMPLOYEE_STATUS_OPTIONS.some((o) => o.value === v)) return EMPLOYEE_STATUS_OPTIONS
  return [{ value: v, label: `${v} (giá trị cũ)` }, ...EMPLOYEE_STATUS_OPTIONS]
}

/**
 * "Trần Minh Được" -> "TĐ". Dùng khi chưa có ảnh đại diện.
 *
 * Bỏ qua các từ không bắt đầu bằng chữ cái: nhiều tên trong dữ liệu mẫu kết
 * thúc bằng "(Demo)", lấy thẳng ký tự đầu của từ cuối sẽ ra dấu ngoặc đơn.
 */
export function employeeInitials(fullName: string): string {
  const words = (fullName || '')
    .trim()
    .split(/\s+/)
    .filter((word) => /^\p{L}/u.test(word))

  const first = words.at(0)?.[0] ?? ''
  const last = words.length > 1 ? (words.at(-1)?.[0] ?? '') : ''
  return (first + last).toUpperCase() || '?'
}
