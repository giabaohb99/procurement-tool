import type { Department, DepartmentOfCompany } from '../types/department'

export interface ConcurrentDepartmentOption {
  id: number
  label: string
}

/**
 * Phòng chọn được cho một dòng kiêm nhiệm ở công ty `companyId` — đúng luật L3 của backend
 * (`concurrent_service.check_concurrent_target`): phòng PHỤC VỤ công ty khi
 * - `Department.company_id` = công ty đó, hoặc `= 0` (phòng DÙNG CHUNG — 26/27 phòng prod, bao-CR-659), hoặc
 * - có dòng `tab_department_company` đang bật nối phòng với công ty đó (`servedPairs`, lấy từ `/departments/by-companies`).
 *
 * ⚠️ `/by-companies` KHÔNG trả phòng dùng chung chưa nạp bảng ánh xạ, còn danh mục phòng ban không biết bảng ánh xạ —
 * phải HỢP hai nguồn, thiếu một là ô chọn rơi mất phòng mà backend cho phép.
 *
 * `primary` = vị trí chính của hồ sơ: cùng công ty chính thì bỏ phòng chính khỏi danh sách (backend chặn 400 "trùng phòng
 * chính"); khác công ty thì cùng một id phòng dùng chung vẫn chọn được. `keepId` = phòng của dòng đang sửa, luôn giữ lại
 * để ô không hiện trống với dữ liệu cũ.
 */
export function buildConcurrentDepartmentOptions(
  departments: readonly Department[],
  servedPairs: readonly DepartmentOfCompany[],
  companyId: number,
  primary: { companyId: number; departmentId: number },
  keepId = 0,
): ConcurrentDepartmentOption[] {
  if (companyId <= 0) return []

  const byId = new Map<number, string>()
  for (const d of departments) {
    if (d.company_id === 0 || d.company_id === companyId) byId.set(d.id, d.name)
  }
  for (const pair of servedPairs) {
    if (pair.company_id === companyId) byId.set(pair.department_id, pair.department_name)
  }

  if (companyId === primary.companyId && primary.departmentId > 0 && primary.departmentId !== keepId) {
    byId.delete(primary.departmentId)
  }

  return [...byId.entries()]
    .map(([id, label]) => ({ id, label }))
    .sort((a, b) => a.label.localeCompare(b.label, 'vi'))
}
