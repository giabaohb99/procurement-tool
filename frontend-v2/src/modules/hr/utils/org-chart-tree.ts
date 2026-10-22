import type {
  OrgChartPayload,
  OrgCompanyNode,
  OrgDepartmentNode,
  OrgPersonNode,
} from '../types/org-chart'

/**
 * Chuẩn hóa bảng cha–con về MỘT FOREST không vòng.
 *
 * Cha không nằm trong `ids`, bằng `0`, hoặc tự trỏ vào mình → `0` (nút gốc).
 * Gặp vòng (A→B→A, dữ liệu nhập tay hoàn toàn có thể ra thế) thì CẮT một cạnh —
 * cạnh của nút có id nhỏ nhất trong vòng, để kết quả ổn định giữa các lần vẽ —
 * thay vì để đệ quy vô hạn treo trình duyệt.
 */
export function resolveParents(
  ids: readonly number[],
  parentOf: ReadonlyMap<number, number>,
): Map<number, number> {
  const members = new Set(ids)
  const resolved = new Map<number, number>()
  for (const id of ids) {
    const parent = parentOf.get(id) ?? 0
    resolved.set(id, parent !== id && members.has(parent) ? parent : 0)
  }
  for (const start of [...ids].sort((a, b) => a - b)) {
    // Mỗi lần cắt gỡ một cạnh nên vòng lặp ngoài chắc chắn dừng.
    for (;;) {
      const path: number[] = []
      const seen = new Set<number>()
      let cursor = start
      while (cursor !== 0 && !seen.has(cursor)) {
        seen.add(cursor)
        path.push(cursor)
        cursor = resolved.get(cursor) ?? 0
      }
      if (cursor === 0) break
      const cycle = path.slice(path.indexOf(cursor))
      resolved.set(Math.min(...cycle), 0)
    }
  }
  return resolved
}

function compareByName(a: { fullName: string; id: number }, b: { fullName: string; id: number }) {
  return a.fullName.localeCompare(b.fullName, 'vi') || a.id - b.id
}

/** Dựng cây người trong MỘT phòng: quản lý chỉ có tác dụng khi cùng phòng. */
function buildPeople(
  members: OrgChartPayload['employees'],
  headId: number,
): OrgPersonNode[] {
  const nodes = new Map<number, OrgPersonNode>()
  for (const member of members) {
    nodes.set(member.id, {
      id: member.id,
      code: member.code,
      fullName: member.full_name,
      position: member.position,
      isHead: member.id === headId,
      reports: [],
    })
  }
  const parents = resolveParents(
    members.map((member) => member.id),
    new Map(members.map((member) => [member.id, member.manager_id])),
  )
  const roots: OrgPersonNode[] = []
  for (const node of nodes.values()) {
    const parent = nodes.get(parents.get(node.id) ?? 0)
    ;(parent ? parent.reports : roots).push(node)
  }
  const sortDeep = (list: OrgPersonNode[]) => {
    // Trưởng phòng lên đầu, còn lại theo tên.
    list.sort((a, b) => Number(b.isHead) - Number(a.isHead) || compareByName(a, b))
    list.forEach((node) => sortDeep(node.reports))
  }
  sortDeep(roots)
  return roots
}

