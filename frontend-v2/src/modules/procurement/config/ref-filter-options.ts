import { companyApi } from '@/modules/hr/api/company-api'
import { departmentApi } from '@/modules/hr/api/department-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import type { SelectOption } from '@/shared/conditional-filter'

/**
 * Nguồn options cho các ô lọc THAM CHIẾU (công ty / phòng ban / nhân sự) — CR-088.
 */

const PAGE_SIZE = 50

/** Danh mục công ty / pháp nhân. */
export async function fetchCompanyOptions(search: string): Promise<SelectOption[]> {
  const res = await companyApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/** Danh mục phòng ban. Endpoint này tìm bằng `q` (tên phòng hoặc tên trưởng bộ phận). */
export async function fetchDepartmentOptions(search: string): Promise<SelectOption[]> {
  const res = await departmentApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/**
 * Danh mục nhân sự. Kèm MÃ vào nhãn vì đây chính là màn có người trùng tên —
 * không có mã thì hai dòng giống hệt nhau, chọn xong không biết đã chọn ai.
 */
export async function fetchEmployeeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ full_name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({
    value: String(item.id),
    label: item.code ? `${item.full_name} (${item.code})` : item.full_name,
  }))
}
