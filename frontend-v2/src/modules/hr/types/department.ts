/** Phòng ban — khớp `DepartmentOut` của backend. */
export interface Department {
  id: number
  code: string
  name: string
  /** Mã mặc định đi vào số hiệu; có thể bị ghi đè theo từng pháp nhân. */
  issue_code: string
  /** 1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án. */
  kind: 1 | 2 | 3
  company_id: number
  /** ID phòng ban cha; 0 = phòng ban gốc. */
  parent: number
  /** Trưởng bộ phận — người duyệt/ký thay mặt phòng trong luồng mua hàng. */
  manager_id: number
  is_active: boolean
  /** Cột join từ hồ sơ nhân sự của `manager_id`. */
  manager_name?: string | null
}

export const DEPARTMENT_KIND_LABELS: Record<Department['kind'], string> = {
  1: 'Phòng chức năng',
  2: 'Đơn vị kinh doanh / sản xuất',
  3: 'Ban dự án',
}

const DEPARTMENT_KINDS = [1, 2, 3] as const

/** Đổ vào ô chọn "Loại đơn vị"; dựng TỪ bảng nhãn để hai chỗ không trôi khỏi nhau. */
export const DEPARTMENT_KIND_OPTIONS = DEPARTMENT_KINDS.map((value) => ({
  value,
  label: DEPARTMENT_KIND_LABELS[value],
}))

/**
 * Một CẶP phòng ban × pháp nhân — khớp `GET /api/departments/by-companies`.
 *
 * Một phòng có mặt ở nhiều pháp nhân, nên nơi cần khai "phòng nào ở công ty
 * nào" (phạm vi áp dụng của văn bản) phải làm việc trên cặp chứ không phải trên
 * danh sách phòng ban.
 */
export interface DepartmentOfCompany {
  department_id: number
  department_name: string
  department_code: string
  company_id: number
  company_name: string
}

export interface DepartmentCompany {
  id: number
  department_id: number
  company_id: number
  company_name: string
  manager_employee_id: number | null
  manager_name: string
  issue_code_override: string
  is_active: boolean
}

export type DepartmentCompanyInput = Pick<
  DepartmentCompany,
  'company_id' | 'manager_employee_id' | 'issue_code_override' | 'is_active'
>
