import { describe, expect, it } from 'vitest'

import type {
  OrgChartDepartmentRow,
  OrgChartEmployeeRow,
  OrgChartPayload,
} from '../types/org-chart'
import { buildOrgChartTree, resolveParents } from './org-chart-tree'

const company = { id: 1, code: 'A', name: 'Công ty A' }

function dept(id: number, over: Partial<OrgChartDepartmentRow> = {}): OrgChartDepartmentRow {
  return { id, code: `D${id}`, name: `Phòng ${id}`, kind: 1, company_id: 1, parent: 0, manager_id: 0, ...over }
}

function emp(id: number, over: Partial<OrgChartEmployeeRow> = {}): OrgChartEmployeeRow {
  return {
    id,
    code: `E${id}`,
    full_name: `Người ${id}`,
    position: '',
    company_id: 1,
    department_id: 10,
    manager_id: 0,
    ...over,
  }
}

function build(over: Partial<OrgChartPayload>) {
  return buildOrgChartTree({ companies: [company], departments: [], employees: [], ...over })
}

describe('resolveParents', () => {
  it('cha ngoài danh sách, bằng 0 hoặc tự trỏ vào mình đều thành gốc', () => {
    const result = resolveParents([1, 2, 3], new Map([[1, 99], [2, 0], [3, 3]]))
    expect([...result.values()]).toEqual([0, 0, 0])
  })

  it('vòng hai nút bị cắt, không treo, vẫn còn đúng một cạnh', () => {
    const result = resolveParents([1, 2], new Map([[1, 2], [2, 1]]))
    expect(result.get(1)).toBe(0) // cắt cạnh của nút id nhỏ nhất
    expect(result.get(2)).toBe(1)
  })

  it('vòng dài có đuôi dẫn vào: đuôi vẫn nối vào vòng, vòng bị cắt', () => {
    const result = resolveParents([1, 2, 3, 4], new Map([[1, 2], [2, 3], [3, 1], [4, 1]]))
    expect(result.get(1)).toBe(0)
    expect(result.get(4)).toBe(1)
  })

  it('danh sách rỗng không nổ', () => {
    expect(resolveParents([], new Map()).size).toBe(0)
  })
})

describe('buildOrgChartTree', () => {
  it('payload rỗng ra cây rỗng', () => {
    expect(build({})).toEqual([])
  })

  it('phòng con nằm dưới phòng cha và quân số cộng dồn', () => {
    const tree = build({
      departments: [dept(10), dept(11, { parent: 10 })],
      employees: [emp(1), emp(2, { department_id: 11 }), emp(3, { department_id: 11 })],
    })
    const root = tree[0].departments[0]
    expect(root.id).toBe(10)
    expect(root.children.map((c) => c.id)).toEqual([11])
    expect(root.ownHeadcount).toBe(1)
    expect(root.headcount).toBe(3)
    expect(tree[0].headcount).toBe(3)
  })

  it('quản lý trực tiếp cùng phòng thành cây; quản lý khác phòng thì người đó là gốc', () => {
    const tree = build({
      departments: [dept(10), dept(11)],
      employees: [
        emp(1),
        emp(2, { manager_id: 1 }),
        emp(3, { manager_id: 1, department_id: 11 }),
      ],
    })
    const [a, b] = tree[0].departments
    expect(a.people[0].reports.map((p) => p.id)).toEqual([2])
    expect(b.people.map((p) => p.id)).toEqual([3])
  })

  it('vòng quản lý không làm treo và không mất người', () => {
    const tree = build({
      departments: [dept(10)],
      employees: [emp(1, { manager_id: 2 }), emp(2, { manager_id: 1 }), emp(3, { manager_id: 3 })],
    })
    const flat: number[] = []
    const walk = (nodes: { id: number; reports: never[] | { id: number; reports: unknown[] }[] }[]) =>
      nodes.forEach((n) => {
        flat.push(n.id)
        walk(n.reports as typeof nodes)
      })
    walk(tree[0].departments[0].people)
    expect(flat.sort()).toEqual([1, 2, 3])
  })

  it('vòng phòng cha không làm treo và không mất phòng', () => {
    const tree = build({
      departments: [dept(10, { parent: 11 }), dept(11, { parent: 10 })],
      employees: [emp(1)],
    })
    expect(tree[0].departments).toHaveLength(1)
    expect(tree[0].departments[0].children).toHaveLength(1)
  })

  it('phòng cha khác pháp nhân: phòng con thành gốc trong pháp nhân của nó', () => {
    const tree = buildOrgChartTree({
      companies: [company, { id: 2, code: 'B', name: 'Công ty B' }],
      departments: [dept(10), dept(20, { company_id: 2, parent: 10 })],
      employees: [],
    })
    expect(tree.map((c) => c.id)).toEqual([1, 2])
    expect(tree[1].departments[0].id).toBe(20)
  })

  it('trưởng phòng ngoài phạm vi (manager_id = 0) thì không ghi tên ai', () => {
    const tree = build({ departments: [dept(10, { manager_id: 0 })], employees: [emp(1)] })
    expect(tree[0].departments[0].head).toBeNull()
  })

  it('trưởng phòng được đánh dấu và đứng đầu danh sách', () => {
    const tree = build({
      departments: [dept(10, { manager_id: 2 })],
      employees: [emp(1, { full_name: 'An' }), emp(2, { full_name: 'Zed' })],
    })
    const [first] = tree[0].departments[0].people
    expect(first.id).toBe(2)
    expect(first.isHead).toBe(true)
    expect(tree[0].departments[0].head?.fullName).toBe('Zed')
  })

  it('người chưa gắn phòng vẫn hiện, trong phòng ảo "Chưa gán phòng ban"', () => {
    const tree = build({
      departments: [dept(10)],
      employees: [emp(1, { department_id: 0 }), emp(2, { department_id: 777 })],
    })
    const names = tree[0].departments.map((d) => d.name)
    expect(names).toContain('Chưa gán phòng ban')
    const orphan = tree[0].departments.find((d) => d.name === 'Chưa gán phòng ban')
    expect(orphan?.ownHeadcount).toBe(2)
  })

  it('phòng thuộc pháp nhân lạ (company_id 0) gom vào "Chưa gán pháp nhân"', () => {
    const tree = build({
      departments: [dept(10, { company_id: 0 })],
      employees: [emp(1, { company_id: 0 })],
    })
    expect(tree.map((c) => c.name)).toEqual(['Chưa gán pháp nhân'])
    expect(tree[0].headcount).toBe(1)
  })

  it('1000 người trong chuỗi quản lý dài vẫn dựng được', () => {
    const employees = Array.from({ length: 1000 }, (_, i) => emp(i + 1, { manager_id: i }))
    const tree = build({ departments: [dept(10)], employees })
    expect(tree[0].headcount).toBe(1000)
  })
})
