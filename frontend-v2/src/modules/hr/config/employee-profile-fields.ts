import { EMPLOYEE_GENDER_OPTIONS } from '../types/employee'
import {
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  JOB_LEVEL_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  codeLabel,
  type CodeOption,
} from '../types/employee-codes'
import type { ChangeRequestGroup } from '../types/employee-change-request'
import { formatDate } from '@/shared/utils/format-date'

/**
 * SỔ TRƯỜNG HỒ SƠ NHÂN SỰ dùng chung cho ba nơi của duoc-CR-676: hộp "Đề nghị sửa thông tin"
 * (Trang cá nhân), màn duyệt của phòng Nhân sự (bảng so sánh) và bản in Phiếu thông tin nhân
 * viên BM00../QT01/NS. Một chỗ khai nhãn + kiểu → ba màn gọi cùng một tên cho cùng một ô.
 *
 * Nhãn lấy đúng chữ của màn chi tiết nhân sự (`employee-tab-*.tsx`); ba ô CCCD thêm đuôi
 * "CCCD" vì trong bảng so sánh chúng đứng lẫn với ô khác, "Ngày cấp" trơn thì không biết cấp gì.
 *
 * `maxLength` khớp bí danh `StrNN` của `backend/.../employee/field_limits.py` (đi qua
 * `change_request_schema.py`): chặn ngay ở ô, khỏi ăn 422 tiếng Anh lúc gửi.
 */

export type EmployeeFieldKind = 'text' | 'date' | 'number' | 'code'

export interface EmployeeFieldDef {
  label: string
  kind: EmployeeFieldKind
  /** Bộ mã của ô CHỌN (`kind: 'code'`). */
  options?: readonly CodeOption[]
  maxLength?: number
  inputType?: 'text' | 'email'
}

export const EMPLOYEE_FIELD_DEFS = {
  // Nhóm 1 — cá nhân
  full_name: { label: 'Họ và tên', kind: 'text' },
  gender: { label: 'Giới tính', kind: 'code', options: EMPLOYEE_GENDER_OPTIONS },
  date_of_birth: { label: 'Ngày sinh', kind: 'date' },
  place_of_birth: { label: 'Nơi sinh', kind: 'text', maxLength: 255 },
  ethnicity: { label: 'Dân tộc', kind: 'text', maxLength: 50 },
  religion: { label: 'Tôn giáo', kind: 'text', maxLength: 50 },
  marital_status: { label: 'Tình trạng hôn nhân', kind: 'code', options: MARITAL_STATUS_OPTIONS },
  children_count: { label: 'Số con', kind: 'number' },
  personal_email: { label: 'Email cá nhân', kind: 'text', maxLength: 255, inputType: 'email' },
  education_level: { label: 'Trình độ học vấn', kind: 'code', options: EDUCATION_LEVEL_OPTIONS },
  major: { label: 'Chuyên ngành', kind: 'text', maxLength: 255 },
  // Nhóm 2 — công việc (chỉ in, không tự khai)
  code: { label: 'Mã nhân viên', kind: 'text' },
  company_name: { label: 'Pháp nhân', kind: 'text' },
  department_name: { label: 'Phòng ban', kind: 'text' },
  position: { label: 'Chức vụ', kind: 'text' },
  direct_manager_name: { label: 'Quản lý trực tiếp', kind: 'text' },
  employment_type: { label: 'Hình thức nhân viên', kind: 'code', options: EMPLOYMENT_TYPE_OPTIONS },
  job_level: { label: 'Cấp bậc', kind: 'code', options: JOB_LEVEL_OPTIONS },
  work_location: { label: 'Nơi làm việc', kind: 'text' },
  hire_date: { label: 'Ngày vào làm', kind: 'date' },
  email: { label: 'Email công việc', kind: 'text' },
  // Nhóm 3 — liên hệ (tự sửa ngay ở thẻ "Liên hệ", không qua đề nghị)
  phone: { label: 'Số điện thoại', kind: 'text' },
  permanent_address: { label: 'Địa chỉ thường trú', kind: 'text' },
  current_address: { label: 'Địa chỉ hiện nay (tạm trú)', kind: 'text' },
  // Nhóm 4 — ngân hàng
  bank_account_no: { label: 'Số tài khoản', kind: 'text', maxLength: 50 },
  bank_account_name: { label: 'Tên chủ tài khoản', kind: 'text', maxLength: 255 },
  bank_name: { label: 'Ngân hàng', kind: 'text', maxLength: 100 },
  bank_branch: { label: 'Chi nhánh', kind: 'text', maxLength: 255 },
  // Nhóm 5 — giấy tờ và BHXH/BHYT
  id_number: { label: 'Số CCCD', kind: 'text', maxLength: 20 },
  id_issue_date: { label: 'Ngày cấp CCCD', kind: 'date' },
  id_issue_place: { label: 'Nơi cấp CCCD', kind: 'text', maxLength: 255 },
  id_expiry_date: { label: 'Ngày hết hạn CCCD', kind: 'date' },
  tax_code: { label: 'Mã số thuế cá nhân', kind: 'text', maxLength: 20 },
  social_insurance_no: { label: 'Số sổ BHXH', kind: 'text', maxLength: 20 },
  health_care_place: { label: 'Nơi đăng ký KCB BHYT', kind: 'text', maxLength: 255 },
  health_care_code: { label: 'Mã nơi KCB BHYT', kind: 'text', maxLength: 20 },
} as const satisfies Record<string, EmployeeFieldDef>

