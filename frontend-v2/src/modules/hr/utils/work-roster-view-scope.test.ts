import { describe, expect, it } from 'vitest'

import { CONCURRENT_KIND_COMPANY, CONCURRENT_KIND_DEPARTMENT } from '../types/employee-concurrent'
import {
  clampRosterDepartment,
  defaultRosterDepartment,
  departmentAllLabel,
  resolveRosterViewScope,
  viewerDepartmentOptions,
} from './work-roster-view-scope'

const canWith = (keys: string[]) => (entity: string, action: string) => keys.includes(`${entity}.${action}`)

const concurrent = (kind: number, id: number, name: string, counts = true) => ({
  kind,
  department_id: id,
  department_name: name,
  counts_scope: counts,
})

describe('resolveRosterViewScope', () => {
  it('HR key wins even when the manager key is also held', () => {
    expect(resolveRosterViewScope(canWith(['work_schedule.write', 'work_schedule_personal.read']))).toBe('all')
  })

  it('manager write key limits to own departments; reading the HR catalog is not enough for "all"', () => {
    expect(resolveRosterViewScope(canWith(['work_schedule_personal.read', 'work_schedule_personal.write']))).toBe('departments')
    expect(resolveRosterViewScope(canWith(['work_schedule_personal.write']))).toBe('departments')
    expect(resolveRosterViewScope(canWith(['work_schedule.read', 'employee.read']))).toBe('self')
  })

  it('a director with the personal key READ only is a company-wide viewer, not a manager', () => {
    expect(resolveRosterViewScope(canWith(['work_schedule_personal.read']))).toBe('company')
    expect(resolveRosterViewScope(canWith(['work_schedule_personal.read', 'work_schedule.read']))).toBe('company')
  })

  it('nobody else sees more than themselves', () => {
    expect(resolveRosterViewScope(canWith([]))).toBe('self')
  })
})

describe('viewerDepartmentOptions', () => {
  it('primary first, then scope-counting department concurrents; company rows, switched-off rows and duplicates dropped', () => {
    const options = viewerDepartmentOptions({
      department_id: 4,
      department_name: 'IT',
      concurrents: [
        concurrent(CONCURRENT_KIND_DEPARTMENT, 7, 'Kế toán'),
        concurrent(CONCURRENT_KIND_DEPARTMENT, 4, 'IT'),
        concurrent(CONCURRENT_KIND_DEPARTMENT, 9, 'Kho', false),
        concurrent(CONCURRENT_KIND_COMPANY, 0, ''),
      ],
    })
    expect(options).toEqual([
      { id: 4, name: 'IT' },
      { id: 7, name: 'Kế toán' },
    ])
  })

  it('no profile / no department → no options (old session without concurrents is fine)', () => {
    expect(viewerDepartmentOptions(null)).toEqual([])
    expect(viewerDepartmentOptions({ department_id: 0 })).toEqual([])
    expect(viewerDepartmentOptions({ department_id: 3 })).toEqual([{ id: 3, name: 'Phòng #3' }])
  })
})

describe('department filter of a manager', () => {
  const one = [{ id: 4, name: 'IT' }]
  const two = [...one, { id: 7, name: 'Kế toán' }]

  it('"all" option: HR keeps "Tất cả phòng ban"; a manager gets "Các phòng của tôi" only with 2+ departments', () => {
    expect(departmentAllLabel('all', 0)).toBe('Tất cả phòng ban')
    expect(departmentAllLabel('company', 0)).toBe('Tất cả phòng ban')
    expect(departmentAllLabel('departments', 2)).toBe('Các phòng của tôi')
    expect(departmentAllLabel('departments', 1)).toBeNull()
  })

  it('defaults to the primary department; HR / staff default to no filter', () => {
    expect(defaultRosterDepartment('departments', two)).toBe(4)
    expect(defaultRosterDepartment('departments', [])).toBe(0)
    expect(defaultRosterDepartment('all', two)).toBe(0)
    expect(defaultRosterDepartment('company', two)).toBe(0)
  })

  it('a pasted link to another department falls back to the primary one; HR is never clamped', () => {
    expect(clampRosterDepartment('departments', 99, two)).toBe(4)
    expect(clampRosterDepartment('departments', 7, two)).toBe(7)
    expect(clampRosterDepartment('departments', 0, two)).toBe(0)
    //  Một phòng: không có mục "Các phòng của tôi" nên `0` trên URL quy về chính phòng đó.
    expect(clampRosterDepartment('departments', 0, one)).toBe(4)
    expect(clampRosterDepartment('all', 99, two)).toBe(99)
    expect(clampRosterDepartment('company', 99, two)).toBe(99)
  })
})
