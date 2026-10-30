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
}

/** Một người trên sơ đồ; `reports` là cấp dưới trực tiếp CÙNG phòng. */
export interface OrgPersonNode {
  id: number
  code: string
  fullName: string
  position: string
  isHead: boolean
  reports: OrgPersonNode[]
}

export interface OrgDepartmentNode {
  id: number
  code: string
  name: string
  head: { id: number; fullName: string; position: string } | null
  /** Gốc của cây quản lý trong phòng (người không có quản lý cùng phòng). */
  people: OrgPersonNode[]
  children: OrgDepartmentNode[]
  /** Số người của phòng này, chưa tính phòng con. */
  ownHeadcount: number
  /** Số người của phòng này + mọi phòng con. */
  headcount: number
}

export interface OrgCompanyNode {
  /** `0` = nhóm "Chưa gán pháp nhân". */
  id: number
  code: string
  name: string
  departments: OrgDepartmentNode[]
  headcount: number
}
