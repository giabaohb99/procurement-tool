import type { EmployeeFieldKey } from './employee-profile-fields'

/**
 * BỐ CỤC bản in "Phiếu thông tin nhân viên" BM00../QT01/NS (C5 của `doc/erp/hrm/01-ho-so-nhan-su.md`).
 *
 * ⚠️ TỆP MẪU GỐC BM00 CHƯA CÓ trong tay (duoc-CR-676, 23/10/2026) — thứ tự mục và thứ tự ô dưới
 * đây dựng theo bảng trường §2/§3 của tài liệu. Có tệp mẫu thì CHỈ sửa mảng này (đổi chỗ, đổi tên
 * mục, thêm/bớt ô), không phải đụng vào component dựng phiếu. Không có ô lương nào — cố ý.
 *
 * Nhãn của từng ô lấy từ `EMPLOYEE_FIELD_DEFS`, nên in ra cùng tên với màn hồ sơ.
 */

export interface PrintFieldSection {
  kind: 'fields'
  title: string
  fields: readonly EmployeeFieldKey[]
}

export interface PrintPeopleSection {
  /** `contacts` = người báo tin (bắt buộc trên phiếu); `families` = hộ gia đình (kê khai BHXH). */
  kind: 'contacts' | 'families'
  title: string
  /** Ghi chú in nghiêng dưới tiêu đề mục. */
  note?: string
}

export type PrintSection = PrintFieldSection | PrintPeopleSection

export const EMPLOYEE_INFO_PRINT_SECTIONS: readonly PrintSection[] = [
  {
    kind: 'fields',
    title: 'I. THÔNG TIN CÁ NHÂN',
    fields: [
      'full_name',
      'gender',
      'date_of_birth',
      'place_of_birth',
      'ethnicity',
      'religion',
      'marital_status',
      'children_count',
      'education_level',
      'major',
      'personal_email',
    ],
  },
  {
    kind: 'fields',
    title: 'II. CÔNG VIỆC',
    fields: [
      'code',
      'company_name',
      'department_name',
      'position',
      'direct_manager_name',
      'employment_type',
      'job_level',
      'work_location',
      'hire_date',
      'email',
    ],
  },
  {
    kind: 'fields',
    title: 'III. LIÊN HỆ',
    fields: ['phone', 'permanent_address', 'current_address'],
  },
  {
    kind: 'fields',
    title: 'IV. NGÂN HÀNG',
    fields: ['bank_account_no', 'bank_account_name', 'bank_name', 'bank_branch'],
  },
  {
    kind: 'fields',
    title: 'V. GIẤY TỜ VÀ BHXH/BHYT',
    fields: [
      'id_number',
      'id_issue_date',
      'id_issue_place',
      'id_expiry_date',
      'tax_code',
      'social_insurance_no',
      'health_care_place',
      'health_care_code',
    ],
  },
  {
    kind: 'contacts',
    title: 'VI. NGƯỜI BÁO TIN KHI CẦN THIẾT',
    note: '(Bắt buộc khai ít nhất một người)',
  },
  {
    kind: 'families',
    title: 'VII. THÀNH VIÊN HỘ GIA ĐÌNH',
    note: '(Dùng để kê khai BHXH khi ký hợp đồng chính thức; quan hệ ghi theo chủ hộ)',
  },
]

/** Ô ghi địa chỉ / email dài — chiếm trọn một hàng thay vì nửa hàng. */
export const PRINT_WIDE_FIELDS: ReadonlySet<EmployeeFieldKey> = new Set<EmployeeFieldKey>([
  'full_name',
  'permanent_address',
  'current_address',
  'company_name',
  'health_care_place',
  'id_issue_place',
  'place_of_birth',
])

/** Bảng người in tối thiểu ngần này dòng — dòng trống để điền tay khi hồ sơ chưa khai đủ. */
export const PRINT_MIN_PEOPLE_ROWS = 3

/** Mã biểu mẫu và ngày ban hành in ở góc phiếu. */
export const EMPLOYEE_INFO_FORM_CODE = 'BM00../QT01/NS'
export const EMPLOYEE_INFO_FORM_ISSUED = 'Ban hành 01/06/2025'
