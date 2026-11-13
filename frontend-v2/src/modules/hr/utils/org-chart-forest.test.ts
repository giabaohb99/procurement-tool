import { describe, expect, it } from 'vitest'

import type { ConcurrentMember } from '../types/concurrent-member'
import { CONCURRENT_KIND_COMPANY, CONCURRENT_KIND_DEPARTMENT } from '../types/employee-concurrent'
import type { OrgChartDepartmentRow, OrgChartEmployeeRow, OrgChartPayload } from '../types/org-chart'
import {
  buildOrgChartForest,
  concurrentGroupTitle,
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
  return { companies, departments: [dept(1), dept(2), dept(3, { parent: 2 })], employees: [], concurrents: [], ...over }
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

  it('company filter: unknown / zero company_id falls into group 0 "Chưa gán pháp nhân"', () => {
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
    const forest = buildOrgChartForest({ companies: [], departments: [], employees: [], concurrents: [] }, ALL)
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

function member(id: number, over: Partial<ConcurrentMember> = {}): ConcurrentMember {
  return {
    id,
    employee_id: 100 + id,
    kind: CONCURRENT_KIND_DEPARTMENT,
    kind_label: 'Phòng ban',
    code: `K${id}`,
    full_name: `Kiêm nhiệm ${id}`,
    position_label: '',
    company_id: 2,
    company_name: 'Công ty B',
    department_id: 2,
    department_name: 'Phòng 2',
    from_date: '2026-09-01',
    to_date: null,
    status: 2,
    status_label: 'Đang hiệu lực',
    counts_scope: true,
    primary_company_id: 1,
    primary_company_name: 'Công ty A',
    primary_department_id: 1,
    primary_department_name: 'Phòng 1',
    can_open: true,
    ...over,
  }
}

describe('buildOrgChartForest — người kiêm nhiệm (duoc-CR-755)', () => {
  it('keeps concurrent people out of the manager tree: not roots, not people, so headcount is not doubled', () => {
    const forest = buildOrgChartForest(payload({ employees: [emp(1)], concurrents: [member(1)] }), ALL)
    expect(forest.roots).toEqual([1])
    expect(forest.people.has(101)).toBe(false)
    expect(forest.visibleIds.has(101)).toBe(false)
    expect(forest.concurrentGroups.map((g) => g.members.map((m) => m.id))).toEqual([[1]])
  })

  it('groups by concurrent place (department + company) and sorts people by name', () => {
    const forest = buildOrgChartForest(
      payload({
        concurrents: [
          member(1, { full_name: 'Zeta' }),
          member(2, { full_name: 'An' }),
          member(3, { department_id: 3, department_name: 'Phòng 3' }),
        ],
      }),
      ALL,
    )
    expect(forest.concurrentGroups.map((g) => [g.departmentName, g.members.map((m) => m.full_name)])).toEqual([
      ['Phòng 2', ['An', 'Zeta']],
      ['Phòng 3', ['Kiêm nhiệm 3']],
    ])
  })

  it('filters by the CONCURRENT company and department, not the primary ones', () => {
    const data = payload({
      concurrents: [member(1), member(2, { company_id: 1, company_name: 'Công ty A', department_id: 1 })],
    })
    const inB = buildOrgChartForest(data, { companyId: 2, departmentIds: null })
    expect(inB.concurrentGroups.flatMap((g) => g.members.map((m) => m.id))).toEqual([1])
    const dept1 = buildOrgChartForest(data, { companyId: null, departmentIds: new Set([1]) })
    expect(dept1.concurrentGroups.flatMap((g) => g.members.map((m) => m.id))).toEqual([2])
    const none = buildOrgChartForest(data, { companyId: 2, departmentIds: new Set([1]) })
    expect(none.concurrentGroups).toEqual([])
  })

  it('a department filter that includes child departments also shows people concurrent in a child', () => {
    const data = payload({ concurrents: [member(1, { department_id: 3, department_name: 'Phòng 3' })] })
    const forest = buildOrgChartForest(data, {
      companyId: null,
      departmentIds: collectOrgDepartmentIds(data.departments, 2),
    })
    expect(forest.concurrentGroups).toHaveLength(1)
  })

  it('an old payload without the concurrents key does not crash (stale cache / older backend)', () => {
    const legacy = { companies, departments: [dept(1)], employees: [emp(1)] } as unknown as OrgChartPayload
    expect(buildOrgChartForest(legacy, ALL).concurrentGroups).toEqual([])
  })

  it('empty list and a person listed twice at the same place (two rows) both stay safe', () => {
    expect(buildOrgChartForest(payload({ concurrents: [] }), ALL).concurrentGroups).toEqual([])
    const twice = buildOrgChartForest(payload({ concurrents: [member(1), member(2, { employee_id: 101 })] }), ALL)
    expect(twice.concurrentGroups[0].members.map((m) => m.id)).toEqual([1, 2])
  })
})

describe('buildOrgChartForest — kiêm nhiệm loại Công ty (duoc-CR-756)', () => {
  const companySeat = (id: number, over: Partial<ConcurrentMember> = {}) =>
    member(id, { kind: CONCURRENT_KIND_COMPANY, kind_label: 'Công ty', department_id: 0, department_name: '', ...over })

  it('Công ty rows group by COMPANY alone (one group per company, no room), titled "Kiêm nhiệm tại ..."', () => {
    const forest = buildOrgChartForest(
      payload({ concurrents: [companySeat(1, { full_name: 'Zeta' }), companySeat(2, { full_name: 'An' }), member(3)] }),
      ALL,
    )
    expect(forest.concurrentGroups.map((g) => [g.kind, g.key, g.members.map((m) => m.full_name)])).toEqual([
      //  Cùng công ty B: nhóm cả công ty đứng trước nhóm phòng.
      [CONCURRENT_KIND_COMPANY, 'c|2', ['An', 'Zeta']],
      [CONCURRENT_KIND_DEPARTMENT, 'd|2|2', ['Kiêm nhiệm 3']],
    ])
    expect(concurrentGroupTitle(forest.concurrentGroups[0])).toBe('Kiêm nhiệm tại Công ty B')
    expect(concurrentGroupTitle(forest.concurrentGroups[1])).toBe('Phòng 2 — Công ty B')
  })

  it('a Công ty row passes the company filter but never a department filter (it sits in no room)', () => {
    const data = payload({ concurrents: [companySeat(1)] })
    expect(buildOrgChartForest(data, { companyId: 2, departmentIds: null }).concurrentGroups).toHaveLength(1)
    expect(buildOrgChartForest(data, { companyId: 1, departmentIds: null }).concurrentGroups).toEqual([])
    //  Id phòng 0 trùng nhóm "Chưa gắn phòng ban" — không được lọt vào đó.
    expect(buildOrgChartForest(data, { companyId: null, departmentIds: new Set([0]) }).concurrentGroups).toEqual([])
  })

  it('group title adds "công ty" only when the name does not already start with it, and survives an empty name', () => {
    expect(concurrentGroupTitle({ kind: CONCURRENT_KIND_COMPANY, departmentName: '', companyName: 'SAM GROUP' })).toBe(
      'Kiêm nhiệm tại công ty SAM GROUP',
    )
    expect(
      concurrentGroupTitle({ kind: CONCURRENT_KIND_COMPANY, departmentName: '', companyName: 'CÔNG TY TNHH DEGO' }),
    ).toBe('Kiêm nhiệm tại CÔNG TY TNHH DEGO')
    expect(concurrentGroupTitle({ kind: CONCURRENT_KIND_COMPANY, departmentName: '', companyName: '' })).toBe(
      'Kiêm nhiệm tại công ty không rõ',
    )
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
