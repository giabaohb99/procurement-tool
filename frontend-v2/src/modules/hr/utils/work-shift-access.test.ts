import { describe, expect, it } from 'vitest'

import {
  canArrangeShifts,
  isLeaveHeld,
  pickCopyWeekDefaultIds,
  viewerDepartmentIds,
  pickArrangeableDates,
  pickArrangeableEmployeeIds,
  resolveShiftCellAccess,
} from './work-shift-access'

/** `can` giả từ bảng quyền thu gọn `{ khóa: ['write', ...] }`. */
function canFrom(grants: Record<string, string[]>) {
  return (entity: string, action: string) => grants[entity]?.includes(action) ?? false
}

const SELF = 42
const TODAY = '2026-11-16'
const hr = canFrom({ work_schedule: ['read', 'write', 'delete'] })
const manager = canFrom({ work_schedule_personal: ['read', 'write', 'delete'] })
const viewer = { employeeId: SELF }

describe('resolveShiftCellAccess', () => {
  it('HR edits any colleague on any date, past days included', () => {
    expect(resolveShiftCellAccess(hr, 7, '2026-01-01', viewer, TODAY)).toMatchObject({ mode: 'hr', canWrite: true, canDelete: true, lock: null })
  })

  it('nobody arranges their own shift — HR included (owner rule 16/11/2026)', () => {
    expect(resolveShiftCellAccess(hr, SELF, '2026-12-01', viewer, TODAY)).toMatchObject({ canWrite: false, canDelete: false, lock: 'self' })
  })

  it('a cell with a pending / approved leave is locked for everyone until the leave is changed', () => {
    expect(resolveShiftCellAccess(hr, 7, TODAY, viewer, TODAY, true)).toMatchObject({ canWrite: false, canDelete: false, lock: 'leave' })
    expect(resolveShiftCellAccess(manager, 7, '2026-12-01', viewer, TODAY, true).lock).toBe('leave')
  })

  it('a manager edits a colleague from today on, today itself included', () => {
    expect(resolveShiftCellAccess(manager, 7, TODAY, viewer, TODAY)).toMatchObject({ mode: 'personal', canWrite: true, lock: null })
    expect(resolveShiftCellAccess(manager, 7, '2026-12-31', viewer, TODAY).canWrite).toBe(true)
  })

  it('a manager cannot touch a past day — read-only with the past hint', () => {
    expect(resolveShiftCellAccess(manager, 7, '2026-11-15', viewer, TODAY)).toMatchObject({ canWrite: false, canDelete: false, lock: 'past' })
  })

  it('a manager cannot arrange their own shift, even in the future (self wins over past)', () => {
    expect(resolveShiftCellAccess(manager, SELF, '2026-12-01', viewer, TODAY).lock).toBe('self')
    expect(resolveShiftCellAccess(manager, SELF, '2026-01-01', viewer, TODAY).lock).toBe('self')
  })

  it('an account with no employee profile is never "self" — employee_id 0 must not match id 0 rows', () => {
    expect(resolveShiftCellAccess(manager, 0, TODAY, { employeeId: 0 }, TODAY).lock).toBeNull()
    expect(resolveShiftCellAccess(manager, 7, TODAY, { employeeId: null }, TODAY).lock).toBeNull()
  })

  it('no key at all → no_permission', () => {
    const none = canFrom({ employee: ['read'] })
    expect(resolveShiftCellAccess(none, 7, TODAY, viewer, TODAY)).toMatchObject({ mode: 'none', canWrite: false, lock: 'no_permission' })
    expect(canArrangeShifts(none)).toBe(false)
  })

  it('delete follows its own key: HR write without delete cannot reset to template', () => {
    const writeOnly = canFrom({ work_schedule: ['write'] })
    expect(resolveShiftCellAccess(writeOnly, 7, TODAY, viewer, TODAY)).toMatchObject({ canWrite: true, canDelete: false })
  })

  it('HR write + personal delete: the delete falls back to the manager rules', () => {
    const mixed = canFrom({ work_schedule: ['write'], work_schedule_personal: ['delete'] })
    expect(resolveShiftCellAccess(mixed, 7, '2026-11-01', viewer, TODAY)).toMatchObject({ canWrite: true, canDelete: false })
    expect(resolveShiftCellAccess(mixed, 7, TODAY, viewer, TODAY)).toMatchObject({ canWrite: true, canDelete: true })
  })
})

