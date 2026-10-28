import { describe, expect, it } from 'vitest'

import type { ContractReminder, MonthlyReminderGroupPayload } from '../types/monthly-reminders'
import {
  buildMonthlyReminderGroups,
  formatDayMonth,
  formatIsoDayMonth,
  formatMonthKeyLabel,
  isPastContractLookahead,
  monthKeyToDate,
  shiftMonthKey,
  toMonthKey,
} from './monthly-reminders'

const FALLBACK = new Date(2026, 9, 28)

function group<T>(items: T[], over: Partial<MonthlyReminderGroupPayload<T>> = {}): MonthlyReminderGroupPayload<T> {
  return { allowed: true, items, total: items.length, truncated: false, ...over }
}

function contract(over: Partial<ContractReminder> = {}): ContractReminder {
  return {
    employee_id: 9,
    employee_code: 'NV09',
    employee_name: 'Lê Văn C',
    department: 'Kho',
    contract_code: 'HDLD009',
    contract_no: '',
    end_date: '2026-10-20',
    days_left: 22,
    level: 'warn',
    ...over,
  }
}

const NO_ACCESS = group<ContractReminder>([], { allowed: false })

describe('buildMonthlyReminderGroups', () => {
  it('hides groups marked allowed=false (no permission) but keeps an allowed empty one', () => {
    const groups = buildMonthlyReminderGroups({
      month: '2026-10',
      birthdays: group([], { allowed: false }),
      anniversaries: group([]),
      contracts: NO_ACCESS,
      probations: NO_ACCESS,
    })
    expect(groups.map((g) => g.key)).toEqual(['anniversaries'])
    expect(groups[0]?.rows).toEqual([])
  })

  it('treats a group missing from an older server as not permitted', () => {
    expect(buildMonthlyReminderGroups({ month: '2026-10' })).toEqual([])
  })

  it('merges contracts and probations into one group sorted by end date', () => {
    const groups = buildMonthlyReminderGroups({
      month: '2026-10',
      contracts: group([contract({ employee_id: 1, end_date: '2026-10-25', contract_code: 'A' })]),
      probations: group([contract({ employee_id: 2, end_date: '2026-10-03', contract_code: 'B', level: 'danger' })]),
    })
    const g = groups[0]
    expect(g?.key).toBe('expiring_contracts')
    expect(g?.rows.map((r) => r.employeeId)).toEqual([2, 1])
    expect(g?.rows.map((r) => r.detail)).toEqual(['Thử việc hết hạn 03/10', 'Hợp đồng hết hạn 25/10'])
    expect(g?.rows[0]?.urgent).toBe(true)
    expect(g?.total).toBe(2)
  })

  it('shows birthdays as day/month only and anniversaries with the milestone year', () => {
    const groups = buildMonthlyReminderGroups({
      month: '2026-10',
      birthdays: group([{ employee_id: 7, employee_code: 'NV07', employee_name: 'B', day: 5, month: 10 }]),
      anniversaries: group([
        { employee_id: 8, employee_code: 'NV08', employee_name: 'C', day: 3, month: 10, years: 5, hire_date: '2021-10-03' },
      ]),
    })
    expect(groups.map((g) => g.rows[0]?.detail)).toEqual(['Sinh nhật 05/10', 'Tròn 5 năm làm việc · 03/10'])
  })

  it('carries the real total and the truncated flag when the 200-row cap was hit', () => {
    const items = [{ employee_id: 1, employee_code: 'X', employee_name: 'X', day: 1, month: 10 }]
    const g = buildMonthlyReminderGroups({ month: '2026-10', birthdays: group(items, { total: 260, truncated: true }) })[0]
    expect(g).toMatchObject({ total: 260, truncated: true })
  })

  it('returns no groups before data arrives', () => {
    expect(buildMonthlyReminderGroups(undefined)).toEqual([])
  })
})

describe('day/month formatting', () => {
  it('pads day and month and gives up on missing numbers', () => {
    expect(formatDayMonth(5, 3)).toBe('05/03')
    expect(formatDayMonth(0, 3)).toBe('')
    expect(formatDayMonth(null, undefined)).toBe('')
  })

  it.each([
    ['2026-02-09', '09/02'],
    ['2026-02-09T00:00:00', '09/02'],
    ['', ''],
    ['abc', 'abc'],
  ])('ISO %s → %s', (raw, want) => {
    expect(formatIsoDayMonth(raw)).toBe(want)
  })
})

describe('month keys', () => {
  it('pads the month and crosses year boundaries both ways', () => {
    expect(toMonthKey(new Date(2026, 0, 31))).toBe('2026-01')
    expect(shiftMonthKey('2026-01', -1, FALLBACK)).toBe('2025-12')
    expect(shiftMonthKey('2026-12', 1, FALLBACK)).toBe('2027-01')
  })

  it('does not overflow from the 31st into the month after (anchored on day 1)', () => {
    expect(shiftMonthKey('2026-01', 1, FALLBACK)).toBe('2026-02')
  })

  it.each(['', '2026-13', '2026-00', '26-10', 'xx'])('falls back to the fallback month for a broken key %s', (key) => {
    expect(toMonthKey(monthKeyToDate(key, FALLBACK))).toBe('2026-10')
  })

  it('labels the month the Vietnamese way', () => {
    expect(formatMonthKeyLabel('2026-03', FALLBACK)).toBe('Tháng 3/2026')
  })
})

describe('isPastContractLookahead', () => {
  const today = new Date(2026, 9, 28)
  it('is false for this month and the near future', () => {
    expect(isPastContractLookahead('2026-10', today)).toBe(false)
    expect(isPastContractLookahead('2027-03', today)).toBe(false)
  })

  it('is true once any day of the month is more than 180 days ahead', () => {
    //  28/10/2026 + 180 ngày = 26/04/2027 → tháng 4/2027 đã lố một phần.
    expect(isPastContractLookahead('2027-04', today)).toBe(true)
    expect(isPastContractLookahead('2028-01', today)).toBe(true)
  })

  it('is false for past months', () => {
    expect(isPastContractLookahead('2025-01', today)).toBe(false)
  })
})
