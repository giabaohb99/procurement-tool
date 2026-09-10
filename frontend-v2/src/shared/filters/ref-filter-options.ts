import { companyApi } from '@/modules/hr/api/company-api'
import { departmentApi } from '@/modules/hr/api/department-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import type { SelectOption } from '@/shared/conditional-filter'

/**
 * Nguồn options cho các ô lọc THAM CHIẾU dùng chung (công ty / phòng ban / nhân
 * sự) — dữ liệu cắt ngang mọi phân hệ. Tách khỏi phân hệ Thu mua để Đặt xe / Duyệt
 * dấu (và các phân hệ sau) dùng lại, không kéo lẫn cấu hình của nhau.
 */

const PAGE_SIZE = 50

export async function fetchCompanyOptions(search: string): Promise<SelectOption[]> {
  const res = await companyApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

export async function fetchDepartmentOptions(search: string): Promise<SelectOption[]> {
  const res = await departmentApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/** Nhân sự — kèm MÃ vào nhãn để phân biệt người trùng tên. */
export async function fetchEmployeeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ full_name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({
    value: String(item.id),
    label: item.code ? `${item.full_name} (${item.code})` : item.full_name,
  }))
}