/** Pháp nhân › phòng ban (theo `parent`) › người (theo quản lý trực tiếp). */
export function buildOrgChartTree(payload: OrgChartPayload): OrgCompanyNode[] {
  const { companies, employees } = payload
  //  Người chưa gắn phòng (hoặc phòng không còn) vẫn phải hiện: gom vào một phòng
  //  ảo «Chưa gán phòng ban» theo pháp nhân (id âm để không đụng id thật).
  const realDeptIds = new Set(payload.departments.map((dept) => dept.id))
  const orphanCompanyIds = [
    ...new Set(
      employees.filter((e) => !realDeptIds.has(e.department_id)).map((e) => e.company_id),
    ),
  ]
  const orphanDeptOf = new Map(orphanCompanyIds.map((cid) => [cid, -(cid + 1)]))
  const departments = [
    ...payload.departments,
    ...orphanCompanyIds.map((cid) => ({
      id: -(cid + 1),
      code: '',
      name: 'Chưa gán phòng ban',
      kind: 0,
      company_id: cid,
      parent: 0,
      manager_id: 0,
    })),
  ]
  const employeeById = new Map(employees.map((employee) => [employee.id, employee]))

  const membersOf = new Map<number, OrgChartPayload['employees']>()
  for (const employee of employees) {
    const deptId = realDeptIds.has(employee.department_id)
      ? employee.department_id
      : (orphanDeptOf.get(employee.company_id) ?? 0)
    const list = membersOf.get(deptId) ?? []
    list.push(employee)
    membersOf.set(deptId, list)
  }

  const deptNodes = new Map<number, OrgDepartmentNode>()
  for (const dept of departments) {
    const members = membersOf.get(dept.id) ?? []
    const headRow = dept.manager_id ? employeeById.get(dept.manager_id) : undefined
    deptNodes.set(dept.id, {
      id: dept.id,
      code: dept.code,
      name: dept.name,
      head: headRow
        ? { id: headRow.id, fullName: headRow.full_name, position: headRow.position }
        : null,
      people: buildPeople(members, dept.manager_id),
      children: [],
      ownHeadcount: members.length,
      headcount: members.length,
    })
  }

  //  Phòng cha khác pháp nhân thì coi như gốc trong pháp nhân của chính nó: cây
  //  được vẽ TRONG từng pháp nhân nên không thể móc xuyên sang pháp nhân khác.
  const companyOf = new Map(departments.map((dept) => [dept.id, dept.company_id]))
  const parentOf = new Map(
    departments.map((dept) => [
      dept.id,
      companyOf.get(dept.parent) === dept.company_id ? dept.parent : 0,
    ]),
  )
  const parents = resolveParents(
    departments.map((dept) => dept.id),
    parentOf,
  )

  const rootsByCompany = new Map<number, OrgDepartmentNode[]>()
  for (const dept of departments) {
    const node = deptNodes.get(dept.id)
    if (!node) continue
    const parent = deptNodes.get(parents.get(dept.id) ?? 0)
    if (parent) {
      parent.children.push(node)
    } else {
      const list = rootsByCompany.get(dept.company_id) ?? []
      list.push(node)
      rootsByCompany.set(dept.company_id, list)
    }
  }

  const sumHeadcount = (node: OrgDepartmentNode): number => {
    node.children.sort((a, b) => a.name.localeCompare(b.name, 'vi') || a.id - b.id)
    node.headcount = node.ownHeadcount + node.children.reduce((sum, c) => sum + sumHeadcount(c), 0)
    return node.headcount
  }

  const result: OrgCompanyNode[] = []
  const knownCompanyIds = new Set(companies.map((company) => company.id))
  const companyRows = [
    ...companies,
    //  Phòng thuộc pháp nhân không trả về (id 0 hoặc ngoài tầm nhìn) gom vào một nhóm chung.
    ...(departments.some((dept) => !knownCompanyIds.has(dept.company_id))
      ? [{ id: 0, code: '', name: 'Chưa gán pháp nhân' }]
      : []),
  ]
  for (const company of companyRows) {
    const roots =
      company.id === 0
        ? departments
            .filter((dept) => !knownCompanyIds.has(dept.company_id))
            .flatMap((dept) => rootsByCompany.get(dept.company_id) ?? [])
        : (rootsByCompany.get(company.id) ?? [])
    const uniqueRoots = [...new Set(roots)].sort(
      (a, b) => a.name.localeCompare(b.name, 'vi') || a.id - b.id,
    )
    if (uniqueRoots.length === 0) continue
    const headcount = uniqueRoots.reduce((sum, root) => sum + sumHeadcount(root), 0)
    result.push({ id: company.id, code: company.code, name: company.name, departments: uniqueRoots, headcount })
  }
  return result
}
