import { describe, expect, it } from 'vitest'

import { LEAVE_ACCRUAL_MODE, LEAVE_ACCRUAL_MODE_LABELS, LEAVE_ACCRUAL_STATUS } from '../types/leave'
import {
  getAccrualStartHint,
  getAccrualTone,
  hasMissingContract,
  matrixAccrualEntries,
  pickAccrualInfo,
  summarizeMissingContract,
} from './leave-accrual-status'

describe('LEAVE_ACCRUAL_MODE (hand-typed copy of backend LeaveAccrualMode)', () => {
  it('keeps codes 1-3 unchanged and adds 4 with the backend label', () => {
    //  Bộ mã số gõ tay (gen_status_ts.py chỉ sinh mã CHUỖI) — lệch backend là ô chọn ra số trần.
    expect(LEAVE_ACCRUAL_MODE).toEqual({ FULL_YEAR: 1, PRORATA_HIRE: 2, MONTHLY: 3, MONTHLY_AFTER: 4 })
    expect(LEAVE_ACCRUAL_MODE_LABELS[4]).toBe('Cộng dần sau mỗi tháng làm đủ')
    expect(LEAVE_ACCRUAL_MODE_LABELS[3]).toBe('Cộng dần theo tháng')
    expect(Object.keys(LEAVE_ACCRUAL_MODE_LABELS).map(Number).sort()).toEqual([1, 2, 3, 4])
  })

  it('matches backend LeaveAccrualStatus codes (codes only, labels come from the API)', () => {
    expect(LEAVE_ACCRUAL_STATUS).toEqual({
      ACCRUING: 1,
      PROBATION: 2,
      MISSING_CONTRACT: 3,
      INCOMPLETE_HISTORY: 4,
      SERVICE_CONTRACT: 5,
      NOT_YET_OFFICIAL: 6,
    })
  })
})

describe('getAccrualTone', () => {
  it('1 none · 2/5/6 muted · 3/4 warn · anything else null', () => {
    expect([1, 2, 3, 4, 5, 6].map(getAccrualTone)).toEqual(['none', 'muted', 'warn', 'warn', 'muted', 'muted'])
    for (const odd of [0, 7, -1, 99, null, undefined]) expect(getAccrualTone(odd)).toBeNull()
  })
})

describe('getAccrualStartHint', () => {
  it('formats the start date dd/mm/yyyy only for an accruing employee', () => {
    expect(getAccrualStartHint({ accrual_status: 1, accrual_start_date: '2026-02-01' })).toBe('Tích từ 01/02/2026')
  })

  it('returns null for probation, missing contract, null fields, absent fields and null info', () => {
    expect(getAccrualStartHint({ accrual_status: 2, accrual_start_date: null })).toBeNull()
    //  Chưa có HĐLĐ có ngày (ngày vào làm) nhưng KHÔNG phải ngày tích chuẩn — nhãn hổ phách lo chuyện đó.
    expect(getAccrualStartHint({ accrual_status: 3, accrual_start_date: '2026-03-01' })).toBeNull()
    expect(getAccrualStartHint({ accrual_status: 6, accrual_start_date: '2027-01-01' })).toBeNull()
    expect(getAccrualStartHint({ accrual_status: null, accrual_start_date: null })).toBeNull()
    expect(getAccrualStartHint({})).toBeNull()
    expect(getAccrualStartHint(null)).toBeNull()
    expect(getAccrualStartHint(undefined)).toBeNull()
  })

  it('accruing without a date or with a garbage date shows nothing instead of "Tích từ "', () => {
    expect(getAccrualStartHint({ accrual_status: 1, accrual_start_date: null })).toBeNull()
    expect(getAccrualStartHint({ accrual_status: 1, accrual_start_date: '' })).toBeNull()
    expect(getAccrualStartHint({ accrual_status: 1, accrual_start_date: 'not-a-date' })).toBeNull()
  })
})

