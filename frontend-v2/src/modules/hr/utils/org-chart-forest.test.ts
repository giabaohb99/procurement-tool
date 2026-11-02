import { describe, expect, it } from 'vitest'

import type { OrgChartDepartmentRow, OrgChartEmployeeRow, OrgChartPayload } from '../types/org-chart'
import {
  buildOrgChartForest,
  collectOrgDepartmentIds,
  getOrgChartManagerPath,
  listOrgChartManagers,
  type OrgChartForest,
} from './org-chart-forest'

const companies = [
  { id: 1, code: 'A', name: 'Công ty A' },
  { id: 2, code: 'B', name: 'Công ty B' },
]
const ALL = { companyId: null, departmentIds: null }

function dept(id: number, over: Partial<OrgChartDepartmentRow> = {}): OrgChartDepartmentRow {
  return { id, code: `D${id}`, name: `Phòng ${id}`, kind: 1, company_id: 1, parent: 0, manager_id: 0, ...over }
}

function emp(id: number, over: Partial<OrgChartEmployeeRow> = {}): OrgChartEmployeeRow {
  return { id, code: `E${id}`, full_name: `Người ${id}`, position: '', company_id: 1, department_id: 1, manager_id: 0, ...over }
}

function payload(over: Partial<OrgChartPayload>): OrgChartPayload {
  return { companies, departments: [dept(1), dept(2), dept(3, { parent: 2 })], employees: [], ...over }
}

//  Mọi người trên cây (đi từ gốc xuống) — để chốt không ai bị mất hay vẽ hai lần.
function walk(forest: OrgChartForest): number[] {
  const out: number[] = []
  const stack = [...forest.roots]
  while (stack.length > 0) {
    const id = stack.pop() as number
    out.push(id)
    stack.push(...(forest.people.get(id)?.reportIds ?? []))
  }
  return out
}

describe('buildOrgChartForest', () => {
  it('hangs people under their direct manager even across departments, roots are those without one', () => {
    const forest = buildOrgChartForest(
      payload({
        employees: [
          emp(1, { full_name: 'Giám đốc' }),
          emp(2, { manager_id: 1, department_id: 2, full_name: 'Bình' }),
          emp(3, { manager_id: 1, department_id: 3, full_name: 'An' }),
        ],
      }),
      ALL,
    )
    expect(forest.roots).toEqual([1])
    //  Cấp dưới theo tên (vi): An trước Bình.
    expect(forest.people.get(1)?.reportIds).toEqual([3, 2])
    expect(forest.people.get(3)?.departmentName).toBe('Phòng 3')
  })

  it('puts the root with most reports first, then by name', () => {
    const forest = buildOrgChartForest(
      payload({
        employees: [emp(1, { full_name: 'Zed' }), emp(2, { full_name: 'An' }), emp(3, { manager_id: 1 })],
      }),
      ALL,
    )
    expect(forest.roots).toEqual([1, 2])
  })

  it('a manager hidden by the department filter makes their reports roots, but keeps managerId for the popover', () => {
    const forest = buildOrgChartForest(
      payload({ employees: [emp(1, { department_id: 1 }), emp(2, { manager_id: 1, department_id: 2 })] }),
      { companyId: null, departmentIds: new Set([2]) },
    )
    expect(forest.roots).toEqual([2])
    expect(forest.people.get(2)?.managerId).toBe(1)
    expect(forest.visibleIds.has(1)).toBe(false)
  })

  it('manager outside the payload, zero or self becomes no manager (managerId 0), not a dangling id', () => {
    const forest = buildOrgChartForest(
      payload({ employees: [emp(1, { manager_id: 999 }), emp(2, { manager_id: 2 }), emp(3, { manager_id: 0 })] }),
      ALL,
    )
    expect([...forest.people.values()].map((p) => p.managerId)).toEqual([0, 0, 0])
    expect(forest.roots).toHaveLength(3)
  })

  it('company filter: unknown / zero company_id falls into group 0 «Chưa gán pháp nhân»', () => {
    const data = payload({ employees: [emp(1, { company_id: 2 }), emp(2, { company_id: 0 }), emp(3, { company_id: 77 })] })
    expect([...buildOrgChartForest(data, { companyId: 0, departmentIds: null }).visibleIds].sort()).toEqual([2, 3])
    expect([...buildOrgChartForest(data, { companyId: 2, departmentIds: null }).visibleIds]).toEqual([1])
  })

  it('department filter 0 picks people whose department is missing or unknown', () => {
    const data = payload({ employees: [emp(1, { department_id: 0 }), emp(2, { department_id: 404 }), emp(3)] })
    const forest = buildOrgChartForest(data, { companyId: null, departmentIds: new Set([0]) })
    expect([...forest.visibleIds].sort()).toEqual([1, 2])
    expect(forest.people.get(2)?.departmentName).toBe('')
  })

  it('a manager cycle is cut, nobody is lost and nobody appears twice', () => {
    const forest = buildOrgChartForest(
      payload({ employees: [emp(1, { manager_id: 2 }), emp(2, { manager_id: 3 }), emp(3, { manager_id: 1 })] }),
      ALL,
    )
    const seen = walk(forest)
    expect(seen.sort()).toEqual([1, 2, 3])
    expect(forest.roots).toHaveLength(1)
  })

  it('empty payload gives an empty forest', () => {
    const forest = buildOrgChartForest({ companies: [], departments: [], employees: [] }, ALL)
    expect(forest.roots).toEqual([])
    expect(forest.visibleIds.size).toBe(0)
  })
})