export type EmployeeFieldKey = keyof typeof EMPLOYEE_FIELD_DEFS

/**
 * Ô của từng NHÓM đề nghị — khớp ĐÚNG `PersonalChange` / `BankChange` / `DocumentsChange` của
 * `backend/.../employee/change_request_schema.py` (`extra="forbid"`: gửi thừa một ô là 422 cả
 * lượt). Thêm ô bên đó thì thêm ở đây, và ngược lại.
 */
export const CHANGE_REQUEST_GROUP_FIELDS: Record<ChangeRequestGroup, readonly EmployeeFieldKey[]> = {
  personal: [
    'gender',
    'date_of_birth',
    'place_of_birth',
    'ethnicity',
    'religion',
    'marital_status',
    'children_count',
    'personal_email',
    'education_level',
    'major',
  ],
  bank: ['bank_account_no', 'bank_account_name', 'bank_name', 'bank_branch'],
  documents: [
    'id_number',
    'id_issue_date',
    'id_issue_place',
    'id_expiry_date',
    'tax_code',
    'social_insurance_no',
    'health_care_place',
    'health_care_code',
  ],
}

export const CHANGE_REQUEST_GROUP_LABELS: Record<ChangeRequestGroup | 'families', string> = {
  personal: 'Cá nhân',
  bank: 'Ngân hàng',
  documents: 'Giấy tờ',
  families: 'Hộ gia đình',
}

/** Câu thay giá trị bị che — backend trả `null` + `masked: true` khi người xem thiếu quyền nhạy cảm. */
export const MASKED_VALUE_TEXT = 'Đã ẩn (cần quyền xem thông tin nhạy cảm)'

/** Nhãn của một ô; khóa lạ (backend thêm ô mà bên này chưa biết) thì trả nguyên tên khóa. */
export function getEmployeeFieldLabel(field: string): string {
  return (EMPLOYEE_FIELD_DEFS as Record<string, EmployeeFieldDef>)[field]?.label ?? field
}

/**
 * Giá trị một ô → chữ để HIỂN THỊ / IN.
 *
 * ⚠️ `null` / `undefined` / mã `0` của ô chọn đều ra chuỗi RỖNG, không bao giờ ra chữ "null"
 * hay "Chưa khai" — ô bị che (thiếu quyền nhạy cảm) và ô chưa nhập đều phải in thành ô trống.
 * Số con `0` là câu trả lời THẬT nên giữ "0".
 */
export function formatEmployeeFieldValue(field: string, value: unknown): string {
  if (value === null || value === undefined) return ''
  const def = (EMPLOYEE_FIELD_DEFS as Record<string, EmployeeFieldDef>)[field]
  if (!def) return String(value)
  switch (def.kind) {
    case 'date':
      return typeof value === 'string' && value ? formatDate(value) : ''
    case 'code': {
      const code = Number(value)
      if (!code) return ''
      return codeLabel(def.options ?? [], code) || String(value)
    }
    case 'number':
      return String(value)
    default:
      return String(value)
  }
}
