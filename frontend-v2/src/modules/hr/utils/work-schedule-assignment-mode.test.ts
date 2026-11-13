import { describe, expect, it } from 'vitest'

import { WORK_SCHEDULE_LEVEL_CODE } from '../types/work-schedule'
import {
  entityForMode,
  hasStarted,
  isAllowedPersonalEffectiveFrom,
  isAllowedStartedEffectiveTo,
  isCreatedByViewer,
  isPersonallyAssignable,
  resolveAssignmentMode,
  resolveAssignmentRowAccess,
  resolvePersonalRowLocks,
  shiftIsoDate,
} from './work-schedule-assignment-mode'

/** `can` giả từ bảng quyền thu gọn `{ khóa: ['create', ...] }`. */
function canFrom(grants: Record<string, string[]>) {
  return (entity: string, action: string) => grants[entity]?.includes(action) ?? false
}

const SELF = 42
const SELF_USER = 9
const viewer = { employeeId: SELF, userId: SELF_USER }
const TODAY = '2026-11-13'
const employeeRow = (targetId: number, createdBy = SELF_USER, effectiveFrom = '2026-11-20') => ({
  target_level: WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE,
  target_id: targetId,
  created_by: createdBy,
  effective_from: effectiveFrom,
})

describe('resolveAssignmentMode', () => {
  it('goes the HR way when the user holds work_schedule, even if they also hold the personal key', () => {
    const can = canFrom({ work_schedule: ['create'], work_schedule_personal: ['create'] })
    expect(resolveAssignmentMode(can, 'create')).toBe('hr')
  })

  it('goes the personal way when only work_schedule_personal grants the action', () => {
    const can = canFrom({ work_schedule: ['read'], work_schedule_personal: ['create', 'write'] })
    expect(resolveAssignmentMode(can, 'create')).toBe('personal')
    expect(resolveAssignmentMode(can, 'write')).toBe('personal')
  })

  it('decides per action: personal create without write gives no edit path', () => {
    const can = canFrom({ work_schedule_personal: ['create'] })
    expect(resolveAssignmentMode(can, 'create')).toBe('personal')
    expect(resolveAssignmentMode(can, 'write')).toBe('none')
    expect(resolveAssignmentMode(can, 'delete')).toBe('none')
  })

  it('mixes ways per action: HR write but only personal delete', () => {
    const can = canFrom({ work_schedule: ['write'], work_schedule_personal: ['delete'] })
    expect(resolveAssignmentMode(can, 'write')).toBe('hr')
    expect(resolveAssignmentMode(can, 'delete')).toBe('personal')
  })

  it('reading work_schedule alone opens nothing', () => {
    const can = canFrom({ work_schedule: ['read'], work_schedule_personal: ['read'] })
    expect(resolveAssignmentMode(can, 'create')).toBe('none')
  })

  it('maps each way to the key the CRUD gate must ask', () => {
    expect(entityForMode('hr')).toBe('work_schedule')
    expect(entityForMode('personal')).toBe('work_schedule_personal')
    expect(entityForMode('none')).toBe('work_schedule')
  })
})

describe('isPersonallyAssignable', () => {
  it('accepts an employee-level row of someone else', () => {
    expect(isPersonallyAssignable(employeeRow(7), SELF)).toBe(true)
  })

  it('refuses the user own employee record', () => {
    expect(isPersonallyAssignable(employeeRow(SELF), SELF)).toBe(false)
  })

  it('refuses every wider level (department, company, whole system)', () => {
    for (const level of [
      WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
      WORK_SCHEDULE_LEVEL_CODE.COMPANY,
      WORK_SCHEDULE_LEVEL_CODE.SYSTEM,
    ]) {
      expect(isPersonallyAssignable({ target_level: level, target_id: 7 }, SELF)).toBe(false)
    }
  })

  it('compares numbers even when the API hands back numeric strings', () => {
    const row = { target_level: '4', target_id: String(SELF) } as unknown as Parameters<
      typeof isPersonallyAssignable
    >[0]
    expect(isPersonallyAssignable(row, SELF)).toBe(false)
  })

  it('without a linked employee record (undefined or 0) only the level counts', () => {
    expect(isPersonallyAssignable(employeeRow(7), undefined)).toBe(true)
    expect(isPersonallyAssignable(employeeRow(0), 0)).toBe(true)
  })
})

