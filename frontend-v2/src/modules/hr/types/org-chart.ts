import type { ConcurrentMember } from './concurrent-member'

/** Dữ liệu PHẲNG của `GET /api/org-chart` (đã lọc theo phạm vi người xem). */
export interface OrgChartCompanyRow {
  id: number
  code: string
  name: string
}

export interface OrgChartDepartmentRow {
  id: number
  code: string
  name: string
  kind: number
  company_id: number
  /** `0` = phòng gốc (hoặc phòng cha nằm ngoài tầm nhìn). */
  parent: number
  /** Trưởng phòng; `0` = chưa gán HOẶC người đó ngoài phạm vi xem. */
  manager_id: number
}

export interface OrgChartEmployeeRow {
  id: number
  code: string
  full_name: string
  position: string
  company_id: number
  department_id: number
  /** Quản lý trực tiếp; `0` = chưa gán HOẶC người đó ngoài phạm vi xem. */
  manager_id: number
}

export interface OrgChartPayload {
  companies: OrgChartCompanyRow[]
  departments: OrgChartDepartmentRow[]
  employees: OrgChartEmployeeRow[]
  /**
   * Người KIÊM NHIỆM đang hiệu lực ở các phòng người xem phủ (duoc-CR-755) — vẽ ở PHÒNG KIÊM NHIỆM kèm nhãn
   * **Kiêm nhiệm**. Cố ý nằm ngoài `employees`: người đó vẫn chỉ là MỘT nhân sự ở công ty + phòng chính, nên không
   * thành thêm một nút trong cây quản lý và không bị đếm hai lần.
   */
  concurrents: ConcurrentMember[]
  /** `true` = backend cắt danh sách `concurrents` ở trần dòng — sơ đồ chưa hiện đủ người kiêm nhiệm. */
  concurrents_truncated?: boolean
}
