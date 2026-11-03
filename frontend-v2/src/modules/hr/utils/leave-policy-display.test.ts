import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import {
  POLICY_LINES_MAX,
  buildAssignmentListHref,
  buildLeaveTypeNameLookup,
  describeBalanceChanges,
  formatPolicyRange,
  parsePolicyDays,
  summarizeQuotaChanges,
  upsertPolicyLine,
} from './leave-policy-display'

const typeName = buildLeaveTypeNameLookup([
  { id: 1, name: 'Phép năm' },
  { id: 2, name: 'Phép thâm niên' },
])

describe('parsePolicyDays (review M3)', () => {
  it('reads the Vietnamese decimal comma and the dot alike, trimming spaces', () => {
    expect(parsePolicyDays('12,5')).toBe(12.5)
    expect(parsePolicyDays(' 12.5 ')).toBe(12.5)
    expect(parsePolicyDays('0')).toBe(0)
    expect(parsePolicyDays('366')).toBe(366)
  })

  it('returns null for empty / blank input instead of 0 — Number("") once added a silent 0-day line', () => {
    expect(parsePolicyDays('')).toBeNull()
    expect(parsePolicyDays('   ')).toBeNull()
  })

  it('returns null for anything that is not a plain number', () => {
    for (const raw of ['abc', '12,', ',5', '1,2,3', '12.5.1', '1e3', 'NaN', 'Infinity', '12 ngày', '0x10', '+5']) {
      expect(parsePolicyDays(raw)).toBeNull()
    }
  })

  it('keeps a negative number as a number so the range check (0–366) speaks, not "Nhập số ngày"', () => {
    expect(parsePolicyDays('-1')).toBe(-1)
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: -1 }).error).toMatch(/từ 0 đến 366/)
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 367 }).error).toMatch(/từ 0 đến 366/)
  })
})

describe('upsertPolicyLine', () => {
  it('overwrites the existing line of the same leave type instead of adding a duplicate (backend 422s on duplicates)', () => {
    const { lines, error } = upsertPolicyLine(
      [
        { id: 9, leave_type_id: 1, annual_days: 12 },
        { leave_type_id: 2, annual_days: 3 },
      ],
      { leave_type_id: 1, annual_days: 15 },
    )
    expect(error).toBeNull()
    expect(lines).toEqual([
      { id: 9, leave_type_id: 1, annual_days: 15 },
      { leave_type_id: 2, annual_days: 3 },
    ])
  })

  it('accepts 0 and the 366 ceiling, rejects anything outside or off the 0.5 step', () => {
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 0 }).error).toBeNull()
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 366 }).error).toBeNull()
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 12.5 }).error).toBeNull()
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: -0.5 }).error).toMatch(/0 đến 366/)
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 366.5 }).error).toMatch(/0 đến 366/)
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: 12.25 }).error).toMatch(/bước 0,5/)
    expect(upsertPolicyLine([], { leave_type_id: 1, annual_days: Number.NaN }).error).toMatch(/0 đến 366/)
  })

  it('requires a real leave type id — 0 / negative / fractional never reach the request', () => {
    for (const id of [0, -1, 1.5]) {
      const result = upsertPolicyLine([], { leave_type_id: id, annual_days: 12 })
      expect(result.error).toBe('Chọn loại nghỉ.')
      expect(result.lines).toEqual([])
    }
  })

  it('caps the policy at 50 leave types but still lets an existing line be overwritten at the cap', () => {
    const full = Array.from({ length: POLICY_LINES_MAX }, (_, i) => ({ leave_type_id: i + 1, annual_days: 1 }))
    expect(upsertPolicyLine(full, { leave_type_id: 999, annual_days: 2 }).error).toMatch(/tối đa 50/)
    const overwrite = upsertPolicyLine(full, { leave_type_id: 7, annual_days: 2 })
    expect(overwrite.error).toBeNull()
    expect(overwrite.lines).toHaveLength(POLICY_LINES_MAX)
    expect(overwrite.lines[6].annual_days).toBe(2)
  })

  it('never mutates the input array (draft vs server copy must stay separate)', () => {
    const original = [{ leave_type_id: 1, annual_days: 12 }]
    upsertPolicyLine(original, { leave_type_id: 1, annual_days: 20 })
    expect(original).toEqual([{ leave_type_id: 1, annual_days: 12 }])
  })
})

describe('summarizeQuotaChanges', () => {
  it('lists only types whose quota moves, with Vietnamese decimal commas', () => {
    expect(
      summarizeQuotaChanges(
        [
          { leave_type_id: 1, before: 12, after: 13.5 },
          { leave_type_id: 2, before: 3, after: 3 },
        ],
        typeName,
      ),
    ).toBe('Phép năm 12 → 13,5')
  })

  it('says "Không đổi" for an empty or all-equal list, and falls back to #id for an unknown type', () => {
    expect(summarizeQuotaChanges([], typeName)).toBe('Không đổi')
    expect(summarizeQuotaChanges([{ leave_type_id: 2, before: 3, after: 3 }], typeName)).toBe('Không đổi')
    expect(summarizeQuotaChanges([{ leave_type_id: 77, before: 0, after: 5 }], typeName)).toBe('#77 0 → 5')
  })
})

describe('describeBalanceChanges', () => {
  it('states explicitly that nothing changed when recalc was off', () => {
    expect(describeBalanceChanges({ created: 0, recalculated: [], kept: 0, negative_after: [] })).toBe(
      'Quỹ phép năm nay không đổi.',
    )
    expect(describeBalanceChanges(undefined)).toBe('')
  })

  it('counts recalculated / created / kept rows and warns about negative balances', () => {
    const text = describeBalanceChanges({
      created: 1,
      recalculated: [{ leave_type_id: 1, before: 12, after: 15 }],
      kept: 2,
      negative_after: [{ leave_type_id: 1, available_days: -1 }],
    })
    expect(text).toContain('tính lại 1 dòng quỹ')
    expect(text).toContain('cấp mới 1 dòng quỹ')
    expect(text).toContain('giữ nguyên 2 dòng quỹ')
    expect(text).toContain('1 dòng quỹ bị ÂM')
  })
})

describe('formatPolicyRange / buildAssignmentListHref', () => {
  it('writes an open-ended range as "Không thời hạn"', () => {
    expect(formatPolicyRange('2026-07-01', null)).toBe('01/07/2026 → Không thời hạn')
    expect(formatPolicyRange('2026-07-01', '2026-12-31')).toBe('01/07/2026 → 31/12/2026')
  })

  it('links to the assignment list filtered by policy, plus the employee code when a row is given', () => {
    expect(buildAssignmentListHref(4)).toBe(`${appRoutes.hr.leavePolicyAssignments}?policy_id=4`)
    expect(buildAssignmentListHref(4, { employee_code: 'NSU 01&x' })).toBe(
      `${appRoutes.hr.leavePolicyAssignments}?policy_id=4&q=NSU+01%26x`,
    )
    expect(buildAssignmentListHref(4, { employee_code: '' })).toBe(
      `${appRoutes.hr.leavePolicyAssignments}?policy_id=4`,
    )
  })
})
