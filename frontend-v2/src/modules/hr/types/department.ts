/** Phòng ban — khớp `DepartmentOut` của backend. */
export interface Department {
  id: number
  code: string
  name: string
  company_id: number
  /** ID phòng ban cha; 0 = phòng ban gốc. */
  parent: number
  /** Trưởng bộ phận — người duyệt/ký thay mặt phòng trong luồng mua hàng. */
  manager_id: number
  is_active: boolean
  /** Cột join từ hồ sơ nhân sự của `manager_id`. */
  manager_name?: string | null
}