describe('resolveAssignmentRowAccess', () => {
  const personalAll = canFrom({
    work_schedule: ['read'],
    work_schedule_personal: ['read', 'create', 'write', 'delete'],
  })

  it('HR edits and deletes every row, own record and wide levels included', () => {
    const can = canFrom({ work_schedule: ['write', 'delete'] })
    expect(resolveAssignmentRowAccess(can, employeeRow(SELF), viewer, TODAY)).toEqual({ edit: 'hr', remove: 'hr' })
    expect(
      resolveAssignmentRowAccess(can, { target_level: WORK_SCHEDULE_LEVEL_CODE.SYSTEM, target_id: 0, effective_from: '2020-01-01' }, viewer, TODAY),
    ).toEqual({ edit: 'hr', remove: 'hr' })
  })

  it('personal key edits and deletes an employee-level row of a colleague', () => {
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(7), viewer, TODAY)).toEqual({
      edit: 'personal',
      remove: 'personal',
    })
  })

  it('personal key only views the department row and the user own row', () => {
    const none = { edit: 'none', remove: 'none' }
    expect(
      resolveAssignmentRowAccess(
        personalAll,
        { target_level: WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT, target_id: 3, created_by: SELF_USER, effective_from: '2026-11-20' },
        viewer,
        TODAY,
      ),
    ).toEqual(none)
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(SELF), viewer, TODAY)).toEqual(none)
  })

  it('personal key only views a colleague row assigned by HR or another head (created_by differs)', () => {
    const none = { edit: 'none', remove: 'none' }
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(7, 3), viewer, TODAY)).toEqual(none)
  })

  it('fails closed when created_by is missing (older backend) or 0 (seeded row)', () => {
    const none = { edit: 'none', remove: 'none' }
    const { created_by: _drop, ...noOwner } = employeeRow(7)
    expect(resolveAssignmentRowAccess(personalAll, noOwner, viewer, TODAY)).toEqual(none)
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(7, 0), viewer, TODAY)).toEqual(none)
  })

  it('HR ignores created_by entirely', () => {
    const can = canFrom({ work_schedule: ['write', 'delete'] })
    expect(resolveAssignmentRowAccess(can, employeeRow(7, 3), viewer, TODAY)).toEqual({ edit: 'hr', remove: 'hr' })
  })

  it('personal key still edits its own started row, but can no longer delete it', () => {
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(7, SELF_USER, '2026-11-01'), viewer, TODAY)).toEqual({
      edit: 'personal',
      remove: 'none',
    })
  })

  it('a row starting today has not started yet: still deletable', () => {
    expect(resolveAssignmentRowAccess(personalAll, employeeRow(7, SELF_USER, TODAY), viewer, TODAY).remove).toBe(
      'personal',
    )
  })

  it('HR deletes a started row as before', () => {
    const can = canFrom({ work_schedule: ['delete'] })
    expect(resolveAssignmentRowAccess(can, employeeRow(7, 3, '2020-01-01'), viewer, TODAY).remove).toBe('hr')
  })

  it('personal create without write leaves every existing row view-only', () => {
    const can = canFrom({ work_schedule_personal: ['create'] })
    expect(resolveAssignmentRowAccess(can, employeeRow(7), viewer, TODAY)).toEqual({ edit: 'none', remove: 'none' })
  })
})

describe('isCreatedByViewer', () => {
  it('matches only a positive, equal account id', () => {
    expect(isCreatedByViewer({ created_by: SELF_USER }, SELF_USER)).toBe(true)
    expect(isCreatedByViewer({ created_by: 3 }, SELF_USER)).toBe(false)
    expect(isCreatedByViewer({ created_by: 0 }, 0)).toBe(false)
    expect(isCreatedByViewer({}, SELF_USER)).toBe(false)
    expect(isCreatedByViewer({ created_by: SELF_USER }, undefined)).toBe(false)
  })
})

