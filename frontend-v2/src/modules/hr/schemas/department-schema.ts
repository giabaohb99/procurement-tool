import { z } from 'zod'

/** Form phòng ban — bám `DepartmentCreate` của backend. */
export const departmentSchema = z.object({
  // Bỏ trống khi tạo mới thì backend tự sinh mã dạng PBA0001.
  code: z.string().trim().max(50, 'Mã tối đa 50 ký tự'),
  name: z.string().trim().min(1, 'Nhập tên phòng ban').max(255, 'Tên tối đa 255 ký tự'),
  /** Trưởng bộ phận — người duyệt/ký thay mặt phòng. 0 = chưa chỉ định. */
  manager_id: z.number().int().min(0),
  is_active: z.boolean(),
})

export type DepartmentFormValues = z.infer<typeof departmentSchema>

export const EMPTY_DEPARTMENT_FORM: DepartmentFormValues = {
  code: '',
  name: '',
  manager_id: 0,
  is_active: true,
}
