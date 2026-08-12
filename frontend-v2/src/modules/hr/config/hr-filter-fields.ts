import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { EMPLOYEE_STATUSES } from '../types/employee'

/**
 * Khai báo trường cho BỘ LỌC NÂNG CAO của từng bảng trong phân hệ Nhân sự.
 *
 * ⚠️ `name` PHẢI nằm trong whitelist `FILTERABLE` của controller tương ứng,
 * nếu không backend im lặng bỏ qua điều kiện và người dùng tưởng bộ lọc hỏng:
 *
 *   employee   -> code, full_name, email, position, status, department_id, is_active, role_names
 *   department -> code, name, is_active
 *   company    -> code, name, tax_code, is_active
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
    options: EMPLOYEE_STATUSES.map((status) => ({ label: status, value: status })),
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
  { name: 'tax_code', label: 'Mã số thuế', type: 'text' },
  {
    name: 'is_active',
    label: 'Đang dùng',
    type: 'boolean',
    operators: [...ACTIVE_OPERATORS],
  },
]