describe('isAllowedPersonalEffectiveFrom', () => {
  const today = '2026-11-13'

  it('accepts today and later, refuses yesterday', () => {
    expect(isAllowedPersonalEffectiveFrom('2026-11-13', today)).toBe(true)
    expect(isAllowedPersonalEffectiveFrom('2027-01-01', today)).toBe(true)
    expect(isAllowedPersonalEffectiveFrom('2026-11-12', today)).toBe(false)
  })

  it('crosses month and year boundaries correctly (string order = date order for yyyy-mm-dd)', () => {
    expect(isAllowedPersonalEffectiveFrom('2026-10-31', '2026-11-01')).toBe(false)
    expect(isAllowedPersonalEffectiveFrom('2025-12-31', '2026-01-01')).toBe(false)
  })

  it('editing a row keeps its stored past start date, but moving it to another past date is refused', () => {
    expect(isAllowedPersonalEffectiveFrom('2026-11-01', today, '2026-11-01')).toBe(true)
    expect(isAllowedPersonalEffectiveFrom('2026-11-02', today, '2026-11-01')).toBe(false)
  })

  it('leaves an empty value to the required rule', () => {
    expect(isAllowedPersonalEffectiveFrom('', today)).toBe(true)
  })
})

describe('resolvePersonalRowLocks', () => {
  it('creating a new row locks nothing', () => {
    expect(resolvePersonalRowLocks(null, TODAY)).toEqual({
      started: false,
      replaces: false,
      lockTarget: false,
      lockSchedule: false,
      lockStart: false,
      endMin: null,
    })
  })

  it('a started row keeps only the end date (from yesterday) and the note', () => {
    expect(resolvePersonalRowLocks({ effective_from: '2026-11-12' }, TODAY)).toEqual({
      started: true,
      replaces: false,
      lockTarget: true,
      lockSchedule: true,
      lockStart: true,
      endMin: '2026-11-12',
    })
  })

  it('a not-started replacing row locks target and start but keeps schedule and end date editable', () => {
    expect(resolvePersonalRowLocks({ effective_from: '2026-11-20', replaces_previous: true }, TODAY)).toEqual({
      started: false,
      replaces: true,
      lockTarget: true,
      lockSchedule: false,
      lockStart: true,
      endMin: null,
    })
  })

  it('a missing replaces_previous (older backend) does not pre-lock; backend 400 still guards', () => {
    expect(resolvePersonalRowLocks({ effective_from: '2026-11-20' }, TODAY).lockTarget).toBe(false)
  })

  it('a row starting today is not started', () => {
    expect(hasStarted({ effective_from: TODAY }, TODAY)).toBe(false)
    expect(hasStarted({ effective_from: '' }, TODAY)).toBe(false)
  })
})

describe('shiftIsoDate', () => {
  it('crosses month, year and leap-day boundaries in local calendar terms', () => {
    expect(shiftIsoDate('2026-11-01', -1)).toBe('2026-10-31')
    expect(shiftIsoDate('2026-01-01', -1)).toBe('2025-12-31')
    expect(shiftIsoDate('2028-03-01', -1)).toBe('2028-02-29')
    expect(shiftIsoDate('2026-03-01', -1)).toBe('2026-02-28')
  })
})

describe('isAllowedStartedEffectiveTo', () => {
  const yesterday = '2026-11-12'

  it('accepts empty (open-ended), yesterday and later; refuses the day before yesterday', () => {
    expect(isAllowedStartedEffectiveTo('', yesterday)).toBe(true)
    expect(isAllowedStartedEffectiveTo('2026-11-12', yesterday)).toBe(true)
    expect(isAllowedStartedEffectiveTo('2026-12-31', yesterday)).toBe(true)
    expect(isAllowedStartedEffectiveTo('2026-11-11', yesterday)).toBe(false)
  })

  it('keeping the stored end date untouched is never blocked', () => {
    expect(isAllowedStartedEffectiveTo('2026-10-01', yesterday, '2026-10-01')).toBe(true)
  })
})