describe('resetBlocked (Về mẫu tuần)', () => {
  it('today and past days cannot go back to the template for anyone, HR included; tomorrow can', () => {
    expect(resolveShiftCellAccess(hr, 7, '2026-11-15', viewer, TODAY).resetBlocked).toBe(true)
    expect(resolveShiftCellAccess(hr, 7, TODAY, viewer, TODAY).resetBlocked).toBe(true)
    expect(resolveShiftCellAccess(hr, 7, '2026-11-17', viewer, TODAY)).toMatchObject({ resetBlocked: false, canDelete: true })
    //  Chặn theo ngày độc lập với quyền: HR vẫn sửa khung giờ được hôm nay.
    expect(resolveShiftCellAccess(hr, 7, TODAY, viewer, TODAY).canWrite).toBe(true)
  })
})

describe('bulk pickers', () => {
  it('nobody sends their own id — the backend would reject the whole batch', () => {
    expect(pickArrangeableEmployeeIds(manager, [1, SELF, 3], viewer)).toEqual([1, 3])
    expect(pickArrangeableEmployeeIds(hr, [1, SELF, 3], viewer)).toEqual([1, 3])
    expect(pickArrangeableEmployeeIds(hr, [1, 3], { employeeId: null })).toEqual([1, 3])
    expect(pickArrangeableEmployeeIds(canFrom({}), [1, 3], viewer)).toEqual([])
  })

  it('a manager only gets today and later; HR gets every date', () => {
    const dates = ['2026-11-14', '2026-11-16', '2026-11-20']
    expect(pickArrangeableDates(manager, dates, TODAY)).toEqual(['2026-11-16', '2026-11-20'])
    expect(pickArrangeableDates(hr, dates, TODAY)).toEqual(dates)
    expect(pickArrangeableDates(manager, [], TODAY)).toEqual([])
  })
})

describe('isLeaveHeld', () => {
  it('locks on the backend leave_hold flag OR a visible leave; a missing flag means not held', () => {
    expect(isLeaveHeld({ leave_hold: true, leave: null })).toBe(true)
    expect(isLeaveHeld({ leave: { request_id: 1 } as never })).toBe(true)
    expect(isLeaveHeld({ leave: null })).toBe(false)
    expect(isLeaveHeld({ leave_hold: false, leave: null })).toBe(false)
    expect(isLeaveHeld(undefined)).toBe(false)
  })
})

describe('copy-week default rows (no tick)', () => {
  const items = [
    { employee_id: 1, department_id: 4 },
    { employee_id: SELF, department_id: 4 },
    { employee_id: 3, department_id: 9 },
    { employee_id: 5, department_id: 12 },
    { employee_id: 6, department_id: 0 },
  ]

  it('manager: only people of their own departments (primary + concurrent counting toward scope), never self', () => {
    const depts = viewerDepartmentIds({
      department_id: 4,
      concurrents: [
        { kind: 1, department_id: 12, counts_scope: true },
        { kind: 1, department_id: 9, counts_scope: false },
        { kind: 2, department_id: 0, counts_scope: true },
      ],
    })
    expect(depts).toEqual([4, 12])
    expect(pickCopyWeekDefaultIds(manager, items, viewer, depts)).toEqual([1, 5])
  })

  it('HR: every row on the page except self; a manager with no department copies nobody', () => {
    expect(pickCopyWeekDefaultIds(hr, items, viewer, [])).toEqual([1, 3, 5, 6])
    expect(pickCopyWeekDefaultIds(manager, items, viewer, viewerDepartmentIds({ department_id: 0 }))).toEqual([])
    expect(viewerDepartmentIds(null)).toEqual([])
  })
})
