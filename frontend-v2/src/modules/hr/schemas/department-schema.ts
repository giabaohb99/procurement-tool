import { z } from 'zod'

const ISSUE_CODE_PATTERN = /^[A-Z0-9]*$/

/** Form phòng ban — bám `DepartmentCreate` của backend. */
export const departmentSchema = z.object({
  // Bỏ trống khi tạo mới thì backend tự sinh mã dạng PBA0001.
  code: z.string().trim().max(50, 'Mã tối đa 50 ký tự'),
  name: z.string().trim().min(1, 'Nhập tên phòng ban').max(255, 'Tên tối đa 255 ký tự'),
  issue_code: z
    .string()
    .trim()
    .max(20, 'Mã số hiệu tối đa 20 ký tự')
    .regex(ISSUE_CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu và số'),
  /** 1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án. */
  kind: z.number().int().min(1).max(3),
  company_id: z.number().int().min(0),
  parent: z.number().int().min(0),
  /** Trưởng bộ phận — người duyệt/ký thay mặt phòng. 0 = chưa chỉ định. */
  manager_id: z.number().int().min(0),
  is_active: z.boolean(),
})

export type DepartmentFormValues = z.infer<typeof departmentSchema>

export const EMPTY_DEPARTMENT_FORM: DepartmentFormValues = {
  code: '',
  name: '',
  issue_code: '',
  kind: 1,
  company_id: 0,
  parent: 0,
  manager_id: 0,
  is_active: true,
}