describe('getOrgChartManagerPath', () => {
  const forest = buildOrgChartForest(
    payload({ employees: [emp(1), emp(2, { manager_id: 1 }), emp(3, { manager_id: 2 }), emp(4, { manager_id: 3, department_id: 2 })] }),
    { companyId: null, departmentIds: new Set([1]) },
  )

  it('returns managers from the root down to (not including) the person', () => {
    expect(getOrgChartManagerPath(forest, 3)).toEqual([1, 2])
    expect(getOrgChartManagerPath(forest, 1)).toEqual([])
  })

  it('stops at managers that are not drawn and returns [] for unknown ids', () => {
    expect(getOrgChartManagerPath(forest, 4)).toEqual([])
    expect(getOrgChartManagerPath(forest, 999)).toEqual([])
  })

  it('does not loop forever on a cut cycle', () => {
    const cyclic = buildOrgChartForest(payload({ employees: [emp(1, { manager_id: 2 }), emp(2, { manager_id: 1 })] }), ALL)
    expect(getOrgChartManagerPath(cyclic, 1).length + getOrgChartManagerPath(cyclic, 2).length).toBe(1)
  })
})

describe('collectOrgDepartmentIds / listOrgChartManagers', () => {
  it('collects the department and all descendants, survives a parent cycle', () => {
    const departments = [dept(1), dept(2, { parent: 1 }), dept(3, { parent: 2 }), dept(4, { parent: 5 }), dept(5, { parent: 4 })]
    expect([...collectOrgDepartmentIds(departments, 1)].sort()).toEqual([1, 2, 3])
    expect([...collectOrgDepartmentIds(departments, 4)].sort()).toEqual([4, 5])
    expect([...collectOrgDepartmentIds(departments, 0)]).toEqual([0])
  })

  it('lists only visible people who have reports', () => {
    const forest = buildOrgChartForest(payload({ employees: [emp(1), emp(2, { manager_id: 1 }), emp(3)] }), ALL)
    expect(listOrgChartManagers(forest)).toEqual([1])
  })
})

describe('buildOrgChartForest — ép tải', () => {
  it('2000 people with random managers incl. cycles: < 1s, every person exactly once', () => {
    let seed = 42
    const rand = (n: number) => {
      seed = (seed * 1103515245 + 12345) % 2147483648
      return seed % n
    }
    const employees = Array.from({ length: 2000 }, (_, i) =>
      emp(i + 1, { company_id: (i % 2) + 1, department_id: rand(5), manager_id: rand(2001) }),
    )
    const started = performance.now()
    const forest = buildOrgChartForest(payload({ employees }), ALL)
    expect(performance.now() - started).toBeLessThan(1000)
    const seen = walk(forest)
    expect(seen).toHaveLength(2000)
    expect(new Set(seen).size).toBe(2000)
  })

  it('a straight 2000-level chain: no stack overflow, one root, path to the bottom has 1999 managers', () => {
    const employees = Array.from({ length: 2000 }, (_, i) => emp(i + 1, { manager_id: i }))
    const forest = buildOrgChartForest(payload({ employees }), ALL)
    expect(forest.roots).toEqual([1])
    expect(getOrgChartManagerPath(forest, 2000)).toHaveLength(1999)
  })
})
