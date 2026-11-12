import type { EmployeeConcurrent } from '../types/employee-concurrent'

/** Hai cờ điều khiển gửi kèm PATCH hồ sơ — khớp `EmployeeUpdate` của backend (phase 03). */
export interface CompanyChangeConcurrentChoice {
  end_old_company_concurrent: boolean
  keep_concurrent_ids: number[]
}

/** Từ tập dòng được tick GIỮ → thân gửi đi. Giữ hết = `false` (không kết thúc gì), khỏi gửi danh sách. */
export function buildCompanyChangeChoice(rows: readonly EmployeeConcurrent[], keepIds: ReadonlySet<number>): CompanyChangeConcurrentChoice {
  const kept = rows.filter((r) => keepIds.has(r.id)).map((r) => r.id)
  if (rows.length > 0 && kept.length === rows.length) return { end_old_company_concurrent: false, keep_concurrent_ids: [] }
  return { end_old_company_concurrent: true, keep_concurrent_ids: kept }
}
