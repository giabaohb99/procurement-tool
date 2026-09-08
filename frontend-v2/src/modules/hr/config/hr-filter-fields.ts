import { apiGet } from '@/core/api'
import type { FilterFieldDefinition, SelectOption } from '@/shared/conditional-filter'
import type { PaginatedResult } from '@/shared/types/api'
import { EMPLOYEE_STATUS_OPTIONS } from '../types/employee'
import type { JobPosition } from '../types/job-position'
import {
  EMPLOYMENT_TYPE_FILTER_OPTIONS,
  JOB_LEVEL_FILTER_OPTIONS,
} from '../types/employee-codes'

/**
 * Khai báo trường cho BỘ LỌC NÂNG CAO của từng bảng trong phân hệ Nhân sự.
 *
 * ⚠️ `name` PHẢI nằm trong whitelist `FILTERABLE` của controller tương ứng,
 * nếu không backend im lặng bỏ qua điều kiện và người dùng tưởng bộ lọc hỏng:
 *
 *   employee   -> code, full_name, email, position, position_id, status, department_id,
 *                 is_active, role_names
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

/** Danh mục Chức vụ cho ô lọc — chỉ dòng đang dùng, giống ô chọn trên hồ sơ. */
async function jobPositionOptions(search: string): Promise<SelectOption[]> {
  const res = await apiGet<PaginatedResult<JobPosition>>('/api/job-positions', {
    //  Sắp theo TÊN như ô chọn trên hồ sơ (`use-job-positions.ts`): mặc định
    //  của backend là `id desc`, tức thứ tự người ta gõ vào — cùng một danh
    //  sách đổi chỗ mỗi lần có ai thêm một chức vụ.
    params: { name: search, is_active: true, page_size: 50, sort_by: 'name', sort_dir: 'asc' },
  })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

export const EMPLOYEE_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã NV', type: 'text' },
  { name: 'full_name', label: 'Họ tên', type: 'text' },
  { name: 'email', label: 'Email', type: 'text' },
  {
    //  ⚠️ Lọc theo `position_id` (KHÓA), không theo chữ — duoc-CR-320. Lọc bằng
    //  chữ thì đổi tên một chức vụ là mọi bộ lọc đã lưu trượt sạch, và
    //  `contains` còn khớp chuỗi con («Phó phòng» lọt vào kết quả «Trưởng
    //  phòng»). Cùng luật với các ô tham chiếu của màn Văn bản.
    name: 'position_id',
    label: 'Vị trí / Chức vụ',
    type: 'select',
    fetchOptions: jobPositionOptions,
  },
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
  //  ── HRM Đợt 2 (duoc-CR-314) ─────────────────────────────────────────────
  //  ⚠️ Ba tên dưới đây phải có trong `FILTERABLE` của
  //  `backend/app/modules/employee/service.py`, nếu không `apply_filters`
  //  **im lặng bỏ qua** điều kiện: màn hình vẫn ra kết quả, chỉ là không lọc gì,
  //  và người dùng tưởng bộ lọc hỏng chứ không biết là chưa khai.
  {
    name: 'employment_type',
    label: 'Hình thức nhân viên',
    type: 'select',
    operators: ['is', 'is_not', 'in', 'not_in'],
    //  `value` là CHUỖI của con số — cột lưu SMALLINT, và `apply_filters` so
    //  bằng nên gửi nhãn tiếng Việt sẽ ra 0 dòng mà không báo lỗi gì (bẫy CR-118).
    options: EMPLOYMENT_TYPE_FILTER_OPTIONS.map(({ value, label }) => ({
      label,
      value: String(value),
    })),
  },
  {
    name: 'job_level',
    label: 'Cấp bậc',
    type: 'select',
    operators: ['is', 'is_not', 'in', 'not_in'],
    options: JOB_LEVEL_FILTER_OPTIONS.map(({ value, label }) => ({
      label,
      value: String(value),
    })),
  },
  {
    //  Lọc "chưa gán quản lý trực tiếp" = `manager_id is 0` — đúng thứ K5 cần
    //  để Nhân sự đi nhập bù, vì bộ máy duyệt dựa vào ô này.
    name: 'manager_id',
    label: 'ID người quản lý trực tiếp',
    type: 'text',
    operators: ['is', 'is_not'],
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