describe('pickAccrualInfo', () => {
  it('ranks missing contract > incomplete history > muted statuses', () => {
    const incomplete = { accrual_status: 4 }
    const service = { accrual_status: 5 }
    expect(pickAccrualInfo([service, incomplete])).toBe(incomplete)
    expect(pickAccrualInfo([incomplete, { accrual_status: 3 }])?.accrual_status).toBe(3)
    expect(pickAccrualInfo([{ accrual_status: 1 }, service])).toBe(service)
  })

  it('picks the most urgent status: no contract > probation > accruing', () => {
    const accruing = { accrual_status: 1, accrual_start_date: '2026-01-01' }
    const probation = { accrual_status: 2 }
    const noContract = { accrual_status: 3 }
    expect(pickAccrualInfo([accruing, probation, noContract])).toBe(noContract)
    expect(pickAccrualInfo([noContract, probation, accruing])).toBe(noContract)
    expect(pickAccrualInfo([accruing, probation])).toBe(probation)
    expect(pickAccrualInfo([{}, accruing, { accrual_status: null }])).toBe(accruing)
  })

  it('returns null when no row carries a status (empty list, only other accrual modes, unknown codes)', () => {
    expect(pickAccrualInfo([])).toBeNull()
    expect(pickAccrualInfo([{}, { accrual_status: null }])).toBeNull()
    expect(pickAccrualInfo([{ accrual_status: 99 }, { accrual_status: 0 }])).toBeNull()
  })
})

describe('pickAccrualInfo excludeNoContract (badges hidden, option B)', () => {
  it('falls back to the probation row instead of hiding everything', () => {
    const probation = { accrual_status: 2 }
    expect(pickAccrualInfo([{ accrual_status: 3 }, { accrual_status: 4 }, probation], true)).toBe(probation)
    expect(pickAccrualInfo([{ accrual_status: 3 }, { accrual_status: 4 }], true)).toBeNull()
  })
})

describe('summarizeMissingContract (option B: per-row badges only while missing <= 50%)', () => {
  const e = (employee_id: number, accrual_status: number | null) => ({ employee_id, accrual_status })

  it('counts PEOPLE, not balance rows, and ignores rows of other accrual modes', () => {
    const summary = summarizeMissingContract([
      e(1, 3),
      e(1, 3),
      e(2, 2),
      e(3, 1),
      e(3, null),
      e(4, null),
      { employee_id: 5 },
    ])
    //  Người 4, 5 không có dòng loại cộng dần sau tháng làm đủ → không nằm trong mẫu số.
    expect(summary).toEqual({ missing: 1, total: 3, showRowBadges: true })
  })

  it('counts status 4 (incomplete history) together with 3; 5 and 6 are tracked but not missing', () => {
    expect(summarizeMissingContract([e(1, 4), e(2, 3), e(3, 5), e(4, 6), e(5, 2)])).toEqual({
      missing: 2,
      total: 5,
      showRowBadges: true,
    })
    expect(summarizeMissingContract([e(1, 4), e(2, 4), e(3, 6)]).showRowBadges).toBe(false)
  })

  it('exactly half still shows row badges; one more than half hides them', () => {
    expect(summarizeMissingContract([e(1, 3), e(2, 1)]).showRowBadges).toBe(true)
    expect(summarizeMissingContract([e(1, 3), e(2, 3), e(3, 1)]).showRowBadges).toBe(false)
    expect(summarizeMissingContract([e(1, 3)])).toEqual({ missing: 1, total: 1, showRowBadges: false })
  })

  it('a person with one missing row and one accruing row counts once in both numbers', () => {
    expect(summarizeMissingContract([e(1, 3), e(1, 1), e(2, 1), e(3, 1)])).toEqual({
      missing: 1,
      total: 3,
      showRowBadges: true,
    })
  })

  it('empty, missing or legacy (no accrual fields) lists: 0/0 and badges on (nothing to hide)', () => {
    for (const input of [[], undefined, [{ employee_id: 1 }]]) {
      expect(summarizeMissingContract(input)).toEqual({ missing: 0, total: 0, showRowBadges: true })
    }
  })
})

describe('matrixAccrualEntries', () => {
  it('spreads each matrix row accrual map into person x status entries; absent map gives nothing', () => {
    expect(
      matrixAccrualEntries([
        { employee_id: 1, accrual: { '3': { accrual_status: 3 }, '9': { accrual_status: 1 } } },
        { employee_id: 2 },
        { employee_id: 3, accrual: {} },
      ]),
    ).toEqual([
      { employee_id: 1, accrual_status: 3 },
      { employee_id: 1, accrual_status: 1 },
    ])
    expect(matrixAccrualEntries(undefined)).toEqual([])
  })
})

describe('hasMissingContract', () => {
  it('is true only when some row reports status 3 or 4', () => {
    expect(hasMissingContract([{ accrual_status: 1 }, { accrual_status: 3 }])).toBe(true)
    expect(hasMissingContract([{ accrual_status: 4 }])).toBe(true)
    expect(hasMissingContract([{ accrual_status: 2 }, { accrual_status: 5 }, { accrual_status: 6 }, {}])).toBe(false)
    expect(hasMissingContract([])).toBe(false)
  })
})
