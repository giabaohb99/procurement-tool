import type { OrgChartPayload } from '../types/org-chart'
import { resolveParents } from './org-chart-tree'

/** Một thẻ người trên sơ đồ kiểu ERPNext: gốc là NGƯỜI, cây đi theo quản lý trực tiếp. */
export interface OrgChartPerson {
  id: number
  code: string
  fullName: string
  position: string
  departmentId: number
  /** Tên phòng (rỗng khi chưa gắn phòng hoặc phòng ngoài tầm nhìn). */
  departmentName: string
  /** Quản lý trực tiếp CÓ MẶT trong dữ liệu (kể cả khi bị bộ lọc giấu khỏi sơ đồ); `0` = không có. */
  managerId: number
  /** Cấp dưới trực tiếp đang vẽ, đã sắp theo tên. */
  reportIds: number[]
}

export interface OrgChartForest {
  /** Mọi người trong payload (không riêng người đang vẽ) — để khung thông tin tra được tên quản lý. */
  people: Map<number, OrgChartPerson>
  /** Người đứng đầu một nhánh: người có nhiều cấp dưới nhất đứng trước, rồi theo tên. */
  roots: number[]
  /** Những người đang vẽ (đã qua bộ lọc pháp nhân / phòng ban). */
  visibleIds: Set<number>
}

export interface OrgChartForestFilter {
  /** `null` = mọi pháp nhân; `0` = nhóm "Chưa gán pháp nhân". */
  companyId: number | null
  /** Phòng đã chọn CỘNG mọi phòng con; `null` = mọi phòng. */
  departmentIds: ReadonlySet<number> | null
}

const byName = (a: OrgChartPerson, b: OrgChartPerson) =>
  a.fullName.localeCompare(b.fullName, 'vi') || a.id - b.id

/**
 * Dựng rừng quản lý trực tiếp từ dữ liệu phẳng của `/api/org-chart`.
 *
 * Giống ERPNext: người có quản lý NẰM TRONG phần đang vẽ thì treo dưới quản lý đó; quản lý vắng
 * mặt (0, ngoài phạm vi xem, khác pháp nhân, hoặc bị bộ lọc phòng giấu) thì người đó thành gốc.
 * Vòng `manager_id` (A→B→A) bị cắt một cạnh qua `resolveParents`, không làm treo trang.
 */
export function buildOrgChartForest(
  payload: OrgChartPayload,
  filter: OrgChartForestFilter,
): OrgChartForest {
  const knownCompanies = new Set(payload.companies.map((company) => company.id))
  const deptName = new Map(payload.departments.map((dept) => [dept.id, dept.name]))
  const allIds = new Set(payload.employees.map((employee) => employee.id))

  const people = new Map<number, OrgChartPerson>()
  for (const employee of payload.employees) {
    people.set(employee.id, {
      id: employee.id,
      code: employee.code,
      fullName: employee.full_name,
      position: employee.position,
      departmentId: employee.department_id,
      departmentName: deptName.get(employee.department_id) ?? '',
      managerId:
        employee.manager_id !== employee.id && allIds.has(employee.manager_id) ? employee.manager_id : 0,
      reportIds: [],
    })
  }

  //  Pháp nhân không có trong danh sách trả về (0 / ngoài tầm nhìn) gom vào nhóm "Chưa gán" = 0.
  const companyOf = (companyId: number) => (knownCompanies.has(companyId) ? companyId : 0)
  //  Phòng không có trong danh sách (0 / đã xóa / ngoài tầm nhìn) lọc chung dưới khóa 0 "Chưa gắn phòng ban".
  const departmentOf = (departmentId: number) => (deptName.has(departmentId) ? departmentId : 0)
  const visible = payload.employees.filter(
    (employee) =>
      (filter.companyId === null || companyOf(employee.company_id) === filter.companyId) &&
      (filter.departmentIds === null || filter.departmentIds.has(departmentOf(employee.department_id))),
  )
  const visibleIds = new Set(visible.map((employee) => employee.id))
  const parents = resolveParents(
    [...visibleIds],
    new Map(visible.map((employee) => [employee.id, people.get(employee.id)?.managerId ?? 0])),
  )

  const roots: OrgChartPerson[] = []
  for (const id of visibleIds) {
    const person = people.get(id)
    if (!person) continue
    const manager = people.get(parents.get(id) ?? 0)
    if (manager) manager.reportIds.push(id)
    else roots.push(person)
  }
  for (const person of people.values()) {
    person.reportIds.sort((a, b) => {
      const left = people.get(a)
      const right = people.get(b)
      return left && right ? byName(left, right) : a - b
    })
  }
  roots.sort((a, b) => b.reportIds.length - a.reportIds.length || byName(a, b))

  return { people, roots: roots.map((person) => person.id), visibleIds }
}

/** Chuỗi quản lý từ gốc xuống tới (không gồm) `id`, chỉ trong phần đang vẽ — để mở đường tới một thẻ. */
export function getOrgChartManagerPath(forest: OrgChartForest, id: number): number[] {
  const path: number[] = []
  const seen = new Set<number>([id])
  let cursor = forest.people.get(id)?.managerId ?? 0
  while (cursor && forest.visibleIds.has(cursor) && !seen.has(cursor)) {
    //  Chỉ đi lên khi `cursor` thật sự là cha của nút trước trên cây (vòng đã cắt thì dừng).
    const child = path[0] ?? id
    if (!forest.people.get(cursor)?.reportIds.includes(child)) break
    seen.add(cursor)
    path.unshift(cursor)
    cursor = forest.people.get(cursor)?.managerId ?? 0
  }
  return path
}

/**
 * Phòng `rootId` cộng mọi phòng con cháu (theo `parent`). `0` = nhóm "Chưa gắn phòng ban", không có con.
 * Có tập `seen` nên vòng `parent` trong dữ liệu không làm treo.
 */
export function collectOrgDepartmentIds(
  departments: OrgChartPayload['departments'],
  rootId: number,
): Set<number> {
  const result = new Set<number>([rootId])
  if (rootId === 0) return result
  const queue = [rootId]
  while (queue.length > 0) {
    const current = queue.shift()
    for (const dept of departments) {
      if (dept.parent === current && !result.has(dept.id)) {
        result.add(dept.id)
        queue.push(dept.id)
      }
    }
  }
  return result
}

/** Mọi người có cấp dưới trong phần đang vẽ — cho nút "Mở hết". */
export function listOrgChartManagers(forest: OrgChartForest): number[] {
  return [...forest.visibleIds].filter((id) => (forest.people.get(id)?.reportIds.length ?? 0) > 0)
}
