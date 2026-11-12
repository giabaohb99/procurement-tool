import { describe, expect, it } from 'vitest'

import { CONCURRENT_STATUS } from '@/shared/constants/statuses'
import {
  CONCURRENT_ACTIVE,
  CONCURRENT_ENDED,
  CONCURRENT_UPCOMING,
  type EmployeeConcurrent,
} from '../types/employee-concurrent'
import {
  concurrentPeriodLabel,
  concurrentRowsAtOldCompany,
  concurrentStatusLabel,
  isConcurrentUnstarted,
  sortConcurrentRowsDefault,
} from './employee-concurrent-display'

function row(overrides: Partial<EmployeeConcurrent>): EmployeeConcurrent {
  return {
    id: 1,
    employee_id: 1,
    company_id: 10,
    company_name: 'DEGO A',
    department_id: 5,
    department_name: 'Kế toán',
    position_id: 0,
    position_label: '',
    from_date: '2026-01-01',
    to_date: null,
    decision_no: '',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 0,
    status: CONCURRENT_ACTIVE,
    status_label: '',
    file_count: 0,
    ...overrides,
  }
}

describe('concurrent status codes', () => {
  //  Ba hằng số mirror `ConcurrentStatus` của backend; lệch với bộ mã sinh là huy hiệu + xếp + hộp đổi pháp nhân sai cùng lúc.
  it('constants match the generated code set exactly (1 Sắp tới, 2 Đang hiệu lực, 3 Đã hết)', () => {
    expect(CONCURRENT_STATUS.map((o) => [o.value, o.label])).toEqual([
      [String(CONCURRENT_UPCOMING), 'Sắp tới'],
      [String(CONCURRENT_ACTIVE), 'Đang hiệu lực'],
      [String(CONCURRENT_ENDED), 'Đã hết'],
    ])
  })

  it('label falls back to the generated set when the backend label is empty', () => {
    expect(concurrentStatusLabel({ status: 3, status_label: '' })).toBe('Đã hết')
    expect(concurrentStatusLabel({ status: 1, status_label: 'Nhãn backend' })).toBe('Nhãn backend')
    expect(concurrentStatusLabel({ status: 99, status_label: '' })).toBe('')
  })
})

describe('sortConcurrentRowsDefault', () => {
  it('active first, then upcoming, then ended; newest start first inside a group; ties by id desc', () => {
    const rows = [
      row({ id: 1, status: CONCURRENT_ENDED, from_date: '2026-06-01' }),
      row({ id: 2, status: CONCURRENT_UPCOMING, from_date: '2027-01-01' }),
      row({ id: 3, status: CONCURRENT_ACTIVE, from_date: '2025-01-01' }),
      row({ id: 4, status: CONCURRENT_ACTIVE, from_date: '2026-01-01' }),
      row({ id: 5, status: CONCURRENT_ACTIVE, from_date: '2026-01-01' }),
      row({ id: 6, status: CONCURRENT_ACTIVE, from_date: null }),
    ]
    expect(sortConcurrentRowsDefault(rows).map((r) => r.id)).toEqual([5, 4, 3, 6, 2, 1])
  })

  it('does not mutate the input and handles an empty list', () => {
    const rows = [row({ id: 1 }), row({ id: 2 })]
    sortConcurrentRowsDefault(rows)
    expect(rows.map((r) => r.id)).toEqual([1, 2])
    expect(sortConcurrentRowsDefault([])).toEqual([])
  })
})

describe('concurrentRowsAtOldCompany', () => {
  const rows = [
    row({ id: 1, company_id: 10, status: CONCURRENT_ACTIVE }),
    row({ id: 2, company_id: 10, status: CONCURRENT_UPCOMING }),
    row({ id: 3, company_id: 10, status: CONCURRENT_ENDED }),
    row({ id: 4, company_id: 20, status: CONCURRENT_ACTIVE }),
  ]

  it('only non-ended rows of the old company — rows elsewhere are never touched by the backend', () => {
    expect(concurrentRowsAtOldCompany(rows, 10).map((r) => r.id)).toEqual([1, 2])
  })

  it('old company 0 (no legal entity) → nothing to ask', () => {
    expect(concurrentRowsAtOldCompany([row({ company_id: 0 })], 0)).toEqual([])
  })
})

describe('isConcurrentUnstarted', () => {
  //  Backend xóa dòng `from_date >= hôm nay` (kể cả đúng hôm nay, đang hiện "Đang hiệu lực") — phải báo đúng dòng đó.
  it('a row starting TODAY counts as unstarted (it will be deleted, not ended)', () => {
    expect(isConcurrentUnstarted({ from_date: '2026-11-12' }, '2026-11-12')).toBe(true)
    expect(isConcurrentUnstarted({ from_date: '2026-11-13' }, '2026-11-12')).toBe(true)
    expect(isConcurrentUnstarted({ from_date: '2026-11-11' }, '2026-11-12')).toBe(false)
  })

  it('legacy row without a start date is never unstarted', () => {
    expect(isConcurrentUnstarted({ from_date: null }, '2026-11-12')).toBe(false)
  })
})

describe('concurrentPeriodLabel', () => {
  it('formats both ends, open end, missing start, and nothing', () => {
    expect(concurrentPeriodLabel({ from_date: '2026-11-01', to_date: '2026-11-30' })).toBe('01/11/2026 – 30/11/2026')
    expect(concurrentPeriodLabel({ from_date: '2026-11-01', to_date: null })).toBe('Từ 01/11/2026')
    expect(concurrentPeriodLabel({ from_date: null, to_date: '2026-11-30' })).toBe('Đến 30/11/2026')
    expect(concurrentPeriodLabel({ from_date: null, to_date: null })).toBe('')
  })
})
