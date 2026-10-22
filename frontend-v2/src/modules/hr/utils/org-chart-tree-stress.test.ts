import { describe, expect, it } from 'vitest'

import type {
  OrgChartDepartmentRow,
  OrgChartEmployeeRow,
  OrgCompanyNode,
  OrgDepartmentNode,
  OrgPersonNode,
} from '../types/org-chart'
import { buildOrgChartTree, resolveParents } from './org-chart-tree'

/**
 * ÉP TẢI sơ đồ tổ chức (duoc-CR-669): dữ liệu nhập tay nên có thể sâu, có vòng, trỏ lung tung.
 * Điều phải giữ: không treo, không tràn ngăn xếp, KHÔNG mất người nào, tổng quân số khớp đầu vào.
 */

const companies = [
  { id: 1, code: 'A', name: 'Công ty A' },
  { id: 2, code: 'B', name: 'Công ty B' },
]

function dept(id: number, over: Partial<OrgChartDepartmentRow> = {}): OrgChartDepartmentRow {
  return { id, code: `D${id}`, name: `Phòng ${id}`, kind: 1, company_id: 1, parent: 0, manager_id: 0, ...over }
}

function emp(id: number, over: Partial<OrgChartEmployeeRow> = {}): OrgChartEmployeeRow {
  return { id, code: `E${id}`, full_name: `Người ${id}`, position: '', company_id: 1, department_id: 1, manager_id: 0, ...over }
}

function collectPeople(nodes: OrgPersonNode[], out: number[] = []): number[] {
  for (const node of nodes) {
    out.push(node.id)
    collectPeople(node.reports, out)
  }
  return out
}

function collectDepts(nodes: OrgDepartmentNode[], out: OrgDepartmentNode[] = []): OrgDepartmentNode[] {
  for (const node of nodes) {
    out.push(node)
    collectDepts(node.children, out)
  }
  return out
}

function allPeopleIds(tree: OrgCompanyNode[]): number[] {
  return tree.flatMap((company) => collectDepts(company.departments).flatMap((d) => collectPeople(d.people)))
}

describe('sơ đồ tổ chức — ép tải', () => {
  it('2000 người, 200 phòng hai pháp nhân, cha/quản lý ngẫu nhiên có vòng: dựng < 1s, không mất ai', () => {
    let seed = 42
    const rand = (n: number) => {
      seed = (seed * 1103515245 + 12345) % 2147483648
      return seed % n
    }
    const departments = Array.from({ length: 200 }, (_, i) =>
      dept(i + 1, { company_id: (i % 2) + 1, parent: rand(201), manager_id: rand(2001) }),
    )
    const employees = Array.from({ length: 2000 }, (_, i) =>
      emp(i + 1, { company_id: (i % 2) + 1, department_id: rand(230), manager_id: rand(2001) }),
    )

    const started = performance.now()
    const tree = buildOrgChartTree({ companies, departments, employees })
    const elapsed = performance.now() - started

    expect(elapsed).toBeLessThan(1000)
    const ids = allPeopleIds(tree)
    expect(ids).toHaveLength(2000)
    expect(new Set(ids).size).toBe(2000)
    expect(tree.reduce((sum, c) => sum + c.headcount, 0)).toBe(2000)
  })

  it('chuỗi quản lý thẳng 2000 cấp trong một phòng: không tràn ngăn xếp, đủ 2000 người', () => {
    const employees = Array.from({ length: 2000 }, (_, i) => emp(i + 1, { manager_id: i }))
    const tree = buildOrgChartTree({ companies, departments: [dept(1)], employees })
    expect(allPeopleIds(tree)).toHaveLength(2000)
    expect(tree[0].departments[0].people).toHaveLength(1)
  })

  it('chuỗi phòng cha 500 tầng: quân số dồn đúng lên gốc', () => {
    const departments = Array.from({ length: 500 }, (_, i) => dept(i + 1, { parent: i }))
    const employees = Array.from({ length: 500 }, (_, i) => emp(i + 1, { department_id: i + 1 }))
    const tree = buildOrgChartTree({ companies, departments, employees })
    expect(tree[0].departments).toHaveLength(1)
    expect(tree[0].departments[0].headcount).toBe(500)
  })

  it('một vòng 2000 nút: cắt đúng MỘT cạnh ở nút id nhỏ nhất, trả về < 1s', () => {
    const ids = Array.from({ length: 2000 }, (_, i) => i + 1)
    const parentOf = new Map(ids.map((id) => [id, id === 2000 ? 1 : id + 1]))
    const started = performance.now()
    const resolved = resolveParents(ids, parentOf)
    expect(performance.now() - started).toBeLessThan(1000)
    expect([...resolved.values()].filter((p) => p === 0)).toEqual([0])
    expect(resolved.get(1)).toBe(0)
  })

  it('id trùng trong dữ liệu phòng/người không nhân đôi quân số', () => {
    const employees = [emp(1), emp(2, { manager_id: 1 }), emp(3, { manager_id: 2 })]
    const tree = buildOrgChartTree({ companies, departments: [dept(1), dept(2, { parent: 1 })], employees })
    expect(tree[0].headcount).toBe(3)
    expect(new Set(allPeopleIds(tree)).size).toBe(3)
  })
})
