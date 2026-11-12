import { describe, expect, it } from 'vitest'

import type { Department, DepartmentOfCompany } from '../types/department'
import { buildConcurrentDepartmentOptions } from './concurrent-department-options'

function dept(id: number, name: string, companyId: number): Department {
  return { id, code: `P${id}`, name, issue_code: '', kind: 1, company_id: companyId, parent: 0, manager_id: 0, is_active: true }
}

function pair(departmentId: number, name: string, companyId: number): DepartmentOfCompany {
  return { department_id: departmentId, department_name: name, department_code: '', company_id: companyId, company_name: '' }
}

const DEPARTMENTS = [
  dept(1, 'Kế toán', 0), // dùng chung
  dept(2, 'Kinh doanh A', 10), // riêng công ty A
  dept(3, 'Kho B', 20), // riêng công ty B
  dept(4, 'Nhà máy C', 30), // riêng công ty C, nhưng phục vụ B qua bảng ánh xạ
]
const PRIMARY = { companyId: 10, departmentId: 2 }

function ids(companyId: number, pairs: DepartmentOfCompany[] = [], primary = PRIMARY, keepId = 0) {
  return buildConcurrentDepartmentOptions(DEPARTMENTS, pairs, companyId, primary, keepId).map((o) => o.id)
}

describe('buildConcurrentDepartmentOptions', () => {
  it('no company chosen yet → empty list, never the whole catalogue', () => {
    expect(ids(0)).toEqual([])
    expect(ids(-1)).toEqual([])
  })

  it('other company: own departments + shared departments, never another company private department', () => {
    expect(ids(20).sort()).toEqual([1, 3])
  })

  it('department mapped to the company via tab_department_company is offered even though its home is another company', () => {
    expect(ids(20, [pair(4, 'Nhà máy C', 20)]).sort()).toEqual([1, 3, 4])
  })

  it('a mapping for a DIFFERENT company does not leak into this list', () => {
    expect(ids(20, [pair(4, 'Nhà máy C', 99)]).sort()).toEqual([1, 3])
  })

  it('same company as the primary position: primary department removed (backend rejects 400)', () => {
    expect(ids(10)).not.toContain(2)
    expect(ids(10)).toContain(1)
  })

  it('shared department equal to the primary id is still offered at ANOTHER company', () => {
    const primaryShared = { companyId: 10, departmentId: 1 }
    expect(ids(20, [], primaryShared)).toContain(1)
    expect(ids(10, [], primaryShared)).not.toContain(1)
  })

  it('editing a legacy row that already holds the primary department keeps it so the field is not blank', () => {
    expect(ids(10, [], PRIMARY, 2)).toContain(2)
  })

  it('duplicates between catalogue and mapping collapse to one entry, sorted by Vietnamese name', () => {
    const list = buildConcurrentDepartmentOptions(DEPARTMENTS, [pair(1, 'Kế toán', 20), pair(3, 'Kho B', 20)], 20, PRIMARY)
    expect(list.map((o) => o.label)).toEqual(['Kế toán', 'Kho B'])
  })
})
