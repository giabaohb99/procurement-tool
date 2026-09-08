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
  /** NHÃN chức vụ — backend chép từ danh mục, chỉ để hiển thị/in. */
  position: string
  /**
   * KHÓA chức vụ trong `tab_job_position`; `0` = chưa gán (duoc-CR-320).
   *
   * Để TÙY CHỌN như mọi cột thêm sau: bản ghi cũ trong bộ test (và mọi câu trả
   * lời API dựng trước cột này) không có khóa đó, và bắt buộc thì mọi chỗ dựng
   * một `Employee` giả đều phải nhớ thêm một số 0 vô nghĩa.
   */
  position_id?: number
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

  // ── HỒ SƠ MỞ RỘNG (duoc-CR-314, 08/09/2026) ────────────────────────────────
  //  ⚠️ 15 trường trong nhóm này bị backend CHE ở tầng serializer khi người xem
  //  không có `employee_sensitive.read` — chúng về `''` / `null`, y như chưa
  //  nhập. Không có cách nào phân biệt từ đây, và đó là chủ ý: người không có
  //  quyền không cần biết ô đó có dữ liệu hay không. Muốn nói với người dùng
  //  «bạn không được xem» thì hỏi `can('employee_sensitive', 'read')` rồi đổi
  //  câu chữ, ĐỪNG suy từ giá trị rỗng.

  // Nhóm 1 — cá nhân
  /** NHẠY CẢM. `YYYY-MM-DD` hoặc `null`. */
  date_of_birth?: string | null
  place_of_birth?: string
  ethnicity?: string
  religion?: string
  marital_status?: number
  marital_status_label?: string
  children_count?: number
  /** Email CÁ NHÂN — KHÁC `email` (email công việc, cũng là tên đăng nhập). */
  personal_email?: string
  /** NHẠY CẢM. Mã số thuế cá nhân. */
  tax_code?: string
  education_level?: number
  education_level_label?: string
  major?: string

  // Nhóm 2 — công việc
  /**
   * NGƯỜI QUẢN LÝ TRỰC TIẾP. `0` = chưa gán.
   *
   * ⚠️ Không phải trường hiển thị cho đẹp — đây là dữ liệu mà vai tương đối
   * «người quản lý trực tiếp» của bộ máy duyệt đọc để tìm người ký. Sai ô này
   * thì đơn từ chạy sai đường mà không màn nào báo.
   */
  manager_id?: number
  /**
   * Tên người quản lý trực tiếp, backend trả kèm.
   *
   * ⚠️ ĐỪNG lẫn với `manager_name` phía trên — cái đó là trưởng PHÒNG BAN, đọc
   * qua `department.manager`. Hai người này thường khác nhau.
   */
  direct_manager_name?: string
  employment_type?: number
  employment_type_label?: string
  job_level?: number
  job_level_label?: string
  work_location?: string
  resign_date?: string | null

  // Nhóm 3 — liên hệ (cả hai NHẠY CẢM)
  permanent_address?: string
  current_address?: string

  // Nhóm 4 — ngân hàng (toàn bộ NHẠY CẢM)
  bank_account_no?: string
  bank_account_name?: string
  bank_name?: string
  bank_branch?: string

  // Nhóm 5 — giấy tờ và BHXH/BHYT
  /** NHẠY CẢM. */
  id_number?: string
  /** NHẠY CẢM. */
  id_issue_date?: string | null
  /** NHẠY CẢM. */
  id_issue_place?: string
  /** NHẠY CẢM. */
  id_expiry_date?: string | null
  /** NHẠY CẢM. Đặt qua cửa upload riêng, KHÔNG gửi kèm form. */
  id_front_image?: string
  /** NHẠY CẢM. Đặt qua cửa upload riêng, KHÔNG gửi kèm form. */
  id_back_image?: string
  /** NHẠY CẢM. */
  social_insurance_no?: string
  /** Nơi khám chữa bệnh BHYT — CỐ Ý không nằm trong nhóm nhạy cảm. */
  health_care_place?: string
  health_care_code?: string

  // Nhóm 7 — tùy biến
  extra_fields?: Record<string, unknown>
}

/** Bản chi tiết — kèm id tài khoản đăng nhập (0 = nhân sự chưa được cấp tài khoản). */
export interface EmployeeDetail extends Employee {
  user_id: number
}

/** Người báo tin trong trường hợp cần thiết — `tab_employee_contact`. */
export interface EmployeeContact {
  id: number
  full_name: string
  /**
   * MÃ SỐ quan hệ với NHÂN VIÊN — xem `RELATION_OPTIONS`.
   *
   * Từng là chữ tự do; khách chốt thành ô CHỌN 08/09/2026 vì mỗi người gõ một
   * kiểu («vợ» · «Vợ» · «v/c») nên không lọc được, không đếm được.
   */
  relation: number
  address: string
  phone: string
  sort_order: number
}

/** Thành viên hộ gia đình — `tab_employee_family`, phục vụ kê khai BHXH. */
export interface EmployeeFamily {
  id: number
  full_name: string
  /** MÃ SỐ quan hệ với CHỦ HỘ (không phải với nhân viên) — hồ sơ BHXH hỏi vậy. */
  relation: number
  /** Cùng quy ước `Employee.gender`: 0 chưa khai · 1 nam · 2 nữ. */
  gender: number
  date_of_birth: string | null
  phone: string
  id_number: string
  sort_order: number
}

/**
 * Giới tính của HỒ SƠ NHÂN SỰ — khớp `leave/constants.py` (`GENDER_*`).
 *
 * ⚠️ Khác `GENDER_LABELS` ở `types/leave.ts` ở HAI chỗ:
 * · bên đó `0` là *«Mọi giới»* vì nó mô tả một LOẠI NGHỈ áp cho ai; ở đây `0` là
 *   *«Chưa khai»* — nó mô tả một con người, và một người thì không thể "mọi
 *   giới". Dùng nhầm bảng nhãn là màn hồ sơ hiện «Mọi giới» cho người chưa nhập,
 *   đọc ra như đã khai xong.
 * · bên đó KHÔNG có `3` («Khác»): loại nghỉ "chỉ dành cho giới Khác" không có
 *   nghĩa. Mã `3` chỉ sống trong hồ sơ con người (08/09/2026).
 */
export const EMPLOYEE_GENDER_OPTIONS = [
  { value: 0, label: 'Chưa khai' },
  { value: 1, label: 'Nam' },
  { value: 2, label: 'Nữ' },
  { value: 3, label: 'Khác' },
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
