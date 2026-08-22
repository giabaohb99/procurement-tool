import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { EMPLOYEE_STATUS_OPTIONS } from '../types/employee'

/**
 * Khai báo trường cho BỘ LỌC NÂNG CAO của từng bảng trong phân hệ Nhân sự.
 *
 * ⚠️ `name` PHẢI nằm trong whitelist `FILTERABLE` của controller tương ứng,
 * nếu không backend im lặng bỏ qua điều kiện và người dùng tưởng bộ lọc hỏng:
 *
 *   employee   -> code, full_name, email, position, status, department_id, is_active, role_names
 *   department -> code, name, issue_code, kind, company_id, is_active
 *   company    -> code, name, issue_code, tax_code, level, is_active
 *
 * Các select QUAN TRỌNG (phòng ban, tình trạng, trạng thái) vẫn nằm ngoài thanh
 * công cụ cho thao tác hằng ngày; những trường còn lại gom hết vào đây.
 *
 * Tài khoản đăng nhập (`/api/users`) KHÔNG có mặt ở đây: endpoint đó tự xử lý
 * tham số riêng (`search`, `department`, `role_id`, `no_role`, `orphan`) và
 * không chạy qua `apply_filters`, nên cú pháp `<field>__<op>` vô tác dụng.
 */

const ACTIVE_OPERATORS = ['is'] as const

export const EMPLOYEE_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã NV', type: 'text' },
  { name: 'full_name', label: 'Họ tên', type: 'text' },
  { name: 'email', label: 'Email', type: 'text' },
  { name: 'position', label: 'Vị trí / Chức vụ', type: 'text' },
  {
    name: 'status',
    label: 'Tình trạng làm việc',
    type: 'select',
    // Thêm in/not_in để lọc kiểu "Chính thức HOẶC Cộng tác viên" trong một dòng.
    operators: ['is', 'is_not', 'in', 'not_in', 'is_empty', 'is_not_empty'],
    // B-03: `value` phải là MÃ vì cột đã lưu mã. Gửi nhãn thì backend vẫn nhận câu lọc,
    // chỉ là trả về 0 dòng mà không báo lỗi gì — đúng bẫy CR-118 đã dính một lần.
    options: EMPLOYEE_STATUS_OPTIONS.map(({ value, label }) => ({ label, value })),
  },
  {
    name: 'is_active',
    label: 'Hồ sơ đang dùng',
    type: 'boolean',
    operators: [...ACTIVE_OPERATORS],
  },
]

export const DEPARTMENT_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã phòng ban', type: 'text' },
  { name: 'name', label: 'Tên phòng ban', type: 'text' },
  { name: 'issue_code', label: 'Mã số hiệu', type: 'text' },
  {
    name: 'kind',
    label: 'Loại đơn vị',
    type: 'select',
    options: [
      { label: 'Phòng chức năng', value: '1' },
      { label: 'Đơn vị kinh doanh / sản xuất', value: '2' },
      { label: 'Ban dự án', value: '3' },
    ],
  },
  {
    name: 'is_active',
    label: 'Đang hoạt động',
    type: 'boolean',
    operators: [...ACTIVE_OPERATORS],
  },
]

export const COMPANY_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã công ty', type: 'text' },
  { name: 'name', label: 'Tên pháp nhân', type: 'text' },
  { name: 'issue_code', label: 'Mã số hiệu', type: 'text' },
  { name: 'tax_code', label: 'Mã số thuế', type: 'text' },
  {
    name: 'level',
    label: 'Cấp pháp nhân',
    type: 'select',
    options: [
      { label: 'Tập đoàn', value: '1' },
      { label: 'Công ty thành viên', value: '2' },
      { label: 'Đơn vị trực thuộc', value: '3' },
    ],
  },
  {
    name: 'is_active',
    label: 'Đang dùng',
    type: 'boolean',
    operators: [...ACTIVE_OPERATORS],
  },
]
